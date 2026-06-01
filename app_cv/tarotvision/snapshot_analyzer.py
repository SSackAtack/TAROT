from dataclasses import dataclass
import math

import numpy as np

from tarotvision.card_detection import find_card_quads
from tarotvision.card_recognition import deskew_card_crop


@dataclass(frozen=True)
class SnapshotAnalysisResult:
    cards: list
    card_count: int
    diagnostics: dict | None = None


class SnapshotAnalyzer:
    def __init__(self, find_quads=None, crop_card=None, recognize_crop=None,
                 scene_width=26.0, scene_height=15.6):
        self.find_quads = find_quads or find_card_quads
        self.crop_card = crop_card or deskew_card_crop
        self.recognize_crop = recognize_crop
        self.scene_width = scene_width
        self.scene_height = scene_height

    def analyze(self, frame):
        cards = []
        diagnostics = {
            "quads_found": 0,
            "recognition_attempts": 0,
            "recognition_rejections": 0,
        }
        frame_height, frame_width = frame.shape[:2]
        quads = self.find_quads(frame)
        diagnostics["quads_found"] = len(quads)
        for quad in quads:
            crop = self.crop_card(frame, quad)
            diagnostics["recognition_attempts"] += 1
            recognition = self.recognize_crop(crop) if self.recognize_crop else None
            if not recognition:
                diagnostics["recognition_rejections"] += 1
                continue
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
        return SnapshotAnalysisResult(
            cards=cards,
            card_count=len(cards),
            diagnostics=diagnostics,
        )


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
