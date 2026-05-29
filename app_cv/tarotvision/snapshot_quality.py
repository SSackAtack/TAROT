from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class SnapshotQuality:
    accepted: bool
    quality_score: float
    blur_score: float
    brightness: float
    contrast: float
    reject_reason: str = None


@dataclass(frozen=True)
class SelectedSnapshot:
    index: int
    frame: object
    quality: SnapshotQuality


def _to_gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def score_snapshot(frame, min_blur_score=20.0,
                   min_brightness=15.0, max_brightness=245.0,
                   min_contrast=10.0):
    gray = _to_gray(frame)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if brightness < min_brightness:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "too_dark")
    if brightness > max_brightness:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "too_bright")
    if contrast < min_contrast:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "low_contrast")
    if blur_score < min_blur_score:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "blurry")

    quality_score = min(1.0, (blur_score / 200.0) * 0.5 + (contrast / 80.0) * 0.5)
    return SnapshotQuality(True, quality_score, blur_score, brightness, contrast)


def choose_best_snapshot(frames, **score_kwargs):
    best = None
    for index, frame in enumerate(frames):
        quality = score_snapshot(frame, **score_kwargs)
        if not quality.accepted:
            continue
        candidate = SelectedSnapshot(index, frame, quality)
        if best is None or candidate.quality.quality_score > best.quality.quality_score:
            best = candidate
    return best
