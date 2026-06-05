from dataclasses import dataclass

import cv2
import numpy as np

from tarotvision.card_detection import find_card_quads
from tarotvision.detection_diagnostics import empty_detection_diagnostics


@dataclass(frozen=True)
class DetectionProfile:
    name: str
    mode: str
    canny_low: int = 30
    canny_high: int = 100
    min_area_ratio: float = 0.001
    contour_mode: str = "list"
    use_min_area_rect_fallback: bool = False


@dataclass(frozen=True)
class MultiProfileDetectionResult:
    quads: list
    best_profile: str | None
    debug: dict


DEFAULT_PROFILES = [
    DetectionProfile("canny_low", "canny", canny_low=20, canny_high=80, min_area_ratio=0.001, contour_mode="list"),
    DetectionProfile("canny_default", "canny", canny_low=50, canny_high=150, min_area_ratio=0.005, contour_mode="external"),
    DetectionProfile("adaptive_light", "adaptive_light", min_area_ratio=0.001, contour_mode="list", use_min_area_rect_fallback=True),
    DetectionProfile("adaptive_dark", "adaptive_dark", min_area_ratio=0.001, contour_mode="list", use_min_area_rect_fallback=True),
    DetectionProfile("min_area_rect", "canny", canny_low=20, canny_high=80, min_area_ratio=0.001,
                     contour_mode="list", use_min_area_rect_fallback=True),
]


def _gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def _profile_frame(frame, profile):
    gray = _gray(frame)
    if profile.mode == "canny":
        return frame
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    if profile.mode == "adaptive_light":
        return cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 3,
        )
    if profile.mode == "adaptive_dark":
        return cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 3,
        )
    return frame


def _bbox(quad):
    x, y, w, h = cv2.boundingRect(np.asarray(quad, dtype=np.int32))
    return x, y, w, h


def _iou_box(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1 = max(ax, bx)
    y1 = max(ay, by)
    x2 = min(ax + aw, bx + bw)
    y2 = min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = aw * ah + bw * bh - inter
    return 0.0 if union <= 0 else inter / union


def _dedupe_quads(quads, iou_threshold=0.75):
    accepted = []
    accepted_boxes = []
    for quad in sorted(quads, key=lambda item: cv2.contourArea(item), reverse=True):
        box = _bbox(quad)
        if any(_iou_box(box, existing) >= iou_threshold for existing in accepted_boxes):
            continue
        accepted.append(quad)
        accepted_boxes.append(box)
    return accepted


def find_card_quads_multi_profile(frame, profiles=None, max_candidates=10, background_model=None):
    profiles = profiles or DEFAULT_PROFILES
    all_quads = []
    debug_profiles = []
    best_profile = None
    best_count = 0
    background_mask_nonzero_ratio = None

    if background_model is not None and background_model.active:
        mask = background_model.foreground_mask(frame)
        if mask is not None:
            background_mask_nonzero_ratio = float(np.count_nonzero(mask) / mask.size)
            bg_quads, bg_debug = find_card_quads(
                mask,
                min_area_ratio=0.001,
                canny_low=20,
                canny_high=80,
                contour_mode="list",
                max_candidates=max_candidates,
                return_debug=True,
                use_min_area_rect_fallback=True,
            )
            all_quads.extend(bg_quads)
            if len(bg_quads) > best_count:
                best_count = len(bg_quads)
                best_profile = "background_diff"
            debug_profiles.append({
                "name": "background_diff",
                "mode": "background_diff",
                "quads": len(bg_quads),
                "contours_total": bg_debug.get("contours_total", 0),
                "candidates_after_quad": bg_debug.get("candidates_after_quad", 0),
                "min_area_rect_candidates": bg_debug.get("min_area_rect_candidates", 0),
                "min_area_rect_accepted": bg_debug.get("min_area_rect_accepted", 0),
                "reject_reasons": bg_debug.get("reject_reasons", {}),
            })

    for profile in profiles:
        profile_input = _profile_frame(frame, profile)
        quads, debug = find_card_quads(
            profile_input,
            min_area_ratio=profile.min_area_ratio,
            canny_low=profile.canny_low,
            canny_high=profile.canny_high,
            contour_mode=profile.contour_mode,
            max_candidates=max_candidates,
            return_debug=True,
            use_min_area_rect_fallback=profile.use_min_area_rect_fallback,
        )
        all_quads.extend(quads)
        if len(quads) > best_count:
            best_count = len(quads)
            best_profile = profile.name
        debug_profiles.append({
            "name": profile.name,
            "mode": profile.mode,
            "quads": len(quads),
            "contours_total": debug.get("contours_total", 0),
            "candidates_after_quad": debug.get("candidates_after_quad", 0),
            "min_area_rect_candidates": debug.get("min_area_rect_candidates", 0),
            "min_area_rect_accepted": debug.get("min_area_rect_accepted", 0),
            "reject_reasons": debug.get("reject_reasons", {}),
        })

    deduped = _dedupe_quads(all_quads)[:max_candidates]
    diagnostics = empty_detection_diagnostics()
    diagnostics.update({
        "profiles": debug_profiles,
        "quads_final": len(deduped),
        "best_profile": best_profile,
        "geometry_source": best_profile,
        "background_mask_nonzero_ratio": background_mask_nonzero_ratio,
    })
    return MultiProfileDetectionResult(
        quads=deduped,
        best_profile=best_profile,
        debug=diagnostics,
    )
