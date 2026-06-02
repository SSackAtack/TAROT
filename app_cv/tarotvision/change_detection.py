from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ChangeDetectorConfig:
    threshold: int = 20
    min_area_ratio: float = 0.002
    max_area_ratio: float = 0.35
    global_shift_ratio: float = 0.45
    padding_px: int = 16


@dataclass(frozen=True)
class ChangeRegion:
    bbox: tuple[int, int, int, int]
    area_ratio: float
    kind: str


@dataclass(frozen=True)
class ChangeDetectionResult:
    regions: list[ChangeRegion]
    mask_nonzero_ratio: float
    global_shift: bool
    ignored_small_count: int
    ignored_large_count: int


class ChangeDetector:
    def __init__(self, config=None):
        self.config = config or ChangeDetectorConfig()

    def detect(self, previous_frame, current_frame, empty_reference=None):
        previous_gray = _to_gray(previous_frame)
        current_gray = _to_gray(current_frame)
        if previous_gray.shape != current_gray.shape:
            return ChangeDetectionResult([], 0.0, True, 0, 0)

        raw_mask = _difference_mask(previous_gray, current_gray, self.config.threshold)
        mask_ratio = _mask_ratio(raw_mask)
        if mask_ratio >= self.config.global_shift_ratio:
            return ChangeDetectionResult([], mask_ratio, True, 0, 0)

        contours, _ = cv2.findContours(raw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        frame_area = float(raw_mask.shape[0] * raw_mask.shape[1])
        regions = []
        ignored_small = 0
        ignored_large = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area_ratio = float(w * h) / frame_area
            if area_ratio < self.config.min_area_ratio:
                ignored_small += 1
                continue
            if area_ratio > self.config.max_area_ratio:
                ignored_large += 1
                continue
            bbox = _pad_bbox((x, y, w, h), raw_mask.shape[1], raw_mask.shape[0], self.config.padding_px)
            regions.append(ChangeRegion(
                bbox=bbox,
                area_ratio=area_ratio,
                kind=_classify_region(current_frame, bbox, empty_reference),
            ))

        regions.sort(key=lambda region: region.area_ratio, reverse=True)
        return ChangeDetectionResult(regions, mask_ratio, False, ignored_small, ignored_large)


def _to_gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def _difference_mask(previous_gray, current_gray, threshold):
    diff = cv2.absdiff(previous_gray, current_gray)
    _, mask = cv2.threshold(diff, int(threshold), 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def _mask_ratio(mask):
    if mask is None or mask.size == 0:
        return 0.0
    return float(np.count_nonzero(mask)) / float(mask.size)


def _pad_bbox(bbox, width, height, padding):
    x, y, w, h = bbox
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(width, x + w + padding)
    y2 = min(height, y + h + padding)
    return (x1, y1, x2 - x1, y2 - y1)


def _classify_region(current_frame, bbox, empty_reference):
    if empty_reference is None or not getattr(empty_reference, "active", False):
        return "added_or_moved"
    x, y, w, h = bbox
    mask = empty_reference.foreground_mask(current_frame)
    if mask is None:
        return "added_or_moved"
    roi = mask[y:y + h, x:x + w]
    if roi.size == 0:
        return "added_or_moved"
    foreground_ratio = float(np.count_nonzero(roi)) / float(roi.size)
    return "added_or_moved" if foreground_ratio >= 0.10 else "removed"
