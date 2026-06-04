"""Stage 4 Crop / Deskew / Normalize methods for the offline CV detection lab.

This module provides crop extraction, deskew/perspective correction, and
image normalization methods.  It does NOT perform card identification.

Dependencies: OpenCV, NumPy (standard library only).
"""
from dataclasses import asdict, dataclass, field
from typing import List, Optional

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Default target size for tarot card crops
# ---------------------------------------------------------------------------
DEFAULT_TARGET_WIDTH = 300
DEFAULT_TARGET_HEIGHT = 495
EXPECTED_ASPECT_RATIO = DEFAULT_TARGET_HEIGHT / DEFAULT_TARGET_WIDTH  # 1.65


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CardCropResult:
    raw_crop: Optional[np.ndarray]
    deskewed_crop: Optional[np.ndarray]
    normalized_crop: Optional[np.ndarray]
    crop_method: str
    normalization_variant: str
    source_geometry: dict
    crop_source_frame: str
    target_width: int
    target_height: int
    crop_width: int
    crop_height: int
    crop_aspect_ratio: float
    aspect_ratio_error: float
    padding_ratio: float
    transform_valid: bool
    transform_matrix: Optional[list]
    edge_cut_risk: bool
    border_visible_score: float
    foreground_fill_ratio: float
    brightness_mean: float
    contrast_score: float
    blur_score: float
    normalized_contrast_score: float
    reject_reason: Optional[str]

    def to_dict(self):
        d = asdict(self)
        # Remove large numpy arrays from serialisation
        d.pop("raw_crop", None)
        d.pop("deskewed_crop", None)
        d.pop("normalized_crop", None)
        return d


@dataclass(frozen=True)
class CropMethodResult:
    crops: list  # list[CardCropResult]
    rejected_crops: list  # list[dict]
    debug_images: dict

    def to_dict(self):
        return {
            "crops": [c.to_dict() for c in self.crops],
            "rejected_crops": self.rejected_crops,
        }


# ---------------------------------------------------------------------------
# Public API — available method / normalization lists
# ---------------------------------------------------------------------------

def available_crop_methods():
    return [
        "bbox_crop_resize",
        "rotated_rect_warp_affine",
        "quad_warp_perspective",
        "quad_warp_perspective_with_safe_padding",
        "quad_warp_perspective_fixed_aspect",
        "quad_warp_perspective_keep_border_margin",
    ]


def available_normalizations():
    return [
        "resize_only_normalization",
        "grayscale_normalization",
        "clahe_normalization",
        "brightness_contrast_normalization",
        "orientation_portrait_normalization",
    ]


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------

def run_crop_deskew(
    crop_method,
    normalization_variant,
    source_frame,
    stage3_geometries,
    crop_source_frame,
    target_width=DEFAULT_TARGET_WIDTH,
    target_height=DEFAULT_TARGET_HEIGHT,
    padding_ratio=0.0,
):
    """Run a Stage 4 crop+normalize pipeline on a list of Stage 3 geometries.

    Parameters
    ----------
    crop_method : str
        One of ``available_crop_methods()``.
    normalization_variant : str
        One of ``available_normalizations()``.
    source_frame : np.ndarray
        The frame to crop from (current for added, previous for removed).
    stage3_geometries : list
        Stage 3 geometry dicts/objects with bbox/ordered_quad_points/rotated_bbox.
    crop_source_frame : str
        ``"current"`` or ``"previous"`` — recorded in results for traceability.
    target_width, target_height : int
        Target crop dimensions.
    padding_ratio : float
        Padding ratio for methods that use it.

    Returns
    -------
    CropMethodResult
    """
    if crop_method not in available_crop_methods():
        raise ValueError(f"Unknown Stage 4 crop method: {crop_method}")
    if normalization_variant not in available_normalizations():
        raise ValueError(f"Unknown Stage 4 normalization: {normalization_variant}")

    crops = []
    rejected = []
    debug_images = {}

    for geometry in stage3_geometries:
        geom_dict = geometry if isinstance(geometry, dict) else geometry.to_dict()
        try:
            raw, deskewed, matrix, pad_ratio, valid = _crop_single(
                crop_method, source_frame, geom_dict, target_width, target_height, padding_ratio,
            )
        except Exception as exc:
            rejected.append({"geometry": _safe_geom_summary(geom_dict), "reject_reason": str(exc)})
            continue

        if raw is None or deskewed is None:
            rejected.append({"geometry": _safe_geom_summary(geom_dict), "reject_reason": "crop_returned_none"})
            continue

        normalized = _normalize_crop(normalization_variant, deskewed, target_width, target_height)
        metrics = _compute_crop_metrics(raw, deskewed, normalized, source_frame)

        crop_h, crop_w = deskewed.shape[:2]
        short_side = max(1, min(crop_w, crop_h))
        long_side = max(crop_w, crop_h)
        crop_ar = float(long_side) / float(short_side)
        ar_error = abs(crop_ar - EXPECTED_ASPECT_RATIO) / EXPECTED_ASPECT_RATIO

        crops.append(CardCropResult(
            raw_crop=raw,
            deskewed_crop=deskewed,
            normalized_crop=normalized,
            crop_method=crop_method,
            normalization_variant=normalization_variant,
            source_geometry=_safe_geom_summary(geom_dict),
            crop_source_frame=crop_source_frame,
            target_width=target_width,
            target_height=target_height,
            crop_width=crop_w,
            crop_height=crop_h,
            crop_aspect_ratio=round(crop_ar, 6),
            aspect_ratio_error=round(ar_error, 6),
            padding_ratio=round(pad_ratio, 6),
            transform_valid=valid,
            transform_matrix=matrix,
            edge_cut_risk=metrics["edge_cut_risk"],
            border_visible_score=round(metrics["border_visible_score"], 6),
            foreground_fill_ratio=round(metrics["foreground_fill_ratio"], 6),
            brightness_mean=round(metrics["brightness_mean"], 6),
            contrast_score=round(metrics["contrast_score"], 6),
            blur_score=round(metrics["blur_score"], 6),
            normalized_contrast_score=round(metrics["normalized_contrast_score"], 6),
            reject_reason=None,
        ))

    return CropMethodResult(crops=crops, rejected_crops=rejected, debug_images=debug_images)


# ---------------------------------------------------------------------------
# Crop methods
# ---------------------------------------------------------------------------

def _crop_single(crop_method, frame, geom, target_w, target_h, padding_ratio):
    """Dispatch to a specific crop method. Returns (raw, deskewed, matrix_list, pad_ratio, valid)."""
    if crop_method == "bbox_crop_resize":
        return _bbox_crop_resize(frame, geom, target_w, target_h)
    if crop_method == "rotated_rect_warp_affine":
        return _rotated_rect_warp_affine(frame, geom, target_w, target_h)
    if crop_method == "quad_warp_perspective":
        return _quad_warp_perspective(frame, geom, target_w, target_h, padding_ratio=0.0)
    if crop_method == "quad_warp_perspective_with_safe_padding":
        pr = padding_ratio if padding_ratio > 0 else 0.03
        return _quad_warp_perspective(frame, geom, target_w, target_h, padding_ratio=pr)
    if crop_method == "quad_warp_perspective_fixed_aspect":
        return _quad_warp_perspective(frame, geom, target_w, target_h, padding_ratio=0.0)
    if crop_method == "quad_warp_perspective_keep_border_margin":
        pr = padding_ratio if padding_ratio > 0 else 0.03
        return _quad_warp_perspective(frame, geom, target_w, target_h, padding_ratio=pr)
    raise ValueError(f"Unhandled crop method: {crop_method}")


def _bbox_crop_resize(frame, geom, target_w, target_h):
    """Axis-aligned bbox crop, then resize. No deskew."""
    bbox = _get_bbox(geom)
    x, y, w, h = _clamp_bbox(bbox, frame.shape)
    raw = frame[y:y + h, x:x + w].copy()
    if raw.size == 0:
        return None, None, None, 0.0, False
    deskewed = cv2.resize(raw, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    return raw, deskewed, None, 0.0, True


def _rotated_rect_warp_affine(frame, geom, target_w, target_h):
    """Rotated rect deskew via affine transform."""
    quad = _get_ordered_quad(geom)
    if quad is None:
        # Fallback to bbox
        return _bbox_crop_resize(frame, geom, target_w, target_h)

    pts = np.array(quad, dtype=np.float32)
    rect = cv2.minAreaRect(pts)
    center, (rw, rh), angle = rect

    # Ensure portrait orientation for the rect dimensions
    if rw > rh:
        rw, rh = rh, rw
        angle += 90.0

    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Expand canvas to avoid clipping
    cos_a = abs(M[0, 0])
    sin_a = abs(M[0, 1])
    fh, fw = frame.shape[:2]
    new_w = int(fh * sin_a + fw * cos_a)
    new_h = int(fh * cos_a + fw * sin_a)
    M[0, 2] += (new_w - fw) / 2.0
    M[1, 2] += (new_h - fh) / 2.0

    rotated = cv2.warpAffine(frame, M, (new_w, new_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # Transform center and crop
    new_center = np.array([center[0], center[1], 1.0])
    nc = M @ new_center
    cx, cy = int(round(nc[0])), int(round(nc[1]))
    half_w, half_h = int(round(rw / 2)), int(round(rh / 2))

    x1 = max(0, cx - half_w)
    y1 = max(0, cy - half_h)
    x2 = min(rotated.shape[1], cx + half_w)
    y2 = min(rotated.shape[0], cy + half_h)

    raw = rotated[y1:y2, x1:x2].copy()
    if raw.size == 0:
        return None, None, None, 0.0, False

    deskewed = cv2.resize(raw, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    matrix_list = M.tolist()
    return raw, deskewed, matrix_list, 0.0, True


def _quad_warp_perspective(frame, geom, target_w, target_h, padding_ratio=0.0):
    """Perspective warp from ordered quad points to target rectangle."""
    quad = _get_ordered_quad(geom)
    if quad is None:
        # Fallback to bbox
        return _bbox_crop_resize(frame, geom, target_w, target_h)

    src = np.array(quad, dtype=np.float32)

    # Apply padding if requested
    actual_padding = padding_ratio
    if padding_ratio > 0:
        src = expand_quad_about_center(src, padding_ratio)
        # Clamp to frame bounds
        src = clamp_quad_to_frame(src, frame.shape)

    dst = np.array([
        [0, 0],
        [target_w - 1, 0],
        [target_w - 1, target_h - 1],
        [0, target_h - 1],
    ], dtype=np.float32)

    valid = validate_quad(src)
    M = cv2.getPerspectiveTransform(src, dst)
    deskewed = cv2.warpPerspective(frame, M, (target_w, target_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # Raw crop = axis-aligned bbox of the (possibly padded) quad
    bbox = _quad_to_bbox(src)
    x, y, w, h = _clamp_bbox(bbox, frame.shape)
    raw = frame[y:y + h, x:x + w].copy() if w > 0 and h > 0 else deskewed.copy()

    matrix_list = M.tolist()
    return raw, deskewed, matrix_list, actual_padding, valid


# ---------------------------------------------------------------------------
# Normalization variants
# ---------------------------------------------------------------------------

def _normalize_crop(variant, deskewed, target_w, target_h):
    """Apply a normalization variant to a deskewed crop."""
    img = resize_to_target(deskewed, target_w, target_h)

    if variant == "resize_only_normalization":
        return img

    if variant == "grayscale_normalization":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    if variant == "clahe_normalization":
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    if variant == "brightness_contrast_normalization":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        p2, p98 = np.percentile(gray, (2, 98))
        if p98 - p2 < 1:
            return img
        alpha = 255.0 / (p98 - p2)
        beta = -p2 * alpha
        adjusted = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        return adjusted

    if variant == "orientation_portrait_normalization":
        h, w = img.shape[:2]
        if w > h:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        return img

    raise ValueError(f"Unknown normalization variant: {variant}")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def expand_quad_about_center(quad_pts, ratio):
    """Expand quad points outward from center by ``ratio``.

    Parameters
    ----------
    quad_pts : np.ndarray, shape (4, 2)
        Four corner points.
    ratio : float
        Expansion ratio (e.g. 0.03 = 3%).

    Returns
    -------
    np.ndarray, shape (4, 2), dtype float32
    """
    pts = np.array(quad_pts, dtype=np.float32)
    center = pts.mean(axis=0)
    expanded = center + (pts - center) * (1.0 + ratio)
    return expanded.astype(np.float32)


def clamp_quad_to_frame(quad_pts, frame_shape):
    """Clamp quad points to frame boundaries."""
    h, w = frame_shape[:2]
    pts = np.array(quad_pts, dtype=np.float32)
    pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
    pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)
    return pts


def validate_quad(quad_pts):
    """Basic quad validation: 4 points, positive area, no collapsed edges."""
    pts = np.array(quad_pts, dtype=np.float32)
    if pts.shape != (4, 2):
        return False
    area = cv2.contourArea(pts)
    if area < 100:
        return False
    # Check no two adjacent points are identical
    for i in range(4):
        d = np.linalg.norm(pts[i] - pts[(i + 1) % 4])
        if d < 2.0:
            return False
    return True


def resize_to_target(img, target_w, target_h):
    """Resize image to exact target dimensions."""
    if img.shape[1] == target_w and img.shape[0] == target_h:
        return img
    return cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def compute_crop_metrics(raw, deskewed, normalized, source_frame=None):
    """Public wrapper for crop quality metrics."""
    return _compute_crop_metrics(raw, deskewed, normalized, source_frame)


def _compute_crop_metrics(raw, deskewed, normalized, source_frame=None):
    """Compute quality metrics for a crop."""
    gray = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY) if deskewed.ndim == 3 else deskewed
    norm_gray = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY) if normalized.ndim == 3 else normalized

    h, w = deskewed.shape[:2]

    # Blur score — variance of Laplacian
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Contrast — stddev of luminance
    contrast = float(np.std(gray))

    # Brightness — mean luminance
    brightness = float(np.mean(gray))

    # Normalized contrast
    norm_contrast = float(np.std(norm_gray))

    # Border visible score — edge density in border bands
    border_score = _border_edge_score(deskewed, band_px=6)

    # Foreground fill ratio — non-black pixels / total
    fg_mask = gray > 15
    fill = float(np.count_nonzero(fg_mask)) / float(max(1, gray.size))

    # Edge cut risk — if border bands have very low edge density it means card edge may be cut
    edge_cut = _check_edge_cut_risk(deskewed, threshold=0.005)

    return {
        "blur_score": blur,
        "contrast_score": contrast,
        "brightness_mean": brightness,
        "normalized_contrast_score": norm_contrast,
        "border_visible_score": border_score,
        "foreground_fill_ratio": fill,
        "edge_cut_risk": edge_cut,
    }


def _border_edge_score(img, band_px=6):
    """Measure edge density in the border band of an image."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    edges = cv2.Canny(gray, 50, 150)
    h, w = edges.shape
    band = max(1, min(band_px, w // 4, h // 4))
    border_mask = np.zeros_like(edges, dtype=np.uint8)
    border_mask[:band, :] = 1
    border_mask[-band:, :] = 1
    border_mask[:, :band] = 1
    border_mask[:, -band:] = 1
    border_pixels = int(np.count_nonzero(border_mask))
    if border_pixels == 0:
        return 0.0
    return float(np.count_nonzero(edges * border_mask)) / float(border_pixels)


def _check_edge_cut_risk(img, threshold=0.005):
    """Check if any side of the crop has very low edge density (potential cut)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    edges = cv2.Canny(gray, 50, 150)
    h, w = edges.shape
    band = max(1, min(6, w // 4, h // 4))
    sides = [
        edges[:band, :],      # top
        edges[-band:, :],     # bottom
        edges[:, :band],      # left
        edges[:, -band:],     # right
    ]
    for side in sides:
        density = float(np.count_nonzero(side)) / float(max(1, side.size))
        if density < threshold:
            return True
    return False


def build_debug_sheet(crops, source_frame, target_w, target_h):
    """Build a debug contact sheet showing all crops side by side.

    Returns an image (np.ndarray) or None if no crops.
    """
    if not crops:
        return None

    n = len(crops)
    gap = 4
    sheet_w = n * target_w + (n - 1) * gap
    sheet_h = target_h * 3 + gap * 2  # raw, deskewed, normalized

    sheet = np.zeros((sheet_h, sheet_w, 3), dtype=np.uint8)
    for i, crop in enumerate(crops):
        x_off = i * (target_w + gap)
        for row_idx, img in enumerate([crop.raw_crop, crop.deskewed_crop, crop.normalized_crop]):
            if img is None:
                continue
            y_off = row_idx * (target_h + gap)
            resized = resize_to_target(img, target_w, target_h)
            if resized.ndim == 2:
                resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2BGR)
            rh, rw = resized.shape[:2]
            rh = min(rh, target_h)
            rw = min(rw, target_w)
            sheet[y_off:y_off + rh, x_off:x_off + rw] = resized[:rh, :rw]

    return sheet


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_bbox(geom):
    """Extract bbox [x, y, w, h] from geometry dict."""
    bbox = geom.get("bbox")
    if bbox is None:
        raise ValueError("Geometry has no bbox")
    return [int(v) for v in bbox]


def _get_ordered_quad(geom):
    """Extract ordered_quad_points from geometry dict, or None."""
    quad = geom.get("ordered_quad_points")
    if quad is None or len(quad) != 4:
        return None
    return [[int(p[0]), int(p[1])] for p in quad]


def _clamp_bbox(bbox, frame_shape):
    """Clamp bbox to frame boundaries."""
    fh, fw = frame_shape[:2]
    x, y, w, h = bbox
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    w = max(0, min(w, fw - x))
    h = max(0, min(h, fh - y))
    return [x, y, w, h]


def _quad_to_bbox(quad_pts):
    """Convert quad points to axis-aligned bbox [x, y, w, h]."""
    pts = np.array(quad_pts, dtype=np.float32)
    x_min = int(np.floor(pts[:, 0].min()))
    y_min = int(np.floor(pts[:, 1].min()))
    x_max = int(np.ceil(pts[:, 0].max()))
    y_max = int(np.ceil(pts[:, 1].max()))
    return [x_min, y_min, x_max - x_min, y_max - y_min]


def _safe_geom_summary(geom):
    """Return a serialisable summary of geometry without large arrays."""
    return {
        "bbox": geom.get("bbox"),
        "ordered_quad_points": geom.get("ordered_quad_points"),
        "geometry_type": geom.get("geometry_type"),
        "geometry_confidence": geom.get("geometry_confidence"),
    }
