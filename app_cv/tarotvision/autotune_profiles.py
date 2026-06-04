"""Candidate runtime profiles for live autotuning.

The MVP deliberately avoids ORB recognition thresholds and camera hardware
controls. It searches only the safer detection/workspace parameters that can be
applied and rolled back through RuntimeConfigSession.
"""


def generate_candidate_profiles():
    profiles = []
    min_area_values = [0.0005, 0.001, 0.002, 0.005]
    max_candidate_values = [6.0, 10.0, 16.0]
    inflate_values = [0.0, 6.0]

    for min_area in min_area_values:
        for max_candidates in max_candidate_values:
            for inflate in inflate_values:
                profiles.append({
                    "CARD_DETECT_MIN_AREA_RATIO": min_area,
                    "CARD_DETECT_MAX_CANDIDATES": max_candidates,
                    "WORKSPACE_INFLATE_PERCENT": inflate,
                })

    return profiles
