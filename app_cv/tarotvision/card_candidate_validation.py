from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class CardCandidateValidation:
    accepted: bool
    reject_reason: str | None
    contrast: float
    edge_density: float
    dark_pixel_ratio: float
    border_edge_density: float
    border_dark_ratio: float


def validate_card_candidate_crop(
    crop,
    min_contrast=10.0,
    min_edge_density=0.01,
    min_dark_pixel_ratio=0.01,
    min_border_edge_density=0.003,
    min_border_dark_ratio=0.008,
):
    gray = _as_gray_uint8(crop)
    if gray is None or gray.size == 0:
        return _result(False, "empty_crop", 0.0, 0.0, 0.0, 0.0, 0.0)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 120)
    contrast = float(np.std(gray))
    edge_density = float(np.count_nonzero(edges) / edges.size)
    dark_pixel_ratio = float(np.count_nonzero(gray < 90) / gray.size)
    border_mask = _border_mask(gray.shape)
    border_pixels = int(np.count_nonzero(border_mask))
    if border_pixels:
        border_edge_density = float(np.count_nonzero(edges[border_mask]) / border_pixels)
        border_dark_ratio = float(np.count_nonzero(gray[border_mask] < 110) / border_pixels)
    else:
        border_edge_density = 0.0
        border_dark_ratio = 0.0

    if contrast < min_contrast and edge_density < min_edge_density:
        return _result(
            False,
            "smooth_low_texture",
            contrast,
            edge_density,
            dark_pixel_ratio,
            border_edge_density,
            border_dark_ratio,
        )

    lacks_global_card_marks = dark_pixel_ratio < min_dark_pixel_ratio
    lacks_border_marks = (
        border_edge_density < min_border_edge_density
        and border_dark_ratio < min_border_dark_ratio
    )
    if lacks_global_card_marks and lacks_border_marks:
        return _result(
            False,
            "no_card_border_evidence",
            contrast,
            edge_density,
            dark_pixel_ratio,
            border_edge_density,
            border_dark_ratio,
        )

    return _result(
        True,
        None,
        contrast,
        edge_density,
        dark_pixel_ratio,
        border_edge_density,
        border_dark_ratio,
    )


def _as_gray_uint8(crop):
    if crop is None or not hasattr(crop, "shape"):
        return None
    image = np.asarray(crop)
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        return None
    if gray.dtype == np.uint8:
        return gray
    return np.clip(gray, 0, 255).astype(np.uint8)


def _border_mask(shape):
    height, width = shape[:2]
    band = max(4, int(min(height, width) * 0.06))
    mask = np.zeros((height, width), dtype=bool)
    mask[:band, :] = True
    mask[-band:, :] = True
    mask[:, :band] = True
    mask[:, -band:] = True
    return mask


def _result(
    accepted,
    reject_reason,
    contrast,
    edge_density,
    dark_pixel_ratio,
    border_edge_density,
    border_dark_ratio,
):
    return CardCandidateValidation(
        accepted=bool(accepted),
        reject_reason=reject_reason,
        contrast=round(float(contrast), 3),
        edge_density=round(float(edge_density), 5),
        dark_pixel_ratio=round(float(dark_pixel_ratio), 5),
        border_edge_density=round(float(border_edge_density), 5),
        border_dark_ratio=round(float(border_dark_ratio), 5),
    )
