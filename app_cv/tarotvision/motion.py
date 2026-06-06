from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class MotionResult:
    motion_detected: bool
    scene_settled: bool
    changed_ratio: float


@dataclass(frozen=True)
class MotionMask:
    mask: np.ndarray  # Tablica bool o wymiarach klatki
    area: int         # Liczba pikseli w masce
    key: tuple        # Klucz unikalny cache (height, width, corners_tuple)


class MotionMaskCache:
    def __init__(self):
        self._current = None

    def update(self, frame_shape, corners):
        if corners is None:
            self._current = None
            return None

        height, width = frame_shape[:2]
        pts = np.rint(corners).astype(np.int32)

        key = (height, width, tuple(map(tuple, pts.tolist())))
        if self._current is not None and self._current.key == key:
            return self._current

        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [pts.reshape((-1, 1, 2))], 1)

        area = int(np.count_nonzero(mask))
        if area <= 0:
            self._current = None
            return None

        self._current = MotionMask(mask=mask.astype(bool), area=area, key=key)
        return self._current


class MotionDetector:
    def __init__(self, min_changed_ratio=0.02, pixel_threshold=25, settle_frames=3):
        self.min_changed_ratio = min_changed_ratio
        self.pixel_threshold = pixel_threshold
        self.settle_frames = settle_frames
        self.previous_gray = None
        self.still_frames = 0
        self.had_motion = False

    def update(self, gray_frame, mask=None):
        gray = np.asarray(gray_frame)

        if self.previous_gray is None or self.previous_gray.shape != gray.shape:
            self.previous_gray = gray.copy()
            self.still_frames = 0
            self.had_motion = False
            return MotionResult(False, False, 0.0)

        diff = cv2.absdiff(self.previous_gray, gray)
        changed = diff > self.pixel_threshold

        if mask is not None and mask.mask.shape == changed.shape and mask.area > 0:
            changed_ratio = float(np.count_nonzero(changed & mask.mask)) / float(mask.area)
        else:
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
