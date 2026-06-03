from dataclasses import dataclass
import math
import os

import cv2
import numpy as np

from tarotvision.card_detection_profiles import find_card_quads_multi_profile
from tarotvision.card_candidate_validation import validate_card_candidate_crop
from tarotvision.card_recognition import deskew_card_crop
from tarotvision.recognition_debug import top_match_summary


@dataclass(frozen=True)
class SnapshotAnalysisResult:
    cards: list
    card_count: int
    diagnostics: dict | None = None


class SnapshotAnalyzer:
    def __init__(self, find_quads=None, crop_card=None, recognize_crop=None,
                 scene_width=26.0, scene_height=15.6, background_model=None,
                 find_quads_with_debug=None, recognize_crop_with_debug=None,
                 validate_candidate_crop=validate_card_candidate_crop):
        self.find_quads = find_quads or self._find_quads_default
        self.find_quads_with_debug = find_quads_with_debug
        self.crop_card = crop_card or deskew_card_crop
        self.recognize_crop = recognize_crop
        self.recognize_crop_with_debug = recognize_crop_with_debug
        self.validate_candidate_crop = validate_candidate_crop
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.background_model = background_model

    def _find_quads_default(self, frame):
        return find_card_quads_multi_profile(frame, background_model=self.background_model).quads

    def analyze(self, frame, roi_hints=None):
        cards = []
        diagnostics = {
            "quads_found": 0,
            "recognition_attempts": 0,
            "recognition_rejections": 0,
            "candidate_validation_rejections": 0,
            "recognition_candidates": [],
            "recognition_score": 0.0,
            "roi_limited": roi_hints is not None,
            "roi_count": len(roi_hints or []),
            "roi_diagnostics": [],
            "roi_with_quads_count": 0,
            "roi_with_accepted_card_count": 0,
            "accepted_cards_before_dedup": 0,
            "accepted_cards_after_dedup": 0,
        }
        frame_height, frame_width = frame.shape[:2]
        recognition_score_total = 0.0
        quad_roi_indices = []

        if roi_hints is not None:
            quads = []
            detection_debug = {"roi_hints": []}
            for roi_index, bbox in enumerate(roi_hints):
                x, y, w, h = _clamp_bbox(bbox, frame_width, frame_height)
                if w <= 0 or h <= 0:
                    continue
                crop_frame = frame[y:y + h, x:x + w]
                crop_quads = self.find_quads(crop_frame)
                for crop_quad in crop_quads:
                    points = _quad_points(crop_quad).copy()
                    points[:, 0] += x
                    points[:, 1] += y
                    quads.append(points)
                    quad_roi_indices.append(len(diagnostics["roi_diagnostics"]))
                roi_payload = _empty_roi_diagnostics(
                    roi_index=roi_index,
                    bbox=[x, y, w, h],
                    quad_count=len(crop_quads),
                )
                diagnostics["roi_diagnostics"].append(roi_payload)
                detection_debug["roi_hints"].append({
                    "bbox": [x, y, w, h],
                    "quads": len(crop_quads),
                })
            diagnostics["detection"] = detection_debug
        elif self.find_quads_with_debug is not None:
            detection_result = self.find_quads_with_debug(frame)
            quads = detection_result.quads
            diagnostics["detection"] = detection_result.debug
        else:
            quads = self.find_quads(frame)

        diagnostics["quads_found"] = len(quads)
        for quad_index, quad in enumerate(quads):
            crop = self.crop_card(frame, quad)
            candidate_index = len(diagnostics["recognition_candidates"]) + 1
            roi_payload = _roi_payload_for_quad(diagnostics, quad_roi_indices, quad_index)
            candidate_validation = self._validate_candidate_crop(crop)
            if candidate_validation is not None and not candidate_validation.accepted:
                diagnostics["candidate_validation_rejections"] += 1
                _record_roi_validation_rejection(roi_payload, candidate_validation.reject_reason)
                diagnostics["recognition_candidates"].append(_candidate_diagnostics(
                    candidate_index,
                    None,
                    None,
                    candidate_validation,
                ))
                continue

            _record_roi_candidate_after_validation(roi_payload)
            diagnostics["recognition_attempts"] += 1
            _write_debug_crop(crop, diagnostics["recognition_attempts"])

            recognition, recognition_debug = self._recognize_with_optional_debug(crop)
            candidate_debug = _candidate_diagnostics(
                candidate_index,
                recognition,
                recognition_debug,
                candidate_validation,
            )
            diagnostics["recognition_candidates"].append(candidate_debug)
            if not recognition:
                diagnostics["recognition_rejections"] += 1
                _record_roi_recognition_rejection(roi_payload, candidate_debug.get("reject_reason"))
                continue
            candidate_score = _candidate_recognition_score(
                recognition,
                recognition_debug,
            )
            candidate_debug["recognition_score"] = candidate_score
            recognition_score_total += candidate_score
            center_x, center_y = _quad_center(quad)
            scene_x, scene_y = _frame_to_scene(
                center_x,
                center_y,
                frame_width,
                frame_height,
                self.scene_width,
                self.scene_height,
            )
            cards.append({
                "name": recognition["name"],
                "x": scene_x,
                "y": scene_y,
                "angle": _layout_angle(
                    quad,
                    recognition.get("orientation", "unknown"),
                ),
                "confidence": recognition.get("confidence", 0.0),
                "orientation": recognition.get("orientation", "unknown"),
                "homography_angle_deg": recognition.get("homography_angle_deg", 0.0),
            })
            _record_roi_accepted_card(roi_payload)
            candidate_debug["name"] = recognition["name"]
        _finalize_roi_diagnostics(diagnostics, cards)
        if diagnostics["quads_found"] > 0:
            diagnostics["recognition_score"] = round(
                recognition_score_total / diagnostics["quads_found"],
                3,
            )
        return SnapshotAnalysisResult(
            cards=cards,
            card_count=len(cards),
            diagnostics=diagnostics,
        )

    def _recognize_with_optional_debug(self, crop):
        if self.recognize_crop_with_debug is not None:
            return self.recognize_crop_with_debug(crop)
        recognition = self.recognize_crop(crop) if self.recognize_crop else None
        return recognition, None

    def _validate_candidate_crop(self, crop):
        if self.validate_candidate_crop is None:
            return None
        if crop is None or not hasattr(crop, "shape"):
            return None
        return self.validate_candidate_crop(crop)


def _quad_points(quad):
    return np.asarray(quad, dtype=np.float32).reshape(4, 2)


def _clamp_bbox(bbox, frame_width, frame_height):
    x, y, w, h = [int(v) for v in bbox]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(frame_width, x + max(0, w))
    y2 = min(frame_height, y + max(0, h))
    return x1, y1, max(0, x2 - x1), max(0, y2 - y1)


def _empty_roi_diagnostics(roi_index, bbox, quad_count):
    return {
        "roi_index": int(roi_index),
        "roi_bbox": list(bbox),
        "roi_area": int(bbox[2] * bbox[3]),
        "roi_quads_found": int(quad_count),
        "roi_candidates_after_validation": 0,
        "roi_validation_rejections": 0,
        "roi_recognition_attempts": 0,
        "roi_recognition_rejections": 0,
        "roi_accepted_cards": 0,
        "roi_reject_reasons": {},
    }


def _roi_payload_for_quad(diagnostics, quad_roi_indices, quad_index):
    if quad_index >= len(quad_roi_indices):
        return None
    roi_index = quad_roi_indices[quad_index]
    roi_diagnostics = diagnostics.get("roi_diagnostics") or []
    if roi_index < 0 or roi_index >= len(roi_diagnostics):
        return None
    return roi_diagnostics[roi_index]


def _record_roi_validation_rejection(roi_payload, reject_reason):
    if roi_payload is None:
        return
    roi_payload["roi_validation_rejections"] += 1
    _record_roi_reject_reason(roi_payload, reject_reason or "validation_rejected")


def _record_roi_candidate_after_validation(roi_payload):
    if roi_payload is None:
        return
    roi_payload["roi_candidates_after_validation"] += 1
    roi_payload["roi_recognition_attempts"] += 1


def _record_roi_recognition_rejection(roi_payload, reject_reason):
    if roi_payload is None:
        return
    roi_payload["roi_recognition_rejections"] += 1
    _record_roi_reject_reason(roi_payload, reject_reason or "recognition_rejected")


def _record_roi_accepted_card(roi_payload):
    if roi_payload is None:
        return
    roi_payload["roi_accepted_cards"] += 1


def _record_roi_reject_reason(roi_payload, reject_reason):
    reasons = roi_payload["roi_reject_reasons"]
    reasons[reject_reason] = reasons.get(reject_reason, 0) + 1


def _finalize_roi_diagnostics(diagnostics, cards):
    roi_diagnostics = diagnostics.get("roi_diagnostics") or []
    diagnostics["roi_with_quads_count"] = sum(
        1 for roi in roi_diagnostics if roi["roi_quads_found"] > 0
    )
    diagnostics["roi_with_accepted_card_count"] = sum(
        1 for roi in roi_diagnostics if roi["roi_accepted_cards"] > 0
    )
    diagnostics["accepted_cards_before_dedup"] = len(cards)
    diagnostics["accepted_cards_after_dedup"] = len(cards)


def _quad_center(quad):
    points = _quad_points(quad)
    center = np.mean(points, axis=0)
    return float(center[0]), float(center[1])


def _quad_angle(quad):
    points = _order_quad_points(quad)
    top_left = points[0]
    top_right = points[1]
    vector = top_right - top_left
    return -float(np.arctan2(vector[1], vector[0]))


def _layout_angle(quad, orientation):
    angle = _quad_angle(quad)
    if orientation == "reversed":
        angle += math.pi
    return angle


def _order_quad_points(quad):
    points = _quad_points(quad)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(4)
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = points[np.argmin(sums)]
    ordered[1] = points[np.argmin(diffs)]
    ordered[2] = points[np.argmax(sums)]
    ordered[3] = points[np.argmax(diffs)]
    return ordered


def _frame_to_scene(center_x, center_y, frame_width, frame_height,
                    scene_width, scene_height):
    scene_x = (center_x / frame_width * 2.0 - 1.0) * (scene_width / 2.0)
    scene_y = (1.0 - center_y / frame_height * 2.0) * (scene_height / 2.0)
    return float(scene_x), float(scene_y)


def _candidate_diagnostics(index, recognition, recognition_debug, candidate_validation=None):
    top_matches = top_match_summary(recognition_debug) if recognition_debug else []
    validation_payload = _validation_diagnostics(candidate_validation)
    return {
        "index": int(index),
        "accepted": recognition is not None,
        "reject_reason": (
            recognition_debug.reject_reason
            if recognition_debug is not None
            else (
                candidate_validation.reject_reason
                if candidate_validation is not None and not candidate_validation.accepted
                else None
            )
        ),
        "candidate_validation": validation_payload,
        "crop_keypoints": (
            int(recognition_debug.crop_keypoints)
            if recognition_debug is not None else None
        ),
        "top_matches": top_matches,
        "score_margin": _score_margin(top_matches),
    }


def _validation_diagnostics(candidate_validation):
    if candidate_validation is None:
        return None
    return {
        "accepted": bool(candidate_validation.accepted),
        "reject_reason": candidate_validation.reject_reason,
        "contrast": candidate_validation.contrast,
        "edge_density": candidate_validation.edge_density,
        "dark_pixel_ratio": candidate_validation.dark_pixel_ratio,
        "border_edge_density": candidate_validation.border_edge_density,
        "border_dark_ratio": candidate_validation.border_dark_ratio,
    }


def _candidate_recognition_score(recognition, recognition_debug):
    if recognition_debug is not None:
        top_matches = top_match_summary(recognition_debug, limit=1)
        if top_matches:
            return round(min(float(top_matches[0]["score"]) / 30.0, 1.0), 3)

    match_count = float(recognition.get("match_count", 0.0))
    inlier_ratio = float(recognition.get("inlier_ratio", recognition.get("confidence", 0.0)))
    if match_count <= 0:
        return round(max(0.0, min(inlier_ratio, 1.0)), 3)
    return round(min(match_count / 30.0, 1.0) * max(0.0, min(inlier_ratio, 1.0)), 3)


def _score_margin(top_matches):
    if len(top_matches) < 2:
        return None
    return round(
        float(top_matches[0].get("score", 0.0))
        - float(top_matches[1].get("score", 0.0)),
        3,
    )


def _debug_images_enabled():
    return os.environ.get("TAROTVISION_DEBUG_IMAGES", "0") == "1"


def _debug_log_dir():
    return os.environ.get(
        "TAROTVISION_LOG_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs")),
    )


def _write_debug_crop(crop, index):
    if not _debug_images_enabled() or crop is None:
        return
    try:
        log_dir = _debug_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        cv2.imwrite(os.path.join(log_dir, f"debug_crop_{index}.jpg"), crop)
    except Exception:
        pass
