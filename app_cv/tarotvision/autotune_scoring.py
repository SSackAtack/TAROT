"""Scoring helpers for live autotuning recommendations.

The score intentionally rewards end-to-end recognition quality more than raw
geometry, because a clean rectangle that does not produce accepted cards is not
useful for the operator.
"""


def _sample_score(sample):
    geometry = float(sample.get("geometry_score", 0.0))
    recognition = float(sample.get("recognition_score", 0.0))
    candidate_count = int(sample.get("candidate_count", 0))
    accepted_count = int(sample.get("accepted_count", 0))
    false_positive_count = int(sample.get("false_positive_count", 0))
    matching_ms = float(sample.get("matching_ms", 0.0))

    accepted_ratio = accepted_count / candidate_count if candidate_count > 0 else 0.0
    latency_penalty = max(0.0, matching_ms - 120.0) / 120.0

    return (
        geometry * 0.35
        + recognition * 0.85
        + accepted_ratio * 0.70
        + accepted_count * 0.10
        - false_positive_count * 2.0
        - latency_penalty * 0.35
    )


def score_autotune_profile(profile_result):
    samples = profile_result.get("samples") or []
    if not samples:
        return {
            "profile": profile_result.get("profile", {}),
            "score": -999.0,
            "confidence": "LOW",
            "reasons": ["no_samples"],
        }

    sample_scores = [_sample_score(sample) for sample in samples]
    average = sum(sample_scores) / len(sample_scores)
    false_positive_total = sum(int(sample.get("false_positive_count", 0)) for sample in samples)
    accepted_total = sum(int(sample.get("accepted_count", 0)) for sample in samples)

    reasons = []
    if false_positive_total:
        reasons.append("false_positive_penalty")
    if accepted_total:
        reasons.append("accepted_cards_reward")
    if not reasons:
        reasons.append("geometry_only")

    if average >= 1.2 and accepted_total > 0 and false_positive_total == 0:
        confidence = "HIGH"
    elif average >= 0.5:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "profile": profile_result.get("profile", {}),
        "score": average,
        "confidence": confidence,
        "reasons": reasons,
        "sample_count": len(samples),
        "accepted_total": accepted_total,
        "false_positive_total": false_positive_total,
    }


def choose_best_profile_result(profile_results):
    scored = [score_autotune_profile(result) for result in profile_results]
    if not scored:
        return None
    return max(scored, key=lambda result: result["score"])
