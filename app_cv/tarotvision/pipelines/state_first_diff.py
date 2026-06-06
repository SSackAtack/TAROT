# -*- coding: utf-8 -*-
import time

import numpy as np

from tarotvision.background_model import BackgroundModel
from tarotvision.pipelines.base import VisionPipeline


class StateFirstDiffPipeline(VisionPipeline):
    def __init__(
        self,
        snapshot_session_store,
        change_detector,
        snapshot_analyzer,
        table_state,
        snapshot_gate,
        status_store,
        table_calibration,
        runtime_metrics,
        runtime_config=None,
        build_operator_snapshot_fn=None,
        operator_warnings=None,
        runtime_profile="state_first_diff",
    ):
        self.snapshot_session_store = snapshot_session_store
        self.change_detector = change_detector
        self.snapshot_analyzer = snapshot_analyzer
        self.table_state = table_state
        self.snapshot_gate = snapshot_gate
        self.status_store = status_store
        self.table_calibration = table_calibration
        self.runtime_metrics = runtime_metrics
        self.runtime_config = runtime_config
        self.build_operator_snapshot_fn = build_operator_snapshot_fn or (lambda **_: {})
        self.operator_warnings = operator_warnings or []
        self.runtime_profile = runtime_profile
        self.frame_index = 0
        self.last_diff_diagnostics = None

    def process_frame(self, frame, motion_result, frame_width, frame_height, frame_loop_start):
        self.frame_index += 1
        now_ms = int(time.time() * 1000)
        gate_decision = self.snapshot_gate.update(
            now_ms=now_ms,
            motion_detected=motion_result.motion_detected,
            changed_ratio=motion_result.changed_ratio,
        )
        analysis_frame = self._analysis_frame(frame)

        if not self._has_empty_reference():
            return self._publish(
                frame_width,
                frame_height,
                gate_decision,
                state="waiting_for_empty_reference",
                extra={"reason": "empty_reference_required"},
            )

        if not getattr(gate_decision, "should_sample", False):
            return self._publish(
                frame_width,
                frame_height,
                gate_decision,
                state="waiting_for_stable_frame",
            )

        self.snapshot_session_store.set_current_snapshot(analysis_frame)
        if not self.snapshot_session_store.ready_for_diff():
            self.snapshot_session_store.discard_current_snapshot()
            return self._publish(
                frame_width,
                frame_height,
                gate_decision,
                state="waiting_for_diff_pair",
            )

        previous_snapshot = self.snapshot_session_store.previous_snapshot
        current_snapshot = self.snapshot_session_store.current_snapshot
        change_result = self.change_detector.detect(
            previous_snapshot.image,
            current_snapshot.image,
            empty_reference=self._empty_reference_model(),
        )

        if change_result.global_shift:
            self.snapshot_session_store.discard_current_snapshot()
            return self._publish(
                frame_width,
                frame_height,
                gate_decision,
                state="resync_required",
                extra={
                    "resync_reason": "global_shift_detected",
                    "mask_nonzero_ratio": change_result.mask_nonzero_ratio,
                },
            )

        removed_ids = self._apply_removed_regions(change_result.regions)
        reverify_ids = self._apply_moved_regions(change_result.regions)
        roi_hints = self._roi_hints_for_analysis(change_result.regions)
        accepted_cards = []
        analysis_diagnostics = None
        accepted_cards_before_dedup = []
        accepted_cards_after_dedup = []
        if roi_hints:
            roi_masks = self._roi_masks_for_analysis(change_result, roi_hints)
            if roi_masks is None:
                analysis = self.snapshot_analyzer.analyze(current_snapshot.image, roi_hints=roi_hints)
            else:
                analysis = self.snapshot_analyzer.analyze(
                    current_snapshot.image,
                    roi_hints=roi_hints,
                    roi_masks=roi_masks,
                )
            accepted_cards = list(getattr(analysis, "cards", []) or [])
            accepted_cards_before_dedup = list(accepted_cards)
            analysis_diagnostics = getattr(analysis, "diagnostics", None) or {}
            accepted_cards_after_dedup = _deduplicate_overlapping_cards(accepted_cards)
            accepted_cards = _select_best_card_per_roi(accepted_cards_after_dedup, roi_hints)
            self._apply_accepted_cards(accepted_cards, roi_hints)

        if removed_ids or accepted_cards:
            self.snapshot_session_store.commit_current_snapshot()
            state = "state_updated"
        else:
            self.snapshot_session_store.discard_current_snapshot()
            state = self._idle_state(change_result.regions)

        self.last_diff_diagnostics = _build_last_diff_diagnostics(
            state=state,
            change_result=change_result,
            roi_hints=roi_hints,
            removed_ids=removed_ids,
            reverify_ids=reverify_ids,
            accepted_cards_before_dedup=accepted_cards_before_dedup,
            accepted_cards_after_dedup=accepted_cards_after_dedup,
            accepted_cards_after_roi_limit=accepted_cards,
            analysis_diagnostics=analysis_diagnostics,
        )

        return self._publish(
            frame_width,
            frame_height,
            gate_decision,
            state=state,
            extra={
                "change_region_count": len(change_result.regions),
                "roi_count": len(roi_hints),
                "removed_card_ids": removed_ids,
                "reverify_card_ids": reverify_ids,
                "accepted_card_count": len(accepted_cards),
                "mask_nonzero_ratio": change_result.mask_nonzero_ratio,
            },
        )

    def _analysis_frame(self, frame):
        if getattr(self.table_calibration, "calibrated", False):
            warped = self.table_calibration.warp_frame(frame)
            if warped is not None:
                self.runtime_metrics.add("state_first_diff_warped_frame", 1)
                return warped
        return frame

    def _has_empty_reference(self):
        store = self.snapshot_session_store
        return bool(
            getattr(store, "session_active", False)
            and getattr(store, "empty_reference_locked", False)
            and getattr(store, "empty_reference", None) is not None
        )

    def _empty_reference_model(self):
        model = BackgroundModel()
        model.capture(self.snapshot_session_store.empty_reference.image)
        return model

    def _apply_removed_regions(self, regions):
        removed_ids = []
        for region in regions:
            if region.kind != "removed":
                continue
            removed_ids.extend(self.table_state.remove_cards_intersecting_bbox(region.bbox))
        return removed_ids

    def _apply_moved_regions(self, regions):
        reverify_ids = []
        for region in regions:
            if region.kind != "moved_or_replaced":
                continue
            reverify_ids.extend(
                self.table_state.mark_cards_intersecting_bbox_needs_reverify(
                    region.bbox,
                    "moved_or_replaced",
                )
            )
        return reverify_ids

    def _roi_hints_for_analysis(self, regions):
        added_regions = [region.bbox for region in regions if region.kind == "added"]
        if added_regions:
            return added_regions
        return [region.bbox for region in regions if region.kind == "moved_or_replaced"]

    def _roi_masks_for_analysis(self, change_result, roi_hints):
        mask = getattr(change_result, "mask", None)
        if mask is None or not roi_hints:
            return None

        arr = np.asarray(mask)
        if arr.ndim < 2 or arr.size == 0:
            return None

        height, width = arr.shape[:2]
        roi_masks = []
        for roi_bbox in roi_hints:
            x, y, w, h = [int(value) for value in roi_bbox]
            x1 = max(0, min(width, x))
            y1 = max(0, min(height, y))
            x2 = max(x1, min(width, x + w))
            y2 = max(y1, min(height, y + h))
            roi_masks.append(arr[y1:y2, x1:x2].copy())
        return roi_masks

    def _apply_accepted_cards(self, cards, roi_hints):
        fallback_bbox = roi_hints[0] if len(roi_hints) == 1 else None
        for card in cards:
            card_id = card.get("name")
            if not card_id:
                continue
            self.table_state.upsert_locked(
                card_id,
                card.get("x", 0.0),
                card.get("y", 0.0),
                card.get("angle", 0.0),
                card.get("confidence", 0.0),
                self.frame_index,
                bbox=card.get("bbox", fallback_bbox),
            )

    def _idle_state(self, regions):
        if regions and all(region.kind == "noise_or_lighting" for region in regions):
            return "noise_or_lighting"
        return "no_state_change"

    def _publish(self, frame_width, frame_height, gate_decision, state, extra=None):
        cards = self.table_state.to_layout_cards()
        layout = {
            "source": self.runtime_profile,
            "state": state,
            "session": self._session_status(),
            "card_count": len(cards),
            "cards": cards,
            "gate_state": getattr(gate_decision, "state", None),
            "stable_for_ms": getattr(gate_decision, "stable_for_ms", 0),
            "last_diff": self.last_diff_diagnostics,
        }
        if extra:
            layout.update(extra)

        table_status = self.table_calibration.status()
        marker_ids = table_status.get("marker_ids") or []
        runtime_snapshot = {
            "profile": self.runtime_profile,
            "capture_width": frame_width,
            "capture_height": frame_height,
            "schedule_mode": "state_first_diff",
            "table": table_status,
            "aruco_calibrated": bool(table_status.get("calibrated", False)),
            "aruco_markers": len(marker_ids),
        }
        metrics_snapshot = self.runtime_metrics.snapshot()
        self.status_store.update_cv_state(
            cards=cards,
            metrics=metrics_snapshot,
            runtime=runtime_snapshot,
            operator=self.build_operator_snapshot_fn(
                cards=cards,
                metrics=metrics_snapshot,
                runtime=runtime_snapshot,
                layout=layout,
                warnings=list(self.operator_warnings),
            ),
            layout=layout,
            warnings=list(self.operator_warnings),
        )
        return {
            "action": "continue",
            "frame_width": frame_width,
            "frame_height": frame_height,
            "cards": cards,
            "layout": layout,
        }

    def _session_status(self):
        store = self.snapshot_session_store
        return {
            "active": bool(getattr(store, "session_active", False)),
            "empty_reference_locked": bool(getattr(store, "empty_reference_locked", False)),
            "empty_reference": getattr(store, "empty_reference", None) is not None,
            "previous_snapshot": getattr(store, "previous_snapshot", None) is not None,
            "current_snapshot": getattr(store, "current_snapshot", None) is not None,
            "ready_for_diff": bool(store.ready_for_diff()) if hasattr(store, "ready_for_diff") else False,
        }


def _deduplicate_overlapping_cards(cards, min_iou=0.55):
    ordered = sorted(
        cards,
        key=lambda card: float(card.get("confidence", 0.0)),
        reverse=True,
    )
    kept = []
    for card in ordered:
        bbox = card.get("bbox")
        if bbox is None:
            kept.append(card)
            continue
        if any(_bbox_iou(bbox, kept_card.get("bbox")) >= min_iou for kept_card in kept):
            continue
        kept.append(card)
    return kept


def _select_best_card_per_roi(cards, roi_hints):
    if not cards or not roi_hints:
        return cards

    selected = []
    selected_indexes = set()
    single_roi = len(roi_hints) == 1
    for roi_bbox in roi_hints:
        candidates = _cards_matching_roi(cards, roi_bbox, selected_indexes, center_required=True)
        if not candidates:
            candidates = _cards_matching_roi(cards, roi_bbox, selected_indexes, center_required=False)
        if not candidates and single_roi:
            candidates = [
                (index, card)
                for index, card in enumerate(cards)
                if index not in selected_indexes
            ]
        if not candidates:
            continue
        best_index, best_card = max(
            candidates,
            key=lambda item: float(item[1].get("confidence", 0.0)),
        )
        selected.append(best_card)
        selected_indexes.add(best_index)
    return selected


def _cards_matching_roi(cards, roi_bbox, selected_indexes, center_required):
    candidates = []
    for index, card in enumerate(cards):
        if index in selected_indexes:
            continue
        bbox = card.get("bbox")
        if bbox is None:
            continue
        if center_required:
            if _bbox_center_inside(bbox, roi_bbox):
                candidates.append((index, card))
            continue
        if _bbox_intersection_area(bbox, roi_bbox) > 0.0:
            candidates.append((index, card))
    return candidates


def _bbox_center_inside(bbox, container):
    x, y, w, h = [float(value) for value in bbox]
    cx = x + w / 2.0
    cy = y + h / 2.0
    rx, ry, rw, rh = [float(value) for value in container]
    return rx <= cx <= rx + rw and ry <= cy <= ry + rh


def _bbox_intersection_area(first, second):
    if first is None or second is None:
        return 0.0
    ax, ay, aw, ah = [float(value) for value in first]
    bx, by, bw, bh = [float(value) for value in second]
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh
    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    return inter_w * inter_h


def _bbox_iou(first, second):
    if first is None or second is None:
        return 0.0
    ax, ay, aw, ah = [float(value) for value in first]
    bx, by, bw, bh = [float(value) for value in second]
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh

    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    union = aw * ah + bw * bh - intersection
    if union <= 0.0:
        return 0.0
    return intersection / union


def _build_last_diff_diagnostics(
    state,
    change_result,
    roi_hints,
    removed_ids,
    reverify_ids,
    accepted_cards_before_dedup,
    accepted_cards_after_dedup,
    accepted_cards_after_roi_limit,
    analysis_diagnostics,
):
    return {
        "state": state,
        "change_region_count": len(change_result.regions),
        "regions": [_serialize_region(region) for region in change_result.regions],
        "roi_count": len(roi_hints),
        "roi_hints": [_serialize_bbox(bbox) for bbox in roi_hints],
        "removed_card_ids": list(removed_ids),
        "reverify_card_ids": list(reverify_ids),
        "accepted_card_count_before_dedup": len(accepted_cards_before_dedup),
        "accepted_card_count_after_dedup": len(accepted_cards_after_dedup),
        "accepted_card_count": len(accepted_cards_after_roi_limit),
        "accepted_cards_before_dedup": [
            _serialize_card(card) for card in accepted_cards_before_dedup
        ],
        "accepted_cards_after_dedup": [
            _serialize_card(card) for card in accepted_cards_after_dedup
        ],
        "accepted_cards_after_roi_limit": [
            _serialize_card(card) for card in accepted_cards_after_roi_limit
        ],
        "mask_nonzero_ratio": change_result.mask_nonzero_ratio,
        "ignored_small_count": change_result.ignored_small_count,
        "ignored_large_count": change_result.ignored_large_count,
        "analysis": _json_safe(analysis_diagnostics or {}),
    }


def _serialize_region(region):
    return {
        "bbox": _serialize_bbox(region.bbox),
        "area_ratio": float(region.area_ratio),
        "kind": region.kind,
        "previous_empty_ratio": float(region.previous_empty_ratio),
        "current_empty_ratio": float(region.current_empty_ratio),
    }


def _serialize_card(card):
    return {
        "name": card.get("name"),
        "confidence": float(card.get("confidence", 0.0)),
        "bbox": _serialize_bbox(card.get("bbox")) if card.get("bbox") is not None else None,
        "x": float(card.get("x", 0.0)),
        "y": float(card.get("y", 0.0)),
        "angle": float(card.get("angle", 0.0)),
    }


def _serialize_bbox(bbox):
    return [int(value) for value in bbox]


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
