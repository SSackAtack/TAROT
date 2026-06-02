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

    def analyze(self, frame):
        cards = []
        diagnostics = {
            "quads_found": 0,
            "recognition_attempts": 0,
            "recognition_rejections": 0,
            "candidate_validation_rejections": 0,
            "recognition_candidates": [],
            "recognition_score": 0.0,
        }
        frame_height, frame_width = frame.shape[:2]
        recognition_score_total = 0.0

        if self.find_quads_with_debug is not None:
            detection_result = self.find_quads_with_debug(frame)
            quads = detection_result.quads
            diagnostics["detection"] = detection_result.debug
        else:
            quads = self.find_quads(frame)

        diagnostics["quads_found"] = len(quads)
        for quad in quads:
            crop = self.crop_card(frame, quad)
            candidate_index = len(diagnostics["recognition_candidates"]) + 1
            candidate_validation = self._validate_candidate_crop(crop)
            if candidate_validation is not None and not candidate_validation.accepted:
                diagnostics["candidate_validation_rejections"] += 1
                diagnostics["recognition_candidates"].append(_candidate_diagnostics(
                    candidate_index,
                    None,
                    None,
                    candidate_validation,
                ))
                continue

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
            candidate_debug["name"] = recognition["name"]
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
