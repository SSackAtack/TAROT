from dataclasses import asdict, dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class RegionCandidate:
    bbox: list
    area: int
    mask_area: int
    bbox_area: int
    bbox_area_ratio: float
    mask_area_ratio: float
    foreground_fill_ratio: float
    aspect_ratio: float
    rectangularity: float
    solidity: float
    extent: float
    edge_density: float
    oversized_bbox_flag: bool
    split_card_flag: bool
    merge_card_flag: bool
    reject_reason: str | None = None

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class RegionMethodResult:
    candidates: list
    rejected_candidates: list
    debug_masks: dict


def available_region_methods():
    return [
        "baseline_components",
        "morph_close_components",
        "dilate_merge_components",
        "contour_external",
        "largest_contour_inside_region",
        "padding_tighten_by_mask",
        "projection_tightening",
    ]


def run_region_method(name, stage1_mask, current_frame, **kwargs):
    mask = _ensure_binary_mask(stage1_mask)
    if name == "baseline_components":
        return _components_method(mask, current_frame, **kwargs)
    if name == "morph_close_components":
        kernel_size = int(kwargs.pop("close_kernel_size", 7))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((kernel_size, kernel_size), dtype=np.uint8))
        result = _components_method(closed, current_frame, **kwargs)
        return RegionMethodResult(result.candidates, result.rejected_candidates, {"candidate_mask": closed})
    if name == "dilate_merge_components":
        kernel_size = int(kwargs.pop("dilate_kernel_size", 3))
        merge_padding_px = int(kwargs.pop("merge_padding_px", 12))
        dilated = cv2.dilate(mask, np.ones((kernel_size, kernel_size), dtype=np.uint8), iterations=1)
        result = _components_method(dilated, current_frame, merge_padding_px=merge_padding_px, mark_merged=True, **kwargs)
        return RegionMethodResult(result.candidates, result.rejected_candidates, {"candidate_mask": dilated})
    if name == "contour_external":
        return _contour_external_method(mask, current_frame, **kwargs)
    if name == "largest_contour_inside_region":
        return _largest_contour_inside_region(mask, current_frame, **kwargs)
    if name == "padding_tighten_by_mask":
        return _padding_tighten_by_mask(mask, current_frame, **kwargs)
    if name == "projection_tightening":
        return _projection_tightening(mask, current_frame, **kwargs)
    raise ValueError(f"Unknown Stage 2 region method: {name}")


def _components_method(
    mask,
    current_frame,
    min_area_ratio=0.002,
    max_area_ratio=0.6,
    merge_padding_px=0,
    mark_merged=False,
):
    frame_area = float(mask.shape[0] * mask.shape[1])
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    regions = []
    rejected = []
    for label in range(1, count):
        x, y, width, height, area = stats[label]
        area_ratio = float(area) / frame_area
        region = {"bbox": [int(x), int(y), int(width), int(height)], "area": int(area)}
        if area_ratio < min_area_ratio:
            rejected.append({**region, "reject_reason": "too_small"})
            continue
        if area_ratio > max_area_ratio:
            rejected.append({**region, "reject_reason": "too_large"})
            continue
        regions.append(region)
    if merge_padding_px > 0:
        regions, merged_any = _merge_regions(regions, frame_area, merge_padding_px)
    else:
        merged_any = False
    candidates = [
        _build_candidate(region["bbox"], mask, current_frame, merge_card_flag=bool(mark_merged and merged_any))
        for region in regions
    ]
    return RegionMethodResult(candidates, rejected, {"candidate_mask": mask})


def _contour_external_method(mask, current_frame, min_area_ratio=0.002, max_area_ratio=0.6):
    frame_area = float(mask.shape[0] * mask.shape[1])
    contours = _external_contours(mask)
    candidates = []
    rejected = []
    for contour in contours:
        area = int(cv2.contourArea(contour))
        area_ratio = float(area) / frame_area
        x, y, width, height = cv2.boundingRect(contour)
        region = {"bbox": [int(x), int(y), int(width), int(height)], "area": area}
        if area_ratio < min_area_ratio:
            rejected.append({**region, "reject_reason": "too_small"})
            continue
        if area_ratio > max_area_ratio:
            rejected.append({**region, "reject_reason": "too_large"})
            continue
        candidates.append(_build_candidate(region["bbox"], mask, current_frame))
    return RegionMethodResult(candidates, rejected, {"candidate_mask": mask})


def _largest_contour_inside_region(mask, current_frame, **kwargs):
    baseline = _components_method(mask, current_frame, **kwargs)
    candidates = []
    for candidate in baseline.candidates:
        x, y, width, height = candidate.bbox
        roi = mask[y : y + height, x : x + width]
        contours = _external_contours(roi)
        if not contours:
            candidates.append(candidate)
            continue
        contour = max(contours, key=cv2.contourArea)
        cx, cy, cw, ch = cv2.boundingRect(contour)
        candidates.append(_build_candidate([x + int(cx), y + int(cy), int(cw), int(ch)], mask, current_frame))
    return RegionMethodResult(candidates, baseline.rejected_candidates, {"candidate_mask": mask})


def _padding_tighten_by_mask(mask, current_frame, padding_px=8, **kwargs):
    baseline = _components_method(mask, current_frame, **kwargs)
    candidates = []
    for candidate in baseline.candidates:
        x, y, width, height = _pad_bbox(candidate.bbox, mask.shape, padding_px)
        local = mask[y : y + height, x : x + width]
        tight = _bbox_from_foreground(local)
        if tight is None:
            continue
        tx, ty, tw, th = tight
        candidates.append(_build_candidate([x + tx, y + ty, tw, th], mask, current_frame))
    return RegionMethodResult(candidates, baseline.rejected_candidates, {"candidate_mask": mask})


def _projection_tightening(mask, current_frame, projection_threshold=1, padding_px=2, **kwargs):
    baseline = _components_method(mask, current_frame, **kwargs)
    candidates = []
    for candidate in baseline.candidates:
        x, y, width, height = candidate.bbox
        local = mask[y : y + height, x : x + width]
        rows = np.where(np.count_nonzero(local, axis=1) >= projection_threshold)[0]
        cols = np.where(np.count_nonzero(local, axis=0) >= projection_threshold)[0]
        if rows.size == 0 or cols.size == 0:
            continue
        x1 = max(0, int(cols[0]) - padding_px)
        x2 = min(width - 1, int(cols[-1]) + padding_px)
        y1 = max(0, int(rows[0]) - padding_px)
        y2 = min(height - 1, int(rows[-1]) + padding_px)
        candidates.append(_build_candidate([x + x1, y + y1, x2 - x1 + 1, y2 - y1 + 1], mask, current_frame))
    return RegionMethodResult(candidates, baseline.rejected_candidates, {"candidate_mask": mask})


def _build_candidate(bbox, mask, current_frame, merge_card_flag=False):
    x, y, width, height = [int(value) for value in bbox]
    frame_area = float(mask.shape[0] * mask.shape[1])
    bbox_area = max(1, width * height)
    local_mask = mask[y : y + height, x : x + width]
    mask_area = int(np.count_nonzero(local_mask))
    contours = _external_contours(local_mask)
    contour_area = float(max((cv2.contourArea(contour) for contour in contours), default=mask_area))
    hull_area = contour_area
    if contours:
        hull = cv2.convexHull(max(contours, key=cv2.contourArea))
        hull_area = max(1.0, float(cv2.contourArea(hull)))
    fill = float(mask_area) / float(bbox_area)
    aspect_ratio = float(width) / float(max(1, height))
    rectangularity = contour_area / float(bbox_area)
    solidity = contour_area / hull_area if hull_area else 0.0
    extent = rectangularity
    edge_density = _edge_density(current_frame, bbox)
    oversized = bool(fill < 0.15 or float(bbox_area) / frame_area > 0.35)
    split = bool(fill < 0.35 and not oversized)
    return RegionCandidate(
        bbox=[x, y, width, height],
        area=int(contour_area),
        mask_area=mask_area,
        bbox_area=bbox_area,
        bbox_area_ratio=round(float(bbox_area) / frame_area, 6),
        mask_area_ratio=round(float(mask_area) / frame_area, 6),
        foreground_fill_ratio=round(fill, 6),
        aspect_ratio=round(aspect_ratio, 6),
        rectangularity=round(rectangularity, 6),
        solidity=round(solidity, 6),
        extent=round(extent, 6),
        edge_density=round(edge_density, 6),
        oversized_bbox_flag=oversized,
        split_card_flag=split,
        merge_card_flag=merge_card_flag,
    )


def _edge_density(frame, bbox):
    x, y, width, height = bbox
    roi = frame[y : y + height, x : x + width]
    if roi.size == 0:
        return 0.0
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
    edges = cv2.Canny(gray, 50, 150)
    return float(np.count_nonzero(edges)) / float(max(1, width * height))


def _merge_regions(regions, frame_area, merge_padding_px):
    merged = []
    merged_any = False
    for region in regions:
        current = dict(region)
        did_merge = True
        while did_merge:
            did_merge = False
            remaining = []
            for existing in merged:
                if _boxes_overlap_with_padding(current["bbox"], existing["bbox"], merge_padding_px):
                    current = _merge_two_regions(current, existing, frame_area)
                    did_merge = True
                    merged_any = True
                else:
                    remaining.append(existing)
            merged = remaining
        merged.append(current)
    return merged, merged_any


def _boxes_overlap_with_padding(first, second, padding):
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return not (
        ax + aw + padding < bx
        or bx + bw + padding < ax
        or ay + ah + padding < by
        or by + bh + padding < ay
    )


def _merge_two_regions(first, second, frame_area):
    ax, ay, aw, ah = first["bbox"]
    bx, by, bw, bh = second["bbox"]
    x1 = min(ax, bx)
    y1 = min(ay, by)
    x2 = max(ax + aw, bx + bw)
    y2 = max(ay + ah, by + bh)
    return {"bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)], "area": int(first["area"]) + int(second["area"])}


def _pad_bbox(bbox, shape, padding):
    x, y, width, height = bbox
    max_y, max_x = shape[:2]
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(max_x, x + width + padding)
    y2 = min(max_y, y + height + padding)
    return [x1, y1, x2 - x1, y2 - y1]


def _bbox_from_foreground(mask):
    ys, xs = np.where(mask > 0)
    if xs.size == 0 or ys.size == 0:
        return None
    x1 = int(xs.min())
    x2 = int(xs.max())
    y1 = int(ys.min())
    y2 = int(ys.max())
    return [x1, y1, x2 - x1 + 1, y2 - y1 + 1]


def _external_contours(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def _ensure_binary_mask(mask):
    if mask is None or mask.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    _, binary = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    return binary
