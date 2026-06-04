"""Stage 5 Crop Quality Validation methods for the offline CV detection lab.

This module evaluates crop quality only. It does NOT identify cards, run ORB,
FLANN, template matching, OCR, or compare crops with a card database.
"""
from dataclasses import asdict, dataclass
from typing import Optional

import cv2
import numpy as np


QUALITY_METHOD = "quality_metric_suite_v1"
THRESHOLD_STATUS = "BENCHMARK_HEURISTIC_ONLY"
EXPECTED_ASPECT_RATIO = 1.65
EXPECTED_WIDTH = 300
EXPECTED_HEIGHT = 495


@dataclass(frozen=True)
class CropQualityMetrics:
    crop_quality_status: str
    crop_quality_score: float
    identification_readiness_score: float
    edge_cut_risk: bool
    edge_cut_risk_score: float
    border_visible_score: float
    border_continuity_score: float
    missing_border_score: float
    corner_visibility_score: float
    card_edge_proximity_to_crop_edge: float
    card_fill_ratio: float
    card_fill_ratio_score: float
    background_margin_score: float
    top_margin_ratio: float
    bottom_margin_ratio: float
    left_margin_ratio: float
    right_margin_ratio: float
    overexposed_pixel_ratio: float
    underexposed_pixel_ratio: float
    top_reflection_score: float
    brightness_mean: float
    brightness_std: float
    brightness_mean_score: float
    contrast_score: float
    histogram_spread_score: float
    dynamic_range_score: float
    variance_of_laplacian: float
    variance_of_laplacian_blur_score: float
    tenengrad_score: float
    tenengrad_sharpness_score: float
    edge_density_score: float
    texture_density_score: float
    internal_detail_score: float
    aspect_ratio_error: float
    aspect_ratio_error_score: float
    crop_size_score: float
    quality_flags: list
    reject_reason: Optional[str]
    warning_reason: Optional[str]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class CropQualityResult:
    crop_index: int
    metrics: CropQualityMetrics
    overlay: Optional[np.ndarray]

    def to_dict(self):
        return {
            "crop_index": self.crop_index,
            "crop_quality_status": self.metrics.crop_quality_status,
            "crop_quality_score": self.metrics.crop_quality_score,
            "identification_readiness_score": self.metrics.identification_readiness_score,
            "quality_flags": list(self.metrics.quality_flags),
            "reject_reason": self.metrics.reject_reason,
            "warning_reason": self.metrics.warning_reason,
            "metrics": self.metrics.to_dict(),
        }


@dataclass(frozen=True)
class QualitySuiteResult:
    results: list
    rejected: list
    debug_images: dict

    def to_dict(self):
        return {
            "results": [r.to_dict() for r in self.results],
            "rejected": self.rejected,
        }


def evaluate_crop_quality(crop, crop_index=1):
    """Evaluate one Stage 4 crop with benchmark-only heuristic metrics."""
    if crop is None or getattr(crop, "size", 0) == 0:
        metrics = _empty_fail_metrics(["UNEXPECTED_SIZE"], "empty_crop")
        return CropQualityResult(crop_index=crop_index, metrics=metrics, overlay=None)

    img = _ensure_bgr(crop)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    crop_area = float(max(1, h * w))
    edges = cv2.Canny(gray, 50, 150)
    foreground_bbox = _foreground_bbox(gray, edges)
    margins = _margin_ratios(foreground_bbox, w, h)

    brightness_mean = float(np.mean(gray))
    brightness_std = float(np.std(gray))
    p2, p98 = np.percentile(gray, (2, 98))
    histogram_spread = float(p98 - p2)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    tenengrad = _tenengrad(gray)
    edge_density = float(np.count_nonzero(edges)) / crop_area
    texture_density = _texture_density(gray)
    internal_detail = _internal_detail_score(gray, edges)

    border_visible = _border_visible_score(edges)
    border_continuity = _border_continuity_score(edges)
    corner_visibility = _corner_visibility_score(edges)
    missing_border = _clamp01(1.0 - border_continuity)
    proximity = min(margins.values()) if margins else 0.0

    card_fill_ratio = _card_fill_ratio(foreground_bbox, crop_area)
    card_fill_score = _score_target_range(card_fill_ratio, low=0.70, high=0.98, yellow_low=0.55, yellow_high=1.0)
    background_margin_score = _clamp01(1.0 - max(margins.values()) * 3.0)
    top_reflection = _top_reflection_score(gray, foreground_bbox)

    overexposed_ratio = float(np.count_nonzero(gray > 245)) / crop_area
    underexposed_ratio = float(np.count_nonzero(gray < 10)) / crop_area

    aspect_ratio = float(h) / float(max(1, w))
    aspect_ratio_error = abs(aspect_ratio - EXPECTED_ASPECT_RATIO) / EXPECTED_ASPECT_RATIO
    aspect_ratio_score = _clamp01(1.0 - aspect_ratio_error * 3.0)
    crop_size_score = _crop_size_score(w, h)
    blur_score = _clamp01(laplacian_var / 500.0)
    tenengrad_score = _clamp01(tenengrad / 80.0)
    brightness_score = _score_target_range(brightness_mean, low=45.0, high=220.0, yellow_low=25.0, yellow_high=240.0)
    contrast_stddev_score = _clamp01(brightness_std / 55.0)
    histogram_spread_score = _clamp01(histogram_spread / 190.0)
    dynamic_range_score = histogram_spread_score

    # Fixed-aspect Stage 4 crops often place the true card edge near the output
    # boundary by design. Treat proximity as a warning signal, but let visible,
    # continuous borders prevent a hard edge-cut classification.
    proximity_score = _clamp01(proximity * 20.0)
    edge_cut_risk_score = _weighted_average([
        (border_visible, 0.35),
        (border_continuity, 0.35),
        (corner_visibility, 0.20),
        (proximity_score, 0.10),
    ])
    edge_cut_risk = edge_cut_risk_score < 0.28

    flags = []
    if edge_cut_risk:
        flags.append("EDGE_CUT_RISK")
    if background_margin_score < 0.45:
        flags.append("TOO_MUCH_BACKGROUND")
    if margins["top"] > 0.16:
        flags.append("TOP_MARGIN_RISK")
    if top_reflection > 0.20:
        flags.append("TOP_REFLECTION_RISK")
    if contrast_stddev_score < 0.22:
        flags.append("LOW_CONTRAST")
    if brightness_mean < 25:
        flags.append("TOO_DARK")
    if brightness_mean > 240 or overexposed_ratio > 0.35:
        flags.append("TOO_BRIGHT")
    if blur_score < 0.12 and tenengrad_score < 0.12:
        flags.append("BLURRY")
    if edge_density < 0.006 and texture_density < 0.05:
        flags.append("LOW_DETAIL")
    if aspect_ratio_score < 0.75:
        flags.append("BAD_ASPECT")
    if crop_size_score < 0.75:
        flags.append("UNEXPECTED_SIZE")

    crop_completeness_score = _weighted_average([
        (edge_cut_risk_score, 0.25),
        (border_visible, 0.20),
        (border_continuity, 0.15),
        (corner_visibility, 0.10),
        (card_fill_score, 0.15),
        (aspect_ratio_score, 0.15),
    ])
    crop_quality_score = _weighted_average([
        (crop_completeness_score, 0.35),
        (background_margin_score, 0.15),
        (brightness_score, 0.10),
        (contrast_stddev_score, 0.10),
        (blur_score, 0.10),
        (edge_density, 0.10),
        (crop_size_score, 0.10),
    ])
    readiness_score = _weighted_average([
        (blur_score, 0.20),
        (tenengrad_score, 0.20),
        (contrast_stddev_score, 0.18),
        (brightness_score, 0.12),
        (histogram_spread_score, 0.10),
        (texture_density, 0.10),
        (internal_detail, 0.10),
    ])

    # Stage 5 is diagnostic: benchmark-only YELLOW/FAIL scores must explain
    # which quality dimension lowered the result, even when no hard reject flag
    # was triggered.
    def add_flag(flag):
        if flag not in flags:
            flags.append(flag)

    if crop_quality_score < 0.68:
        add_flag("LOW_QUALITY_SCORE")
    if readiness_score < 0.50:
        add_flag("LOW_READINESS")
    if blur_score < 0.18 or tenengrad_score < 0.18:
        add_flag("LOW_SHARPNESS")
    if contrast_stddev_score < 0.35:
        add_flag("LOW_CONTRAST")
    if texture_density < 0.12 or internal_detail < 0.12:
        add_flag("LOW_DETAIL")
    if brightness_score < 0.50:
        add_flag("LOW_BRIGHTNESS_SCORE")
    if histogram_spread_score < 0.35:
        add_flag("LOW_HISTOGRAM_SPREAD")

    hard_fail_flags = {"EDGE_CUT_RISK", "BAD_ASPECT", "UNEXPECTED_SIZE"}
    if any(flag in hard_fail_flags for flag in flags) and crop_quality_score < 0.35:
        status = "FAIL"
    elif crop_quality_score < 0.40 or readiness_score < 0.30:
        status = "FAIL"
    elif flags or crop_quality_score < 0.68 or readiness_score < 0.50:
        status = "YELLOW"
    else:
        status = "PASS"

    if status != "PASS" and not flags:
        add_flag("LOW_READINESS" if readiness_score < 0.50 else "LOW_QUALITY_SCORE")

    reject_reason = flags[0] if status == "FAIL" and flags else None
    warning_reason = flags[0] if status == "YELLOW" and flags else None

    metrics = CropQualityMetrics(
        crop_quality_status=status,
        crop_quality_score=round(crop_quality_score, 6),
        identification_readiness_score=round(readiness_score, 6),
        edge_cut_risk=edge_cut_risk,
        edge_cut_risk_score=round(edge_cut_risk_score, 6),
        border_visible_score=round(border_visible, 6),
        border_continuity_score=round(border_continuity, 6),
        missing_border_score=round(missing_border, 6),
        corner_visibility_score=round(corner_visibility, 6),
        card_edge_proximity_to_crop_edge=round(proximity, 6),
        card_fill_ratio=round(card_fill_ratio, 6),
        card_fill_ratio_score=round(card_fill_score, 6),
        background_margin_score=round(background_margin_score, 6),
        top_margin_ratio=round(margins["top"], 6),
        bottom_margin_ratio=round(margins["bottom"], 6),
        left_margin_ratio=round(margins["left"], 6),
        right_margin_ratio=round(margins["right"], 6),
        overexposed_pixel_ratio=round(overexposed_ratio, 6),
        underexposed_pixel_ratio=round(underexposed_ratio, 6),
        top_reflection_score=round(top_reflection, 6),
        brightness_mean=round(brightness_mean, 6),
        brightness_std=round(brightness_std, 6),
        brightness_mean_score=round(brightness_score, 6),
        contrast_score=round(contrast_stddev_score, 6),
        histogram_spread_score=round(histogram_spread_score, 6),
        dynamic_range_score=round(dynamic_range_score, 6),
        variance_of_laplacian=round(laplacian_var, 6),
        variance_of_laplacian_blur_score=round(blur_score, 6),
        tenengrad_score=round(tenengrad, 6),
        tenengrad_sharpness_score=round(tenengrad_score, 6),
        edge_density_score=round(edge_density, 6),
        texture_density_score=round(texture_density, 6),
        internal_detail_score=round(internal_detail, 6),
        aspect_ratio_error=round(aspect_ratio_error, 6),
        aspect_ratio_error_score=round(aspect_ratio_score, 6),
        crop_size_score=round(crop_size_score, 6),
        quality_flags=flags,
        reject_reason=reject_reason,
        warning_reason=warning_reason,
    )
    overlay = build_quality_overlay(img, crop_index, metrics)
    return CropQualityResult(crop_index=crop_index, metrics=metrics, overlay=overlay)


def evaluate_crop_quality_suite(crops):
    results = []
    rejected = []
    for idx, crop in enumerate(crops, start=1):
        try:
            img = crop.normalized_crop if hasattr(crop, "normalized_crop") else crop
            results.append(evaluate_crop_quality(img, crop_index=idx))
        except Exception as exc:
            rejected.append({"crop_index": idx, "reject_reason": str(exc)})
    return QualitySuiteResult(results=results, rejected=rejected, debug_images={})


def build_quality_overlay(crop, crop_index, metrics):
    img = _ensure_bgr(crop)
    h, w = img.shape[:2]
    panel_h = 140
    overlay = np.zeros((h + panel_h, max(w, 520), 3), dtype=np.uint8)
    overlay[:h, :w] = img
    overlay[h:, :] = (28, 28, 28)
    color = (60, 220, 80) if metrics.crop_quality_status == "PASS" else (0, 210, 255)
    if metrics.crop_quality_status == "FAIL":
        color = (0, 80, 255)
    lines = [
        f"crop_{crop_index:02d} status: {metrics.crop_quality_status}",
        f"quality={metrics.crop_quality_score:.3f} readiness={metrics.identification_readiness_score:.3f}",
        f"flags={','.join(metrics.quality_flags) if metrics.quality_flags else 'none'}",
        f"top_margin={metrics.top_margin_ratio:.3f} edge_cut={metrics.edge_cut_risk}",
        f"blur={metrics.variance_of_laplacian_blur_score:.3f} contrast={metrics.contrast_score:.3f}",
    ]
    y = h + 25
    for idx, line in enumerate(lines):
        cv2.putText(overlay, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color if idx == 0 else (210, 210, 210), 1, cv2.LINE_AA)
        y += 24
    return overlay


def build_quality_debug_sheet(results, pair_name, expected_crop_count, crop_count, verdict):
    if not results:
        return build_no_crop_quality_debug_sheet(pair_name, expected_crop_count, crop_count, verdict)
    overlays = [r.overlay for r in results if r.overlay is not None]
    if not overlays:
        return build_no_crop_quality_debug_sheet(pair_name, expected_crop_count, crop_count, verdict)
    max_h = max(img.shape[0] for img in overlays)
    total_w = sum(img.shape[1] for img in overlays) + 8 * max(0, len(overlays) - 1)
    sheet = np.zeros((max_h, total_w, 3), dtype=np.uint8)
    x = 0
    for img in overlays:
        h, w = img.shape[:2]
        sheet[:h, x:x + w] = img
        x += w + 8
    return sheet


def build_no_crop_quality_debug_sheet(pair_name, expected_crop_count, crop_count, verdict, width=900, height=300):
    sheet = np.zeros((height, width, 3), dtype=np.uint8)
    sheet[:, :] = (30, 30, 30)
    lines = [
        "NO CROPS",
        f"pair: {pair_name}",
        f"expected_crop_count: {expected_crop_count}",
        f"crop_count: {crop_count}",
        f"verdict: {verdict}",
    ]
    y = 50
    for idx, line in enumerate(lines):
        scale = 1.2 if idx == 0 else 0.7
        thickness = 2 if idx == 0 else 1
        color = (0, 200, 255) if idx == 0 else (180, 180, 180)
        cv2.putText(sheet, line, (30, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)
        y += 50
    return sheet


def _empty_fail_metrics(flags, reject_reason):
    return CropQualityMetrics(
        crop_quality_status="FAIL",
        crop_quality_score=0.0,
        identification_readiness_score=0.0,
        edge_cut_risk=True,
        edge_cut_risk_score=0.0,
        border_visible_score=0.0,
        border_continuity_score=0.0,
        missing_border_score=1.0,
        corner_visibility_score=0.0,
        card_edge_proximity_to_crop_edge=0.0,
        card_fill_ratio=0.0,
        card_fill_ratio_score=0.0,
        background_margin_score=0.0,
        top_margin_ratio=0.0,
        bottom_margin_ratio=0.0,
        left_margin_ratio=0.0,
        right_margin_ratio=0.0,
        overexposed_pixel_ratio=0.0,
        underexposed_pixel_ratio=0.0,
        top_reflection_score=0.0,
        brightness_mean=0.0,
        brightness_std=0.0,
        brightness_mean_score=0.0,
        contrast_score=0.0,
        histogram_spread_score=0.0,
        dynamic_range_score=0.0,
        variance_of_laplacian=0.0,
        variance_of_laplacian_blur_score=0.0,
        tenengrad_score=0.0,
        tenengrad_sharpness_score=0.0,
        edge_density_score=0.0,
        texture_density_score=0.0,
        internal_detail_score=0.0,
        aspect_ratio_error=1.0,
        aspect_ratio_error_score=0.0,
        crop_size_score=0.0,
        quality_flags=flags,
        reject_reason=reject_reason,
        warning_reason=None,
    )


def _ensure_bgr(img):
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img.copy()


def _foreground_bbox(gray, edges):
    h, w = gray.shape[:2]
    crop_area = float(max(1, h * w))

    mask = np.zeros_like(gray, dtype=np.uint8)
    mask[edges > 0] = 255

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = cv2.magnitude(gx, gy)
    nonzero_grad = grad[grad > 0]
    if nonzero_grad.size:
        grad_thr = max(12.0, float(np.percentile(nonzero_grad, 70)))
        mask[grad > grad_thr] = 255

    short_side = max(1, min(h, w))
    close_size = max(5, int(short_side * 0.025))
    if close_size % 2 == 0:
        close_size += 1
    close_kernel = np.ones((close_size, close_size), dtype=np.uint8)
    dilate_kernel = np.ones((max(3, close_size // 2), max(3, close_size // 2)), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)
    mask = cv2.dilate(mask, dilate_kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    min_bbox_area = crop_area * 0.03
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        bbox_area = float(bw * bh)
        if bbox_area < min_bbox_area:
            continue
        fill_ratio = float(cv2.contourArea(contour)) / max(1.0, bbox_area)
        edge_pixels = int(np.count_nonzero(edges[y:y + bh, x:x + bw]))
        edge_support = float(edge_pixels) / max(1.0, bbox_area)
        covers_nearly_all = bbox_area > crop_area * 0.96
        if covers_nearly_all and edge_support < 0.01:
            continue
        score = bbox_area * (1.0 + edge_support + min(fill_ratio, 1.0))
        candidates.append((score, x, y, bw, bh))

    if not candidates:
        return (0, 0, w, h)

    _, x, y, bw, bh = max(candidates, key=lambda item: item[0])
    return (int(x), int(y), max(1, int(bw)), max(1, int(bh)))


def _margin_ratios(bbox, width, height):
    x, y, w, h = bbox
    return {
        "top": _clamp01(float(y) / float(max(1, height))),
        "bottom": _clamp01(float(max(0, height - (y + h))) / float(max(1, height))),
        "left": _clamp01(float(x) / float(max(1, width))),
        "right": _clamp01(float(max(0, width - (x + w))) / float(max(1, width))),
    }


def _card_fill_ratio(bbox, crop_area):
    _, _, w, h = bbox
    return _clamp01(float(w * h) / float(max(1.0, crop_area)))


def _border_visible_score(edges):
    h, w = edges.shape[:2]
    band = max(2, min(20, int(min(h, w) * 0.05)))
    sides = [edges[:band, :], edges[-band:, :], edges[:, :band], edges[:, -band:]]
    densities = [float(np.count_nonzero(side)) / float(max(1, side.size)) for side in sides]
    return _clamp01(float(np.mean(densities)) * 12.0)


def _border_continuity_score(edges):
    h, w = edges.shape[:2]
    band = max(2, min(20, int(min(h, w) * 0.05)))
    side_masks = [
        np.any(edges[:band, :] > 0, axis=0),
        np.any(edges[-band:, :] > 0, axis=0),
        np.any(edges[:, :band] > 0, axis=1),
        np.any(edges[:, -band:] > 0, axis=1),
    ]
    coverage = [float(np.count_nonzero(mask)) / float(max(1, mask.size)) for mask in side_masks]
    return _clamp01(float(np.mean(coverage)))


def _corner_visibility_score(edges):
    h, w = edges.shape[:2]
    patch = max(8, int(min(h, w) * 0.12))
    corners = [
        edges[:patch, :patch],
        edges[:patch, -patch:],
        edges[-patch:, :patch],
        edges[-patch:, -patch:],
    ]
    scores = [1.0 if np.count_nonzero(c) / float(max(1, c.size)) > 0.01 else 0.0 for c in corners]
    return float(np.mean(scores))


def _top_reflection_score(gray, bbox):
    h, w = gray.shape[:2]
    top_band_h = max(1, int(h * 0.20))
    top_band = gray[:top_band_h, :]
    bright = float(np.count_nonzero(top_band > 245)) / float(max(1, top_band.size))
    x, y, bw, bh = bbox
    top_margin_bonus = _clamp01(float(y) / float(max(1, h)) * 2.0)
    return _clamp01(bright * 4.0 + top_margin_bonus * 0.25)


def _tenengrad(gray):
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return float(np.sqrt(gx * gx + gy * gy).mean())


def _texture_density(gray):
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    diff = cv2.absdiff(gray, blurred)
    return _clamp01(float(np.mean(diff)) / 30.0)


def _internal_detail_score(gray, edges):
    h, w = gray.shape[:2]
    y1, y2 = int(h * 0.15), int(h * 0.85)
    x1, x2 = int(w * 0.15), int(w * 0.85)
    inner = edges[y1:y2, x1:x2]
    if inner.size == 0:
        return 0.0
    return _clamp01(float(np.count_nonzero(inner)) / float(inner.size) * 8.0)


def _crop_size_score(width, height):
    width_ratio = min(width, EXPECTED_WIDTH) / float(EXPECTED_WIDTH)
    height_ratio = min(height, EXPECTED_HEIGHT) / float(EXPECTED_HEIGHT)
    return _clamp01(min(width_ratio, height_ratio))


def _score_target_range(value, low, high, yellow_low, yellow_high):
    if low <= value <= high:
        return 1.0
    if yellow_low <= value <= yellow_high:
        if value < low:
            return _clamp01((value - yellow_low) / float(max(1e-6, low - yellow_low)) * 0.5 + 0.5)
        return _clamp01((yellow_high - value) / float(max(1e-6, yellow_high - high)) * 0.5 + 0.5)
    return 0.0


def _weighted_average(items):
    total_weight = sum(weight for _, weight in items)
    if total_weight <= 0:
        return 0.0
    return _clamp01(sum(_clamp01(value) * weight for value, weight in items) / total_weight)


def _clamp01(value):
    return max(0.0, min(1.0, float(value)))
