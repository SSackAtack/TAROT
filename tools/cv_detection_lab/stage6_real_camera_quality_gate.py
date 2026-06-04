"""Offline-only quality gate for Stage 6 real-camera crops."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np


ACCEPT = "ACCEPT_FOR_IDENTIFICATION"
RETRY = "RETRY_CAPTURE"
MANUAL = "MANUAL_REVIEW"
THRESHOLD_SCOPE = "BENCHMARK_HEURISTIC_ONLY"


@dataclass(frozen=True)
class QualityGateResult:
    decision: str
    reasons: list
    local_specular_component_ratio: float
    highlight_occlusion_ratio: float
    usable_detail_ratio: float
    highlight_pixel_ratio: float
    confidence_score: float | None
    confidence_gap: float | None
    threshold_scope: str = THRESHOLD_SCOPE

    def to_dict(self):
        return asdict(self)


def evaluate_quality_gate(crop, confidence_score=None, confidence_gap=None):
    image = _as_bgr(crop)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    highlight_mask = build_highlight_mask(image)
    area = float(max(1, gray.size))
    component_ratio = _largest_component_ratio(highlight_mask)
    highlight_ratio = float(np.count_nonzero(highlight_mask)) / area

    h, w = gray.shape[:2]
    central = highlight_mask[int(h * 0.12):int(h * 0.88), int(w * 0.12):int(w * 0.88)]
    central_area = float(max(1, central.size))
    occlusion_ratio = float(np.count_nonzero(central)) / central_area

    edges = cv2.Canny(gray, 45, 135)
    usable = edges[highlight_mask == 0]
    usable_detail = float(np.count_nonzero(usable)) / float(max(1, usable.size))

    reasons = []
    if component_ratio >= 0.065 or (component_ratio >= 0.015 and occlusion_ratio >= 0.08):
        decision = RETRY
        reasons.append("SPECULAR_OCCLUSION")
    elif component_ratio >= 0.035 or (component_ratio >= 0.012 and occlusion_ratio >= 0.055):
        decision = MANUAL
        reasons.append("SPECULAR_HIGHLIGHT_WARNING")
    elif usable_detail < 0.035:
        decision = MANUAL
        reasons.append("LOW_USABLE_DETAIL")
    else:
        decision = ACCEPT

    if confidence_score is not None and confidence_gap is not None:
        if decision == ACCEPT and confidence_score < 0.03 and confidence_gap < 0.01:
            decision = MANUAL
            reasons.append("LOW_MATCH_SIGNAL")
        elif decision == MANUAL and confidence_score < 0.015 and confidence_gap < 0.005:
            decision = RETRY
            reasons.append("LOW_MATCH_SIGNAL")

    return QualityGateResult(
        decision=decision,
        reasons=reasons,
        local_specular_component_ratio=round(component_ratio, 6),
        highlight_occlusion_ratio=round(occlusion_ratio, 6),
        usable_detail_ratio=round(usable_detail, 6),
        highlight_pixel_ratio=round(highlight_ratio, 6),
        confidence_score=None if confidence_score is None else round(float(confidence_score), 6),
        confidence_gap=None if confidence_gap is None else round(float(confidence_gap), 6),
    ), highlight_mask


def build_highlight_mask(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    saturation = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1] if image.ndim == 3 else np.zeros_like(gray)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    local_mean = cv2.GaussianBlur(gray, (41, 41), 0)
    local_delta = cv2.subtract(blurred, local_mean)
    bright_threshold = max(125.0, float(np.percentile(gray, 78)))
    bright = gray >= bright_threshold
    locally_bright = local_delta >= 16

    gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    gradient = cv2.magnitude(gx, gy)
    low_texture = gradient <= max(42.0, float(np.percentile(gradient, 68)))

    mask = np.zeros_like(gray, dtype=np.uint8)
    low_saturation = saturation <= 95
    mask[bright & locally_bright & low_texture & low_saturation] = 255
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
    return mask


def build_quality_gate_overlay(crop, mask, result):
    image = _as_bgr(crop)
    overlay = image.copy()
    overlay[mask > 0] = (0, 0, 255)
    blended = cv2.addWeighted(image, 0.55, overlay, 0.45, 0)
    panel = np.zeros((image.shape[0] + 150, max(520, image.shape[1]), 3), dtype=np.uint8)
    panel[:image.shape[0], :image.shape[1]] = blended
    lines = [
        f"decision: {result.decision}",
        f"component={result.local_specular_component_ratio:.3f} occlusion={result.highlight_occlusion_ratio:.3f}",
        f"usable_detail={result.usable_detail_ratio:.3f} highlight={result.highlight_pixel_ratio:.3f}",
        f"reasons={','.join(result.reasons) if result.reasons else 'none'}",
        f"scope={result.threshold_scope}",
    ]
    for index, line in enumerate(lines):
        cv2.putText(panel, line, (10, image.shape[0] + 25 + index * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (225, 225, 225), 1, cv2.LINE_AA)
    return panel


def _largest_component_ratio(mask):
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        return 0.0
    largest = max(int(stats[index, cv2.CC_STAT_AREA]) for index in range(1, count))
    return float(largest) / float(max(1, mask.size))


def _as_bgr(crop):
    if crop is None or not hasattr(crop, "shape") or crop.size == 0:
        raise ValueError("Quality gate requires a non-empty crop.")
    return cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR) if crop.ndim == 2 else crop.copy()
