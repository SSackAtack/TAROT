from dataclasses import dataclass
import math
import os

import cv2
import numpy as np

from tarotvision.card_detection_profiles import find_card_quads_multi_profile
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
                 find_quads_with_debug=None):
        self.find_quads = find_quads or self._find_quads_default
        self.find_quads_with_debug = find_quads_with_debug
        self.crop_card = crop_card or deskew_card_crop
        self.recognize_crop = recognize_crop
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
            "recognition_debug": [],
        }
        frame_height, frame_width = frame.shape[:2]

        if roi_hints is not None:
            return self._analyze_rois(
                frame,
                roi_hints,
                cards,
                diagnostics,
                frame_width,
                frame_height,
            )

        if self.find_quads_with_debug is not None:
            detection_result = self.find_quads_with_debug(frame)
            quads = detection_result.quads
            diagnostics["detection"] = detection_result.debug
        else:
            quads = self.find_quads(frame)

        diagnostics["quads_found"] = len(quads)
        for quad in quads:
            self._recognize_quad(
                source_frame=frame,
                crop_quad=quad,
                layout_quad=quad,
                cards=cards,
                diagnostics=diagnostics,
                frame_width=frame_width,
                frame_height=frame_height,
            )
        return SnapshotAnalysisResult(
            cards=cards,
            card_count=len(cards),
            diagnostics=diagnostics,
        )

    def _analyze_rois(self, frame, roi_hints, cards, diagnostics, frame_width, frame_height):
        diagnostics["roi_count"] = len(roi_hints)
        diagnostics["roi_diagnostics"] = []
        diagnostics["roi_with_quads_count"] = 0
        diagnostics["roi_with_accepted_card_count"] = 0
        diagnostics["accepted_cards_before_dedup"] = 0
        diagnostics["accepted_cards_after_dedup"] = 0

        for roi_index, roi_bbox in enumerate(roi_hints):
            x, y, w, h = _clip_bbox(roi_bbox, frame_width, frame_height)
            roi_frame = frame[y:y + h, x:x + w]
            roi_diag = {
                "roi_index": roi_index,
                "roi_bbox": [x, y, w, h],
                "roi_area": int(w * h),
                "roi_quads_found": 0,
                "roi_accepted_cards": 0,
                "roi_recognition_attempts": 0,
                "roi_recognition_rejections": 0,
            }
            if roi_frame.size == 0:
                diagnostics["roi_diagnostics"].append(roi_diag)
                continue

            if self.find_quads_with_debug is not None:
                detection_result = self.find_quads_with_debug(roi_frame)
                quads = detection_result.quads
                roi_diag["roi_detection"] = detection_result.debug
            else:
                quads = self.find_quads(roi_frame)

            roi_diag["roi_quads_found"] = len(quads)
            diagnostics["quads_found"] += len(quads)
            if quads:
                diagnostics["roi_with_quads_count"] += 1

            accepted_before = len(cards)
            attempts_before = diagnostics["recognition_attempts"]
            rejections_before = diagnostics["recognition_rejections"]
            for quad in quads:
                self._recognize_quad(
                    source_frame=roi_frame,
                    crop_quad=quad,
                    layout_quad=_translate_quad(quad, x, y),
                    cards=cards,
                    diagnostics=diagnostics,
                    frame_width=frame_width,
                    frame_height=frame_height,
                )
            accepted_count = len(cards) - accepted_before
            roi_diag["roi_accepted_cards"] = accepted_count
            roi_diag["roi_recognition_attempts"] = diagnostics["recognition_attempts"] - attempts_before
            roi_diag["roi_recognition_rejections"] = diagnostics["recognition_rejections"] - rejections_before
            if accepted_count > 0:
                diagnostics["roi_with_accepted_card_count"] += 1
            diagnostics["roi_diagnostics"].append(roi_diag)

        diagnostics["accepted_cards_before_dedup"] = len(cards)
        diagnostics["accepted_cards_after_dedup"] = len(cards)
        return SnapshotAnalysisResult(
            cards=cards,
            card_count=len(cards),
            diagnostics=diagnostics,
        )

    def _recognize_quad(self, source_frame, crop_quad, layout_quad, cards,
                        diagnostics, frame_width, frame_height):
        crop = self.crop_card(source_frame, crop_quad)
        diagnostics["recognition_attempts"] += 1
        _write_debug_crop(crop, diagnostics["recognition_attempts"])

        recognition = self.recognize_crop(crop) if self.recognize_crop else None
        recognition_debug = None
        if isinstance(recognition, tuple):
            recognition, recognition_debug = recognition
        if recognition_debug is not None:
            diagnostics["recognition_debug"].append(
                _serialize_recognition_debug(recognition_debug)
            )
        if not recognition:
            diagnostics["recognition_rejections"] += 1
            return

        center_x, center_y = _quad_center(layout_quad)
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
                layout_quad,
                recognition.get("orientation", "unknown"),
            ),
            "confidence": recognition.get("confidence", 0.0),
            "orientation": recognition.get("orientation", "unknown"),
            "homography_angle_deg": recognition.get("homography_angle_deg", 0.0),
        })


def _quad_points(quad):
    return np.asarray(quad, dtype=np.float32).reshape(4, 2)


def _translate_quad(quad, offset_x, offset_y):
    points = _quad_points(quad).copy()
    points[:, 0] += float(offset_x)
    points[:, 1] += float(offset_y)
    return points.reshape(4, 1, 2)


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


def _clip_bbox(bbox, frame_width, frame_height):
    x, y, w, h = [int(value) for value in bbox]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(frame_width, x + w)
    y2 = min(frame_height, y + h)
    return x1, y1, max(0, x2 - x1), max(0, y2 - y1)


def _serialize_recognition_debug(debug):
    return {
        "crop_keypoints": int(debug.crop_keypoints),
        "reject_reason": debug.reject_reason,
        "top_matches": top_match_summary(debug, limit=5),
    }


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
