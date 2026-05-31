"""Offline card detection parameter autotuning for TarotVision.

Iterates through different OpenCV Canny edge and contour detection configurations
to find the parameters that maximize card candidate outline detection quality
without running the full downstream recognition model.
"""

import math
import numpy as np
import cv2

from tarotvision.card_detection import find_card_quads


def score_candidate_quad(quad, frame_shape):
    """Calculates a mathematical score for a single quad candidate.

    Scores are normalized between 0.0 and 1.0 based on:
    1. Bounding rect aspect ratio (closeness to 1.72).
    2. Area ratio (penalizes massive outlines like A4 paper).
    3. Centrality (distance from the center of the frame).

    Args:
        quad:         np.ndarray of shape (4, 1, 2) corner points.
        frame_shape:  (height, width, channels) or (height, width) of the frame.

    Returns:
        float score between 0.0 and 1.0.
    """
    frame_h, frame_w = frame_shape[0], frame_shape[1]
    frame_area = frame_h * frame_w

    if frame_area <= 0:
        return 0.0

    area = cv2.contourArea(quad)
    area_ratio = area / frame_area

    # Out of reasonable bounds
    if area_ratio < 0.0001 or area_ratio > 0.6:
        return 0.0

    # Aspect ratio evaluation
    x, y, w, h = cv2.boundingRect(quad)
    if w <= 0 or h <= 0:
        return 0.0

    ratio = max(w, h) / min(w, h)
    # RWS Card target is 1.72. Tolerance is 0.45.
    target_ratio = 1.72
    max_tolerance = 0.45
    diff = abs(ratio - target_ratio)

    if diff > max_tolerance:
        return 0.0

    aspect_score = 1.0 - (diff / max_tolerance)

    # Area multiplier: penalize huge A4 contours (e.g. ratio > 0.15)
    # to favor the actual smaller nested card outlines.
    if area_ratio <= 0.15:
        area_multiplier = 1.0
    else:
        # Interpolate down to 0.0 at 0.6 area ratio
        area_multiplier = max(0.0, 1.0 - (area_ratio - 0.15) / (0.6 - 0.15))

    # Centrality check (cards are typically near the center)
    cx = x + w / 2
    cy = y + h / 2
    dist_x = cx - frame_w / 2
    dist_y = cy - frame_h / 2
    dist = math.sqrt(dist_x**2 + dist_y**2)
    max_possible_dist = math.sqrt(frame_w**2 + frame_h**2) / 2

    centrality_score = 1.0 - (dist / max_possible_dist) if max_possible_dist > 0 else 1.0

    # Final combined score: weighted product
    return aspect_score * area_multiplier * (0.8 + 0.2 * centrality_score)


def tune_card_detection_params(frame, search_space=None, max_iterations=250):
    """Offline autotuner for card rectangle detection.

    Runs a coarse search over the Canny edge detector and contour retrieval
    parameter space to find configuration that maximizes card outline quality.

    Args:
        frame:           np.ndarray BGR or grayscale frame.
        search_space:    dict of param lists (canny_low, canny_high, min_area_ratio, contour_mode).
        max_iterations:  maximum parameter trials allowed.

    Returns:
        dict with autotuning results.
    """
    if search_space is None:
        search_space = {
            "canny_low": [10, 20, 30, 40, 50],
            "canny_high": [60, 90, 120, 150],
            "min_area_ratio": [0.0005, 0.001, 0.002, 0.005],
            "contour_mode": ["external", "list", "tree"],
        }

    canny_lows = search_space.get("canny_low", [50])
    canny_highs = search_space.get("canny_high", [150])
    min_area_ratios = search_space.get("min_area_ratio", [0.005])
    contour_modes = search_space.get("contour_mode", ["external"])

    best_score = -1.0
    best_params = {
        "canny_low": 50,
        "canny_high": 150,
        "min_area_ratio": 0.005,
        "contour_mode": "external",
        "max_candidates": 10,
    }

    iterations = 0
    debug_runs = []
    candidates_found = 0

    # Grid search
    for cl in canny_lows:
        for ch in canny_highs:
            # Skip invalid Canny configurations where low >= high
            if cl >= ch:
                continue
            for mar in min_area_ratios:
                for mode in contour_modes:
                    if iterations >= max_iterations:
                        break

                    iterations += 1

                    try:
                        # Find card quads using these parameters
                        quads, debug_info = find_card_quads(
                            frame,
                            min_area_ratio=mar,
                            canny_low=cl,
                            canny_high=ch,
                            contour_mode=mode,
                            max_candidates=10,
                            return_debug=True
                        )

                        # Evaluate all candidates, select the highest score
                        run_score = 0.0
                        if len(quads) > 0:
                            scores = [score_candidate_quad(q, frame.shape) for q in quads]
                            run_score = max(scores) if scores else 0.0
                            candidates_found += len(quads)

                        # Update best parameters if score improved
                        if run_score > best_score:
                            best_score = run_score
                            best_params = {
                                "canny_low": cl,
                                "canny_high": ch,
                                "min_area_ratio": mar,
                                "contour_mode": mode,
                                "max_candidates": 10,
                            }

                        debug_runs.append({
                            "params": {
                                "canny_low": cl,
                                "canny_high": ch,
                                "min_area_ratio": mar,
                                "contour_mode": mode,
                            },
                            "score": run_score,
                            "quads_count": len(quads),
                            "contours_total": debug_info["contours_total"],
                        })

                    except Exception as e:
                        # Graceful handling of errors during iteration
                        debug_runs.append({
                            "params": {
                                "canny_low": cl,
                                "canny_high": ch,
                                "min_area_ratio": mar,
                                "contour_mode": mode,
                            },
                            "error": str(e),
                            "score": 0.0,
                            "quads_count": 0,
                        })

                if iterations >= max_iterations:
                    break
            if iterations >= max_iterations:
                break
        if iterations >= max_iterations:
            break

    # Determine confidence levels
    if best_score < 0.0001:
        confidence = "LOW"
        best_score = 0.0
    elif best_score < 0.4:
        confidence = "LOW"
    elif best_score < 0.7:
        confidence = "MEDIUM"
    else:
        confidence = "HIGH"

    return {
        "best_params": best_params,
        "best_score": float(best_score),
        "candidates_found": candidates_found,
        "iterations": iterations,
        "confidence": confidence,
        "debug": debug_runs,
    }


class AutoTuner:
    """Class wrapper for offline card detection parameter tuning."""

    def __init__(self, search_space=None, max_iterations=250):
        self.search_space = search_space
        self.max_iterations = max_iterations

    def tune(self, frame):
        """Runs the autotuner on the provided frame."""
        return tune_card_detection_params(
            frame,
            search_space=self.search_space,
            max_iterations=self.max_iterations
        )
