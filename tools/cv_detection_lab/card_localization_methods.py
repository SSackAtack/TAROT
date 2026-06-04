from dataclasses import asdict, dataclass

import cv2
import numpy as np


EXPECTED_CARD_ASPECT_RATIO = 1.65  # height / width


@dataclass(frozen=True)
class CardGeometryCandidate:
    bbox: list
    rotated_bbox: list | None
    quad_points: list | None
    ordered_quad_points: list | None
    source_stage2_bbox: list
    geometry_type: str
    area: int
    bbox_area_ratio: float
    quad_area_ratio: float
    aspect_ratio: float
    aspect_ratio_error: float
    rectangularity_score: float
    border_score: float
    edge_support_score: float
    corner_score: float
    angle_degrees: float | None
    angle_stability_score: float
    candidate_to_stage2_area_ratio: float
    geometry_confidence: float
    reject_reason: str | None = None

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class CardLocalizationResult:
    geometries: list
    rejected_geometries: list
    debug_images: dict


def available_localization_methods():
    return [
        "bounding_rect_tight",
        "contour_largest_inside_candidate",
        "approx_poly_dp_quad",
        "min_area_rect_candidate",
        "projection_profile_tight_bbox",
        "hybrid_contour_plus_min_area_rect",
        "hybrid_edge_plus_contour",
    ]


def run_localization_method(name, source_frame, stage1_mask, stage2_candidates, **kwargs):
    if name not in available_localization_methods():
        raise ValueError(f"Unknown Stage 3 localization method: {name}")

    mask = _ensure_binary_mask(stage1_mask)
    geometries = []
    rejected = []
    edge_debug = np.zeros(mask.shape, dtype=np.uint8)
    contour_debug = np.zeros(mask.shape, dtype=np.uint8)

    for candidate in stage2_candidates:
        stage2_bbox = _candidate_bbox(candidate)
        local = _local_views(source_frame, mask, stage2_bbox)
        if local["mask"].size == 0 or int(np.count_nonzero(local["mask"])) == 0:
            rejected.append({"source_stage2_bbox": stage2_bbox, "reject_reason": "empty_candidate_mask"})
            continue

        local_edges = _edge_mask(local["frame"])
        edge_debug[local["y"] : local["y"] + local["height"], local["x"] : local["x"] + local["width"]] = local_edges
        geometry = _run_single_method(name, local, local_edges, stage2_bbox, **kwargs)
        if geometry is None:
            rejected.append({"source_stage2_bbox": stage2_bbox, "reject_reason": "no_geometry"})
            continue
        if geometry.reject_reason:
            rejected.append(geometry.to_dict())
            continue
        geometries.append(geometry)
        _draw_geometry_on_mask(contour_debug, geometry)

    return CardLocalizationResult(
        geometries=geometries,
        rejected_geometries=rejected,
        debug_images={"edge_debug": edge_debug, "contour_debug": contour_debug},
    )


def _run_single_method(name, local, local_edges, stage2_bbox, **kwargs):
    contour_source = local["mask"]
    if name == "hybrid_edge_plus_contour":
        contour_source = cv2.morphologyEx(local_edges, cv2.MORPH_CLOSE, np.ones((5, 5), dtype=np.uint8))
    contours = _external_contours(contour_source)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)

    if name == "bounding_rect_tight":
        local_bbox = _bbox_from_foreground(local["mask"])
        return _build_axis_geometry(local_bbox, local, stage2_bbox, "bbox")
    if name == "contour_largest_inside_candidate":
        local_bbox = cv2.boundingRect(contour)
        return _build_axis_geometry(local_bbox, local, stage2_bbox, "contour_bbox", contour=contour)
    if name == "approx_poly_dp_quad":
        epsilon_ratio = float(kwargs.get("epsilon_ratio", 0.03))
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon_ratio * perimeter, True)
        if len(approx) == 4:
            points = [[int(point[0][0] + local["x"]), int(point[0][1] + local["y"])] for point in approx]
            return _build_quad_geometry(points, local, stage2_bbox, "quad")
        rect = cv2.minAreaRect(contour)
        return _build_rotated_geometry(rect, local, stage2_bbox, "quad_fallback_min_area_rect")
    if name == "min_area_rect_candidate":
        return _build_rotated_geometry(cv2.minAreaRect(contour), local, stage2_bbox, "rotated_rect")
    if name == "projection_profile_tight_bbox":
        local_bbox = _projection_bbox(local["mask"], padding_px=int(kwargs.get("padding_px", 2)))
        return _build_axis_geometry(local_bbox, local, stage2_bbox, "projection_bbox")
    if name == "hybrid_contour_plus_min_area_rect":
        return _build_rotated_geometry(cv2.minAreaRect(contour), local, stage2_bbox, "hybrid_contour_min_area_rect")
    if name == "hybrid_edge_plus_contour":
        return _build_rotated_geometry(cv2.minAreaRect(contour), local, stage2_bbox, "hybrid_edge_contour")
    return None


def _build_axis_geometry(local_bbox, local, stage2_bbox, geometry_type, contour=None):
    if local_bbox is None:
        return None
    lx, ly, width, height = [int(value) for value in local_bbox]
    bbox = [local["x"] + lx, local["y"] + ly, int(width), int(height)]
    points = _bbox_to_points(bbox)
    return _build_geometry(
        bbox=bbox,
        rotated_bbox=None,
        quad_points=None,
        ordered_quad_points=points,
        source_stage2_bbox=stage2_bbox,
        geometry_type=geometry_type,
        local=local,
        angle_degrees=None,
        contour=contour,
    )


def _build_rotated_geometry(rect, local, stage2_bbox, geometry_type):
    points = cv2.boxPoints(rect)
    global_points = [[int(round(point[0] + local["x"])), int(round(point[1] + local["y"]))] for point in points]
    ordered = order_quad_points(global_points)
    x, y, width, height = cv2.boundingRect(np.array(global_points, dtype=np.int32))
    angle = _normalize_angle(float(rect[2]))
    return _build_geometry(
        bbox=[int(x), int(y), int(width), int(height)],
        rotated_bbox=ordered,
        quad_points=global_points,
        ordered_quad_points=ordered,
        source_stage2_bbox=stage2_bbox,
        geometry_type=geometry_type,
        local=local,
        angle_degrees=angle,
    )


def _build_quad_geometry(points, local, stage2_bbox, geometry_type):
    ordered = order_quad_points(points)
    x, y, width, height = cv2.boundingRect(np.array(ordered, dtype=np.int32))
    return _build_geometry(
        bbox=[int(x), int(y), int(width), int(height)],
        rotated_bbox=None,
        quad_points=points,
        ordered_quad_points=ordered,
        source_stage2_bbox=stage2_bbox,
        geometry_type=geometry_type,
        local=local,
        angle_degrees=_quad_angle_degrees(ordered),
    )


def _build_geometry(
    bbox,
    rotated_bbox,
    quad_points,
    ordered_quad_points,
    source_stage2_bbox,
    geometry_type,
    local,
    angle_degrees,
    contour=None,
):
    frame_area = float(local["frame_shape"][0] * local["frame_shape"][1])
    bbox_area = max(1, int(bbox[2]) * int(bbox[3]))
    stage2_area = max(1, int(source_stage2_bbox[2]) * int(source_stage2_bbox[3]))
    local_contours = _external_contours(local["mask"])
    contour_area = float(cv2.contourArea(contour)) if contour is not None else float(max((cv2.contourArea(c) for c in local_contours), default=bbox_area))
    quad_area = _polygon_area(ordered_quad_points) if ordered_quad_points else float(bbox_area)
    aspect_ratio = _aspect_ratio_from_points_or_bbox(ordered_quad_points, bbox)
    aspect_error = abs(aspect_ratio - EXPECTED_CARD_ASPECT_RATIO) / EXPECTED_CARD_ASPECT_RATIO
    rectangularity = min(1.0, float(contour_area) / float(bbox_area))
    border = _border_score(local["source_frame"], bbox)
    edge_support = _edge_support_score(local["source_frame"], bbox)
    corner = _corner_score(local["source_frame"], bbox)
    angle_stability = 1.0 if angle_degrees is None else max(0.0, 1.0 - min(45.0, abs(angle_degrees)) / 45.0)
    confidence = _geometry_confidence(rectangularity, border, edge_support, corner, aspect_error, ordered_quad_points)
    reject_reason = None
    if bbox_area <= 0 or confidence <= 0:
        reject_reason = "low_geometry_confidence"
    return CardGeometryCandidate(
        bbox=[int(v) for v in bbox],
        rotated_bbox=rotated_bbox,
        quad_points=quad_points,
        ordered_quad_points=ordered_quad_points,
        source_stage2_bbox=[int(v) for v in source_stage2_bbox],
        geometry_type=geometry_type,
        area=int(contour_area),
        bbox_area_ratio=round(float(bbox_area) / frame_area, 6),
        quad_area_ratio=round(float(quad_area) / frame_area, 6),
        aspect_ratio=round(float(aspect_ratio), 6),
        aspect_ratio_error=round(float(aspect_error), 6),
        rectangularity_score=round(float(rectangularity), 6),
        border_score=round(float(border), 6),
        edge_support_score=round(float(edge_support), 6),
        corner_score=round(float(corner), 6),
        angle_degrees=None if angle_degrees is None else round(float(angle_degrees), 6),
        angle_stability_score=round(float(angle_stability), 6),
        candidate_to_stage2_area_ratio=round(float(bbox_area) / float(stage2_area), 6),
        geometry_confidence=round(float(confidence), 6),
        reject_reason=reject_reason,
    )


def order_quad_points(points):
    pts = np.array(points, dtype=np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(-1)
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = pts[np.argmin(sums)]
    ordered[2] = pts[np.argmax(sums)]
    ordered[1] = pts[np.argmin(diffs)]
    ordered[3] = pts[np.argmax(diffs)]
    return [[int(round(x)), int(round(y))] for x, y in ordered]


def _local_views(source_frame, mask, bbox):
    x, y, width, height = [int(value) for value in bbox]
    x = max(0, x)
    y = max(0, y)
    width = max(0, min(width, mask.shape[1] - x))
    height = max(0, min(height, mask.shape[0] - y))
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "mask": mask[y : y + height, x : x + width],
        "frame": source_frame[y : y + height, x : x + width],
        "source_frame": source_frame,
        "frame_shape": source_frame.shape[:2],
    }


def _candidate_bbox(candidate):
    if hasattr(candidate, "bbox"):
        return [int(value) for value in candidate.bbox]
    return [int(value) for value in candidate["bbox"]]


def _ensure_binary_mask(mask):
    if mask is None or mask.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    _, binary = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    return binary


def _edge_mask(frame):
    if frame.size == 0:
        return np.zeros(frame.shape[:2], dtype=np.uint8)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    return cv2.Canny(gray, 50, 150)


def _external_contours(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def _bbox_from_foreground(mask):
    ys, xs = np.where(mask > 0)
    if xs.size == 0 or ys.size == 0:
        return None
    x1 = int(xs.min())
    x2 = int(xs.max())
    y1 = int(ys.min())
    y2 = int(ys.max())
    return [x1, y1, x2 - x1 + 1, y2 - y1 + 1]


def _projection_bbox(mask, padding_px):
    rows = np.where(np.count_nonzero(mask, axis=1) > 0)[0]
    cols = np.where(np.count_nonzero(mask, axis=0) > 0)[0]
    if rows.size == 0 or cols.size == 0:
        return None
    x1 = max(0, int(cols[0]) - padding_px)
    x2 = min(mask.shape[1] - 1, int(cols[-1]) + padding_px)
    y1 = max(0, int(rows[0]) - padding_px)
    y2 = min(mask.shape[0] - 1, int(rows[-1]) + padding_px)
    return [x1, y1, x2 - x1 + 1, y2 - y1 + 1]


def _bbox_to_points(bbox):
    x, y, width, height = [int(v) for v in bbox]
    return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]


def _polygon_area(points):
    if not points:
        return 0.0
    return abs(float(cv2.contourArea(np.array(points, dtype=np.float32))))


def _aspect_ratio_from_points_or_bbox(points, bbox):
    if points and len(points) == 4:
        tl, tr, br, bl = [np.array(point, dtype=np.float32) for point in points]
        width = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))
        height = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))
    else:
        width = float(max(1, bbox[2]))
        height = float(max(1, bbox[3]))
    short = max(1.0, min(width, height))
    long = max(width, height)
    return float(long) / float(short)


def _border_score(frame, bbox, band_px=4):
    x, y, width, height = [int(v) for v in bbox]
    roi = frame[y : y + height, x : x + width]
    if roi.size == 0:
        return 0.0
    edges = _edge_mask(roi)
    band = max(1, min(band_px, width // 2 if width else 1, height // 2 if height else 1))
    border = np.zeros(edges.shape, dtype=np.uint8)
    border[:band, :] = 1
    border[-band:, :] = 1
    border[:, :band] = 1
    border[:, -band:] = 1
    return float(np.count_nonzero(edges * border)) / float(max(1, np.count_nonzero(border)))


def _edge_support_score(frame, bbox):
    x, y, width, height = [int(v) for v in bbox]
    roi = frame[y : y + height, x : x + width]
    if roi.size == 0:
        return 0.0
    edges = _edge_mask(roi)
    return float(np.count_nonzero(edges)) / float(max(1, width * height))


def _corner_score(frame, bbox):
    x, y, width, height = [int(v) for v in bbox]
    roi = frame[y : y + height, x : x + width]
    if roi.size == 0:
        return 0.0
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
    corners = cv2.goodFeaturesToTrack(gray, maxCorners=12, qualityLevel=0.01, minDistance=5)
    if corners is None:
        return 0.0
    return min(1.0, float(len(corners)) / 4.0)


def _geometry_confidence(rectangularity, border, edge_support, corner, aspect_error, points):
    geometry_bonus = 0.15 if points and len(points) == 4 else 0.0
    score = (
        0.30 * max(0.0, 1.0 - min(1.0, aspect_error))
        + 0.25 * rectangularity
        + 0.20 * min(1.0, border * 8.0)
        + 0.15 * min(1.0, edge_support * 8.0)
        + 0.10 * corner
        + geometry_bonus
    )
    return min(1.0, max(0.0, score))


def _quad_angle_degrees(points):
    if not points or len(points) < 2:
        return None
    tl, tr = np.array(points[0], dtype=np.float32), np.array(points[1], dtype=np.float32)
    dx, dy = tr - tl
    return _normalize_angle(float(np.degrees(np.arctan2(dy, dx))))


def _normalize_angle(angle):
    while angle > 45:
        angle -= 90
    while angle < -45:
        angle += 90
    return angle


def _draw_geometry_on_mask(mask, geometry):
    if geometry.ordered_quad_points:
        points = np.array(geometry.ordered_quad_points, dtype=np.int32)
        cv2.polylines(mask, [points], isClosed=True, color=255, thickness=2)
    else:
        x, y, width, height = geometry.bbox
        cv2.rectangle(mask, (x, y), (x + width, y + height), 255, 2)
