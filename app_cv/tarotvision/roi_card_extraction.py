from dataclasses import dataclass

import cv2
import numpy as np


EXPECTED_CARD_ASPECT_RATIO = 1.65


@dataclass(frozen=True)
class RoiCardExtractionResult:
    quads: list
    debug: dict


def extract_card_quads_from_roi(roi_frame, roi_mask):
    """Extract at most one card quad from one state-first ROI diff mask."""
    frame_shape = getattr(roi_frame, "shape", None)
    debug = _base_debug(frame_shape, getattr(roi_mask, "shape", None))

    if roi_frame is None or getattr(roi_frame, "size", 0) == 0:
        debug["reject_reason"] = "empty_roi_frame"
        return RoiCardExtractionResult([], debug)

    mask = _prepare_mask(roi_mask, roi_frame.shape[:2])
    debug["mask_shape"] = [int(mask.shape[0]), int(mask.shape[1])] if mask.size else [0, 0]
    debug["mask_nonzero_ratio"] = _ratio(np.count_nonzero(mask), mask.size)
    if mask.size == 0 or int(np.count_nonzero(mask)) == 0:
        debug["reject_reason"] = "empty_roi_mask"
        return RoiCardExtractionResult([], debug)

    stage2_candidates, rejected_candidates = _stage2_contour_external(mask, roi_frame)
    debug["contours_total"] = len(stage2_candidates) + len(rejected_candidates)
    debug["stage2_candidate_count"] = len(stage2_candidates)
    debug["stage2_rejected_count"] = len(rejected_candidates)
    if rejected_candidates:
        debug["stage2_rejected"] = rejected_candidates
    if not stage2_candidates:
        debug["reject_reason"] = "no_stage2_candidate"
        return RoiCardExtractionResult([], debug)

    candidate = max(stage2_candidates, key=lambda item: item["score"])
    debug["stage2_bbox"] = [int(value) for value in candidate["bbox"]]
    debug["stage2_foreground_fill_ratio"] = round(float(candidate["foreground_fill_ratio"]), 6)

    quad, geometry = _stage3_hybrid_edge_plus_contour(roi_frame, mask, candidate["bbox"])
    if quad is None:
        debug["reject_reason"] = "no_stage3_geometry"
        return RoiCardExtractionResult([], debug)

    debug.update(_quality_debug(roi_frame, mask, quad, geometry))
    debug["quads_final"] = 1
    return RoiCardExtractionResult([quad], debug)


def _base_debug(frame_shape, mask_shape):
    roi_shape = list(frame_shape[:2]) if frame_shape is not None and len(frame_shape) >= 2 else None
    return {
        "source": "offline_roi_extractor",
        "stage1_method": "gray_absdiff_gaussian",
        "stage2_method": "contour_external",
        "stage3_method": "hybrid_edge_plus_contour",
        "stage4_crop_method": "quad_warp_perspective_fixed_aspect",
        "stage4_normalization": "resize_only_normalization",
        "stage5_quality_method": "quality_metric_suite_v1",
        "roi_shape": roi_shape,
        "mask_shape": list(mask_shape[:2]) if mask_shape is not None and len(mask_shape) >= 2 else None,
        "contours_total": 0,
        "stage2_candidate_count": 0,
        "stage2_rejected_count": 0,
        "quads_final": 0,
        "reject_reason": None,
    }


def _prepare_mask(mask, target_shape):
    if mask is None:
        return np.zeros(target_shape, dtype=np.uint8)

    arr = np.asarray(mask)
    if arr.size == 0 or arr.ndim < 2:
        return np.zeros(target_shape, dtype=np.uint8)
    if arr.ndim == 3:
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)

    _, binary = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY)
    target_h, target_w = [int(value) for value in target_shape]
    if binary.shape[:2] != (target_h, target_w):
        binary = cv2.resize(binary, (target_w, target_h), interpolation=cv2.INTER_NEAREST)

    kernel = np.ones((3, 3), dtype=np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return binary


def _stage2_contour_external(mask, roi_frame):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    frame_area = float(max(1, mask.shape[0] * mask.shape[1]))
    min_area = max(24.0, frame_area * 0.002)
    max_area = frame_area * 0.92
    candidates = []
    rejected = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        x, y, width, height = cv2.boundingRect(contour)
        bbox_area = float(max(1, width * height))
        summary = {
            "bbox": [int(x), int(y), int(width), int(height)],
            "area": int(round(area)),
        }
        if area < min_area:
            rejected.append({**summary, "reject_reason": "too_small"})
            continue
        if area > max_area:
            rejected.append({**summary, "reject_reason": "too_large"})
            continue

        local_mask = mask[y:y + height, x:x + width]
        foreground_fill = _ratio(np.count_nonzero(local_mask), bbox_area)
        edge_density = _edge_density(roi_frame, (x, y, width, height))
        candidates.append({
            **summary,
            "foreground_fill_ratio": foreground_fill,
            "edge_density": edge_density,
            "score": bbox_area * (0.75 + min(1.0, foreground_fill) + min(1.0, edge_density * 8.0)),
        })
    return candidates, rejected


def _stage3_hybrid_edge_plus_contour(roi_frame, mask, bbox):
    x, y, width, height = [int(value) for value in bbox]
    local_frame = roi_frame[y:y + height, x:x + width]
    local_mask = mask[y:y + height, x:x + width]
    if local_frame.size == 0 or local_mask.size == 0:
        return None, None

    edges = _edge_mask(local_frame)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), dtype=np.uint8))
    contour_source = cv2.bitwise_or(local_mask, edges)
    contours, _ = cv2.findContours(contour_source, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None

    contour = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(contour)
    points = cv2.boxPoints(rect).astype(np.float32)
    points[:, 0] += float(x)
    points[:, 1] += float(y)
    ordered = _order_quad_points(points)
    quad = ordered.reshape(4, 1, 2).astype(np.float32)

    rw, rh = rect[1]
    geometry = {
        "bbox": [int(value) for value in cv2.boundingRect(points.astype(np.int32))],
        "quad_area": float(abs(cv2.contourArea(ordered))),
        "rect_width": float(rw),
        "rect_height": float(rh),
        "contour_area": float(cv2.contourArea(contour)),
        "angle_degrees": float(rect[2]),
    }
    return quad, geometry


def _quality_debug(roi_frame, mask, quad, geometry):
    roi_area = float(max(1, roi_frame.shape[0] * roi_frame.shape[1]))
    bbox = geometry["bbox"]
    x, y, width, height = bbox
    bbox_area = float(max(1, width * height))
    local_mask = mask[y:y + height, x:x + width]
    foreground_fill = _ratio(np.count_nonzero(local_mask), bbox_area)
    aspect_ratio = _quad_aspect_ratio(quad)
    aspect_error = abs(aspect_ratio - EXPECTED_CARD_ASPECT_RATIO) / EXPECTED_CARD_ASPECT_RATIO
    aspect_score = _clamp01(1.0 - aspect_error * 2.0)
    quad_area_ratio = float(geometry["quad_area"]) / roi_area
    area_score = _score_target_range(quad_area_ratio, low=0.08, high=0.75, yellow_low=0.03, yellow_high=0.90)
    edge_support = _edge_density(roi_frame, bbox)
    rectangularity = _ratio(geometry["contour_area"], bbox_area)
    geometry_confidence = _weighted_average([
        (aspect_score, 0.35),
        (foreground_fill, 0.25),
        (area_score, 0.20),
        (rectangularity, 0.10),
        (min(1.0, edge_support * 8.0), 0.10),
    ])

    hard_reject = None
    if quad_area_ratio < 0.03:
        hard_reject = "card_area_too_small"
    elif aspect_ratio < 1.05 or aspect_ratio > 2.40:
        hard_reject = "bad_aspect_ratio"
    elif foreground_fill < 0.12:
        hard_reject = "low_foreground_fill"

    if hard_reject:
        quality_status = "FAIL"
    elif geometry_confidence >= 0.68:
        quality_status = "PASS"
    elif geometry_confidence >= 0.35:
        quality_status = "YELLOW"
    else:
        quality_status = "FAIL"

    return {
        "stage3_geometry_type": "hybrid_edge_contour",
        "stage3_bbox": [int(value) for value in bbox],
        "quad_area_ratio": round(float(quad_area_ratio), 6),
        "aspect_ratio": round(float(aspect_ratio), 6),
        "aspect_ratio_error": round(float(aspect_error), 6),
        "foreground_fill_ratio": round(float(foreground_fill), 6),
        "rectangularity_score": round(float(rectangularity), 6),
        "edge_support_score": round(float(edge_support), 6),
        "geometry_confidence": round(float(geometry_confidence), 6),
        "quality_status": quality_status,
        "quality_score": round(float(geometry_confidence), 6),
        "quality_reject_reason": hard_reject,
    }


def _edge_mask(frame):
    if frame.size == 0:
        return np.zeros(frame.shape[:2], dtype=np.uint8)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    return cv2.Canny(gray, 50, 150)


def _edge_density(frame, bbox):
    x, y, width, height = [int(value) for value in bbox]
    roi = frame[y:y + height, x:x + width]
    if roi.size == 0:
        return 0.0
    edges = _edge_mask(roi)
    return _ratio(np.count_nonzero(edges), width * height)


def _order_quad_points(points):
    pts = np.array(points, dtype=np.float32).reshape(4, 2)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(4)
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = pts[np.argmin(sums)]
    ordered[1] = pts[np.argmin(diffs)]
    ordered[2] = pts[np.argmax(sums)]
    ordered[3] = pts[np.argmax(diffs)]
    return ordered


def _quad_aspect_ratio(quad):
    points = np.asarray(quad, dtype=np.float32).reshape(4, 2)
    top_width = float(np.linalg.norm(points[1] - points[0]))
    bottom_width = float(np.linalg.norm(points[2] - points[3]))
    left_height = float(np.linalg.norm(points[3] - points[0]))
    right_height = float(np.linalg.norm(points[2] - points[1]))
    width = max(top_width, bottom_width, 1.0)
    height = max(left_height, right_height, 1.0)
    short = max(1.0, min(width, height))
    long = max(width, height)
    return float(long) / float(short)


def _score_target_range(value, low, high, yellow_low, yellow_high):
    value = float(value)
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


def _ratio(numerator, denominator):
    denominator = float(denominator)
    if denominator <= 0.0:
        return 0.0
    return float(numerator) / denominator


def _clamp01(value):
    return max(0.0, min(1.0, float(value)))
