from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class DiffMethodResult:
    diff: np.ndarray
    mask: np.ndarray


def run_diff_method(name, previous, current):
    if name == "gray_absdiff_fixed":
        return _gray_absdiff(previous, current, threshold=24)
    if name == "gray_absdiff_gaussian":
        return _gray_absdiff(previous, current, threshold=20, blur="gaussian")
    if name == "gray_absdiff_median":
        return _gray_absdiff(previous, current, threshold=20, blur="median")
    if name == "gray_absdiff_otsu":
        return _gray_absdiff_otsu(previous, current)
    if name == "lab_absdiff_weighted":
        return _weighted_color_absdiff(previous, current, cv2.COLOR_BGR2LAB, weights=(0.7, 0.15, 0.15), threshold=18)
    if name == "hsv_absdiff_weighted":
        return _weighted_color_absdiff(previous, current, cv2.COLOR_BGR2HSV, weights=(0.15, 0.35, 0.5), threshold=20)
    if name == "illumination_normalized_gray_absdiff":
        return _illumination_normalized_gray_absdiff(previous, current)
    raise ValueError(f"Unknown Stage 1 diff method: {name}")


def available_methods():
    return [
        "gray_absdiff_fixed",
        "gray_absdiff_gaussian",
        "gray_absdiff_median",
        "lab_absdiff_weighted",
        "hsv_absdiff_weighted",
        "gray_absdiff_otsu",
        "illumination_normalized_gray_absdiff",
    ]


def _gray_absdiff(previous, current, threshold, blur=None):
    previous_gray = _to_gray(previous)
    current_gray = _to_gray(current)
    if blur == "gaussian":
        previous_gray = cv2.GaussianBlur(previous_gray, (5, 5), 0)
        current_gray = cv2.GaussianBlur(current_gray, (5, 5), 0)
    elif blur == "median":
        previous_gray = cv2.medianBlur(previous_gray, 5)
        current_gray = cv2.medianBlur(current_gray, 5)
    diff = cv2.absdiff(previous_gray, current_gray)
    _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    return DiffMethodResult(diff=diff, mask=_clean_mask(mask))


def _gray_absdiff_otsu(previous, current):
    diff = cv2.absdiff(_to_gray(previous), _to_gray(current))
    if int(np.max(diff)) == 0:
        mask = np.zeros(diff.shape, dtype=np.uint8)
    else:
        _, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return DiffMethodResult(diff=diff, mask=_clean_mask(mask))


def _weighted_color_absdiff(previous, current, conversion, weights, threshold):
    previous_color = cv2.cvtColor(previous, conversion)
    current_color = cv2.cvtColor(current, conversion)
    channel_diffs = [
        cv2.absdiff(previous_color[:, :, idx], current_color[:, :, idx]).astype(np.float32) * weight
        for idx, weight in enumerate(weights)
    ]
    diff = np.clip(np.sum(channel_diffs, axis=0), 0, 255).astype(np.uint8)
    _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    return DiffMethodResult(diff=diff, mask=_clean_mask(mask))


def _illumination_normalized_gray_absdiff(previous, current):
    previous_gray = cv2.equalizeHist(_to_gray(previous))
    current_gray = cv2.equalizeHist(_to_gray(current))
    diff = cv2.absdiff(previous_gray, current_gray)
    _, mask = cv2.threshold(diff, 24, 255, cv2.THRESH_BINARY)
    return DiffMethodResult(diff=diff, mask=_clean_mask(mask))


def _to_gray(frame):
    if frame.ndim == 2:
        return frame
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def _clean_mask(mask):
    kernel = np.ones((5, 5), dtype=np.uint8)
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
