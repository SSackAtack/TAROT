from dataclasses import dataclass


@dataclass(frozen=True)
class RecognitionDebug:
    crop_keypoints: int
    top_matches: list
    reject_reason: str | None


def top_match_summary(debug, limit=5):
    sorted_matches = sorted(
        debug.top_matches,
        key=lambda item: item.get("score", 0.0),
        reverse=True,
    )
    return [
        {
            "name": item.get("name"),
            "score": float(item.get("score", 0.0)),
            "match_count": int(item.get("match_count", 0)),
            "inlier_ratio": float(item.get("inlier_ratio", 0.0)),
        }
        for item in sorted_matches[:limit]
    ]
