"""Stage 6 card identification methods for the isolated offline CV lab."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os

import cv2
import numpy as np


FIRST_WAVE_METHODS = [
    "orb_bfmatcher_ratio_test",
    "akaze_bfmatcher",
    "histogram_similarity_hsv",
    "ssim_like_luma",
    "hybrid_orb_plus_histogram",
]


@dataclass(frozen=True)
class ReferenceCard:
    card_id: str
    card_name: str
    image_path: str
    image: np.ndarray


@dataclass(frozen=True)
class IdentificationResult:
    method: str
    predicted_card_id: str
    predicted_card_name: str
    confidence_score: float
    confidence_gap: float
    ambiguous_match: bool
    top_k_candidates: list
    match_evidence: dict


def load_reference_deck(reference_deck_dir, deck_profile_path):
    with open(deck_profile_path, "r", encoding="utf-8-sig") as handle:
        profile = json.load(handle)
    references = []
    for card in profile["cards"]:
        image_path = os.path.join(reference_deck_dir, card["reference_image"])
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Cannot read reference image: {image_path}")
        references.append(ReferenceCard(card["card_id"], card["card_name"], image_path, image))
    return references


def run_identification_method(method, crop, references, readiness_score=1.0, top_k=3):
    if method not in FIRST_WAVE_METHODS:
        raise ValueError(f"Unknown Stage 6 identification method: {method}")
    if crop is None or not references:
        raise ValueError("Stage 6 identification requires a crop and reference cards.")

    if method == "orb_bfmatcher_ratio_test":
        scored = _feature_scores(crop, references, detector="orb")
    elif method == "akaze_bfmatcher":
        scored = _feature_scores(crop, references, detector="akaze")
    elif method == "histogram_similarity_hsv":
        scored = _histogram_scores(crop, references)
    elif method == "ssim_like_luma":
        scored = _ssim_like_scores(crop, references)
    else:
        orb = {item["card_id"]: item for item in _feature_scores(crop, references, detector="orb")}
        hist = {item["card_id"]: item for item in _histogram_scores(crop, references)}
        scored = []
        for reference in references:
            orb_item = orb[reference.card_id]
            hist_item = hist[reference.card_id]
            scored.append({
                "card_id": reference.card_id,
                "card_name": reference.card_name,
                "score": 0.68 * orb_item["score"] + 0.32 * hist_item["score"],
                "evidence": {"orb_score": orb_item["score"], "histogram_score": hist_item["score"]},
            })

    ranked = sorted(scored, key=lambda item: item["score"], reverse=True)
    selected = ranked[: min(top_k, len(ranked))]
    readiness = _clamp01(readiness_score)
    confidence = _clamp01(selected[0]["score"] * (0.75 + 0.25 * readiness))
    gap = selected[0]["score"] - selected[1]["score"] if len(selected) > 1 else selected[0]["score"]
    return IdentificationResult(
        method=method,
        predicted_card_id=selected[0]["card_id"],
        predicted_card_name=selected[0]["card_name"],
        confidence_score=round(confidence, 6),
        confidence_gap=round(max(0.0, gap), 6),
        ambiguous_match=gap < 0.04,
        top_k_candidates=[_round_candidate(item) for item in selected],
        match_evidence=selected[0].get("evidence", {}),
    )


def _feature_scores(crop, references, detector):
    factory = cv2.ORB_create(nfeatures=1200) if detector == "orb" else cv2.AKAZE_create()
    crop_gray = _gray(crop)
    crop_keypoints, crop_descriptors = factory.detectAndCompute(crop_gray, None)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    scored = []
    for reference in references:
        ref_keypoints, ref_descriptors = factory.detectAndCompute(_gray(reference.image), None)
        good = []
        if crop_descriptors is not None and ref_descriptors is not None:
            for pair in matcher.knnMatch(crop_descriptors, ref_descriptors, k=2):
                if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance:
                    good.append(pair[0])
        denominator = max(12, min(len(crop_keypoints), len(ref_keypoints)))
        score = _clamp01(len(good) / float(denominator))
        scored.append({
            "card_id": reference.card_id,
            "card_name": reference.card_name,
            "score": score,
            "evidence": {
                "good_match_count": len(good),
                "crop_keypoint_count": len(crop_keypoints),
                "reference_keypoint_count": len(ref_keypoints),
            },
        })
    return scored


def _histogram_scores(crop, references):
    crop_hist = _hsv_histogram(crop)
    return [
        {
            "card_id": reference.card_id,
            "card_name": reference.card_name,
            "score": _clamp01((cv2.compareHist(crop_hist, _hsv_histogram(reference.image), cv2.HISTCMP_CORREL) + 1.0) / 2.0),
            "evidence": {"metric": "hsv_histogram_correlation"},
        }
        for reference in references
    ]


def _ssim_like_scores(crop, references):
    crop_gray = cv2.resize(_gray(crop), (180, 297), interpolation=cv2.INTER_AREA).astype(np.float32)
    scored = []
    for reference in references:
        ref_gray = cv2.resize(_gray(reference.image), (180, 297), interpolation=cv2.INTER_AREA).astype(np.float32)
        mse = float(np.mean((crop_gray - ref_gray) ** 2))
        score = _clamp01(1.0 - mse / (255.0 ** 2))
        scored.append({
            "card_id": reference.card_id,
            "card_name": reference.card_name,
            "score": score,
            "evidence": {"luma_mse": round(mse, 6)},
        })
    return scored


def _hsv_histogram(image):
    resized = cv2.resize(image, (180, 297), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    histogram = cv2.calcHist([hsv], [0, 1], None, [24, 24], [0, 180, 0, 256])
    cv2.normalize(histogram, histogram)
    return histogram


def _gray(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image


def _round_candidate(item):
    return {
        "card_id": item["card_id"],
        "card_name": item["card_name"],
        "score": round(float(item["score"]), 6),
        "evidence": item.get("evidence", {}),
    }


def _clamp01(value):
    return max(0.0, min(1.0, float(value)))
