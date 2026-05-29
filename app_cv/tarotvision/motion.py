from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class MotionResult:
    motion_detected: bool
    scene_settled: bool
    changed_ratio: float


class MotionDetector:
    def __init__(self, min_changed_ratio=0.02, pixel_threshold=25, settle_frames=3):
        self.min_changed_ratio = min_changed_ratio
        self.pixel_threshold = pixel_threshold
        self.settle_frames = settle_frames
        self.previous_gray = None
        self.still_frames = 0
        self.had_motion = False

    def update(self, gray_frame):
        gray = np.asarray(gray_frame)
        if self.previous_gray is None:
            self.previous_gray = gray.copy()
            return MotionResult(False, False, 0.0)

        diff = cv2.absdiff(self.previous_gray, gray)
        changed = diff > self.pixel_threshold
        changed_ratio = float(np.count_nonzero(changed)) / float(changed.size)
        motion_detected = changed_ratio >= self.min_changed_ratio

        if motion_detected:
            self.had_motion = True
            self.still_frames = 0
        else:
            self.still_frames += 1

        scene_settled = self.had_motion and self.still_frames >= self.settle_frames
        if scene_settled:
            self.had_motion = False

        self.previous_gray = gray.copy()
        return MotionResult(motion_detected, scene_settled, changed_ratio)
