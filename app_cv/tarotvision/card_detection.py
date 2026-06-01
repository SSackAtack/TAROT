"""Card rectangle detection for TarotVision.

Detects rectangular contours with tarot-card aspect ratio (~1.72) in a
camera frame or an ArUco-warped table image.  Returns a list of
four-point quads (OpenCV approxPolyDP results) that are likely cards.

Used by downstream modules (card_recognition) to crop and normalize
individual card images for ORB matching.
"""

import cv2
import numpy as np


# Standardowy stosunek wysokosc/szerokosc kart tarota Rider-Waite-Smith
CARD_ASPECT_RATIO = 1.72
# Tolerancja — poluzowana, bo perspektywa kamery znieksztalca proporcje,
# a karty moga byc lekko obrocone
CARD_ASPECT_TOLERANCE = 0.45

# Minimalna powierzchnia konturu jako udzial w calym obrazie (odrzuca szum)
MIN_AREA_RATIO = 0.005
# Maksymalna powierzchnia konturu (odrzuca krawedzie calego obrazu)
MAX_AREA_RATIO = 0.5

# Parametry Canny edge detection
CANNY_LOW = 50
CANNY_HIGH = 150


def is_card_aspect_ratio(width, height):
    """Check if width/height ratio is close to a tarot card (~1.72).

    Handles both portrait and landscape orientations by using
    max/min rather than assuming portrait.

    Args:
        width:  bounding rect width in pixels.
        height: bounding rect height in pixels.

    Returns:
        True if the ratio is within CARD_ASPECT_TOLERANCE of CARD_ASPECT_RATIO.
    """
    if width <= 0 or height <= 0:
        return False
    ratio = max(width, height) / min(width, height)
    return abs(ratio - CARD_ASPECT_RATIO) <= CARD_ASPECT_TOLERANCE


def find_card_quads(bgr_frame, min_area_ratio=MIN_AREA_RATIO,
                    max_area_ratio=MAX_AREA_RATIO, canny_low=CANNY_LOW,
                    canny_high=CANNY_HIGH, contour_mode="external",
                    max_candidates=None, return_debug=False,
                    use_min_area_rect_fallback=False):
    """Find four-sided convex contours with card-like aspect ratio.

    Pipeline: grayscale -> blur -> Canny edges -> findContours ->
    approxPolyDP -> convexity + aspect ratio filter.

    Args:
        bgr_frame:      BGR or grayscale numpy array (the camera frame
                         or an ArUco-warped table view).
        min_area_ratio:  minimum contour area as fraction of frame area.
        max_area_ratio:  maximum contour area as fraction of frame area.
        canny_low:       low threshold for Canny edge detector.
        canny_high:      high threshold for Canny edge detector.
        contour_mode:    contour retrieval mode ("external", "list", "tree").
        max_candidates:  maximum number of candidate quads to return (sorted by area descending).
        return_debug:    if True, returns tuple (quads, debug_info).
        use_min_area_rect_fallback: when True, wrap ragged contours in the
                         best rotated rectangle if strict 4-point detection fails.

    Returns:
        List of numpy arrays, each with shape (4, 1, 2) — the four
        corner points of each detected card quad.
        If return_debug is True, returns (quads, debug_info).
    """
    mode_map = {
        "external": cv2.RETR_EXTERNAL,
        "list": cv2.RETR_LIST,
        "tree": cv2.RETR_TREE,
    }

    if contour_mode not in mode_map:
        raise ValueError(
            f"Invalid contour_mode '{contour_mode}'. "
            f"Allowed values are: 'external', 'list', 'tree'."
        )

    cv2_mode = mode_map[contour_mode]

    if len(bgr_frame.shape) == 3:
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = bgr_frame

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)
    contours, _ = cv2.findContours(edges, cv2_mode, cv2.CHAIN_APPROX_SIMPLE)

    frame_area = bgr_frame.shape[0] * bgr_frame.shape[1]
    min_area = frame_area * min_area_ratio
    max_area = frame_area * max_area_ratio

    contours_total = len(contours)
    candidates_after_area = 0
    candidates_after_quad = 0
    min_area_rect_candidates = 0
    min_area_rect_accepted = 0
    reject_reasons = {
        "area": 0,
        "non_quad": 0,
        "non_convex": 0,
        "aspect": 0,
        "min_area_rect_aspect": 0,
    }

    quads = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            reject_reasons["area"] += 1
            continue

        candidates_after_area += 1

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            candidates_after_quad += 1

            x, y, w, h = cv2.boundingRect(approx)
            if is_card_aspect_ratio(w, h):
                quads.append(approx)
            else:
                reject_reasons["aspect"] += 1
            continue

        if len(approx) == 4:
            reject_reasons["non_convex"] += 1
        else:
            reject_reasons["non_quad"] += 1

        if not use_min_area_rect_fallback:
            continue

        min_area_rect_candidates += 1
        rect = cv2.minAreaRect(contour)
        rect_w, rect_h = rect[1]
        if not is_card_aspect_ratio(rect_w, rect_h):
            reject_reasons["min_area_rect_aspect"] += 1
            continue
        min_area_rect_accepted += 1
        rect_quad = _box_to_quad(cv2.boxPoints(rect))
        quads.append(rect_quad)

    # Sort quads by area size descending
    quads.sort(key=lambda q: cv2.contourArea(q), reverse=True)

    # Limit to max_candidates if specified
    if max_candidates is not None:
        quads = quads[:max_candidates]

    if return_debug:
        debug_info = {
            "contour_mode": contour_mode,
            "canny_low": int(canny_low),
            "canny_high": int(canny_high),
            "contours_total": int(contours_total),
            "candidates_after_area": int(candidates_after_area),
            "candidates_after_quad": int(candidates_after_quad),
            "min_area_rect_candidates": int(min_area_rect_candidates),
            "min_area_rect_accepted": int(min_area_rect_accepted),
            "reject_reasons": reject_reasons,
            "quads_final": len(quads),
        }
        return quads, debug_info

    return quads


def find_card_quads_with_debug(bgr_frame, min_area_ratio=MIN_AREA_RATIO,
                               max_area_ratio=MAX_AREA_RATIO, canny_low=CANNY_LOW,
                               canny_high=CANNY_HIGH, contour_mode="external",
                               max_candidates=None,
                               use_min_area_rect_fallback=False):
    """Find card quads and return debug diagnostics.

    Args:
        bgr_frame:      BGR or grayscale numpy array.
        min_area_ratio:  minimum contour area ratio.
        max_area_ratio:  maximum contour area ratio.
        canny_low:       low threshold for Canny.
        canny_high:      high threshold for Canny.
        contour_mode:    contour retrieval mode.
        max_candidates:  maximum candidates to return.
        use_min_area_rect_fallback: enable rotated-box reconstruction.

    Returns:
        Tuple of (quads, debug_info).
    """
    return find_card_quads(
        bgr_frame,
        min_area_ratio=min_area_ratio,
        max_area_ratio=max_area_ratio,
        canny_low=canny_low,
        canny_high=canny_high,
        contour_mode=contour_mode,
        max_candidates=max_candidates,
        return_debug=True,
        use_min_area_rect_fallback=use_min_area_rect_fallback,
    )


def contour_to_min_area_quad(contour):
    """Return a 4-point OpenCV quad for the contour's rotated bounding box."""
    rect = cv2.minAreaRect(contour)
    return _box_to_quad(cv2.boxPoints(rect))


def _box_to_quad(box):
    return np.asarray(box, dtype=np.float32).reshape(4, 1, 2)
