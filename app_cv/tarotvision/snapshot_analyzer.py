from dataclasses import dataclass

import numpy as np

from tarotvision.card_detection import find_card_quads
from tarotvision.card_recognition import deskew_card_crop


@dataclass(frozen=True)
class SnapshotAnalysisResult:
    cards: list
    card_count: int


class SnapshotAnalyzer:
    def __init__(self, find_quads=None, crop_card=None, recognize_crop=None):
        self.find_quads = find_quads or find_card_quads
        self.crop_card = crop_card or deskew_card_crop
        self.recognize_crop = recognize_crop

    def analyze(self, frame):
        cards = []
        for quad in self.find_quads(frame):
            crop = self.crop_card(frame, quad)
            recognition = self.recognize_crop(crop) if self.recognize_crop else None
            if not recognition:
                continue
            center_x, center_y = _quad_center(quad)
            cards.append({
                "name": recognition["name"],
                "x": center_x,
                "y": center_y,
                "angle": _quad_angle(quad),
                "confidence": recognition.get("confidence", 0.0),
                "orientation": recognition.get("orientation", "unknown"),
            })
        return SnapshotAnalysisResult(cards=cards, card_count=len(cards))


def _quad_points(quad):
    return np.asarray(quad, dtype=np.float32).reshape(4, 2)


def _quad_center(quad):
    points = _quad_points(quad)
    center = np.mean(points, axis=0)
    return float(center[0]), float(center[1])


def _quad_angle(quad):
    points = _quad_points(quad)
    vector = points[3] - points[0]
    return float(np.arctan2(vector[1], vector[0]))
