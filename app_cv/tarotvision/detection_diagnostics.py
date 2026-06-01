"""Helpers for stable card-detection diagnostics.

The live test workflow compares metrics between physical runs.  Keep the
public keys stable and add new values instead of renaming old ones.
"""


def empty_detection_diagnostics():
    return {
        "profiles": [],
        "quads_final": 0,
        "best_profile": None,
        "geometry_source": None,
        "reject_reasons": {},
        "background_mask_nonzero_ratio": None,
    }


def summarize_detection_diagnostics(diagnostics):
    """Flatten rich detector diagnostics into numeric runtime metrics."""
    if not isinstance(diagnostics, dict):
        diagnostics = {}

    profiles = diagnostics.get("profiles", [])
    if not isinstance(profiles, list):
        profiles = []

    summary = {
        "snapshot_detection_quads_final": int(diagnostics.get("quads_final", 0) or 0),
        "snapshot_detection_profile_count": len(profiles),
        "snapshot_strict_quad_candidates": 0,
        "snapshot_min_area_rect_candidates": 0,
        "snapshot_min_area_rect_accepted": 0,
        "snapshot_foreground_contours_total": 0,
    }

    mask_ratio = diagnostics.get("background_mask_nonzero_ratio")
    if isinstance(mask_ratio, (int, float)):
        summary["snapshot_background_mask_nonzero_ratio"] = float(mask_ratio)

    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        summary["snapshot_strict_quad_candidates"] += int(
            profile.get("candidates_after_quad", 0) or 0
        )
        summary["snapshot_min_area_rect_candidates"] += int(
            profile.get("min_area_rect_candidates", 0) or 0
        )
        summary["snapshot_min_area_rect_accepted"] += int(
            profile.get("min_area_rect_accepted", 0) or 0
        )
        summary["snapshot_foreground_contours_total"] += int(
            profile.get("contours_total", 0) or 0
        )

    return summary
