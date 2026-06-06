# -*- coding: utf-8 -*-
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
        self.build_operator_snapshot_fn = build_operator_snapshot_fn or (lambda: {})
        self.operator_warnings = operator_warnings or []
        self.runtime_profile = runtime_profile
        self.frame_index = 0

    def process_frame(self, frame, motion_result, frame_width, frame_height, frame_loop_start):
        self.frame_index += 1
        gate_decision = self.snapshot_gate.update(motion_result, frame_loop_start)
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
        if roi_hints:
            analysis = self.snapshot_analyzer.analyze(current_snapshot.image, roi_hints=roi_hints)
            accepted_cards = list(getattr(analysis, "cards", []) or [])
            self._apply_accepted_cards(accepted_cards, roi_hints)

        if removed_ids or accepted_cards:
            self.snapshot_session_store.commit_current_snapshot()
            state = "state_updated"
        else:
            self.snapshot_session_store.discard_current_snapshot()
            state = self._idle_state(change_result.regions)

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
            "card_count": len(cards),
            "cards": cards,
            "gate_state": getattr(gate_decision, "state", None),
            "stable_for_ms": getattr(gate_decision, "stable_for_ms", 0),
        }
        if extra:
            layout.update(extra)

        self.status_store.update_cv_state(
            frame_width=frame_width,
            frame_height=frame_height,
            cards=cards,
            layout=layout,
            metrics=self.runtime_metrics.snapshot(),
            calibration=self.table_calibration.status(),
            operator=self.build_operator_snapshot_fn(),
            warnings=list(self.operator_warnings),
        )
        return {
            "action": "continue",
            "frame_width": frame_width,
            "frame_height": frame_height,
            "cards": cards,
            "layout": layout,
        }
