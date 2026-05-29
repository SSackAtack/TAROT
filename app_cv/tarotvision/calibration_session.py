def score_sample(identified, good_matches, false_contours, jitter, matching_ms):
    identification_bonus = 1000.0 if identified else 0.0
    feature_score = min(float(good_matches), 80.0) * 2.0
    false_contour_penalty = float(false_contours) * 20.0
    jitter_penalty = float(jitter) * 120.0
    matching_penalty = max(0.0, float(matching_ms) - 120.0) * 0.5
    return (
        identification_bonus
        + feature_score
        - false_contour_penalty
        - jitter_penalty
        - matching_penalty
    )


def choose_best_candidate(candidates):
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate["score"])
