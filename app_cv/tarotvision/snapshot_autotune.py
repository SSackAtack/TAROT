def score_snapshot_candidate(quad_score, recognition):
    geometry = float(quad_score)
    if recognition is None:
        return geometry * 0.4

    match_count = float(recognition.get("match_count", 0))
    inlier_ratio = float(recognition.get("inlier_ratio", 0.0))
    bounded_inlier_ratio = max(0.0, min(inlier_ratio, 1.0))
    recognition_score = min(match_count / 30.0, 1.0) * bounded_inlier_ratio
    return geometry * 0.45 + recognition_score * 1.10
