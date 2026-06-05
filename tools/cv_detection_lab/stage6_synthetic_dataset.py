"""Deterministic synthetic samples for the isolated Stage 6 validation lab."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

import cv2
import numpy as np


KNOWN_CATEGORIES = (
    "upright_clean",
    "reversed_clean",
    "perspective",
    "blur",
    "exposure",
    "extra_margin",
    "yellow_combined",
)


@dataclass(frozen=True)
class SyntheticSample:
    sample_id: str
    source_deck: str
    source_card_id: str
    expected_card_id: str | None
    is_known: bool
    category: str
    orientation: str
    transform_parameters: dict
    source_image: np.ndarray


def select_evenly_spaced(items, count):
    if count < 1 or count > len(items):
        raise ValueError("Selection count must be between one and the item count.")
    if count == 1:
        return [items[0]]
    indexes = [round(index * (len(items) - 1) / (count - 1)) for index in range(count)]
    return [items[index] for index in indexes]


def build_validation_samples(gilded_references, wrong_deck_sources, seed=6042026):
    samples = []
    for reference in select_evenly_spaced(gilded_references, 24):
        for category in KNOWN_CATEGORIES:
            orientation = "reversed" if category == "reversed_clean" else "upright"
            parameters = _parameters(category, seed, reference.card_id)
            samples.append(_sample("Gilded", reference, category, orientation, parameters, seed, True))
    for deck_name in sorted(wrong_deck_sources):
        for reference in select_evenly_spaced(wrong_deck_sources[deck_name], 12):
            parameters = {"transform": "none", "wrong_deck": True}
            samples.append(_sample(deck_name, reference, "wrong_deck", "upright", parameters, seed, False))
    return samples


def samples_manifest(samples):
    keys = (
        "sample_id", "source_deck", "source_card_id", "expected_card_id",
        "is_known", "category", "orientation", "transform_parameters",
    )
    return [{key: getattr(sample, key) for key in keys} for sample in samples]


def render_sample(sample):
    image = sample.source_image.copy()
    category = sample.category
    parameters = sample.transform_parameters
    if category in ("upright_clean", "wrong_deck"):
        return image
    if category == "reversed_clean":
        return cv2.rotate(image, cv2.ROTATE_180)
    if category == "perspective":
        return _perspective(image, parameters["inset_px"], parameters["shift_px"])
    if category == "blur":
        return cv2.GaussianBlur(image, (parameters["kernel"], parameters["kernel"]), parameters["sigma"])
    if category == "exposure":
        return cv2.convertScaleAbs(image, alpha=parameters["alpha"], beta=parameters["beta"])
    if category == "extra_margin":
        return _extra_margin(image, parameters["margin_px"])
    if category == "yellow_combined":
        changed = _perspective(image, parameters["inset_px"], parameters["shift_px"])
        changed = cv2.GaussianBlur(changed, (parameters["kernel"], parameters["kernel"]), parameters["sigma"])
        changed = cv2.convertScaleAbs(changed, alpha=parameters["alpha"], beta=parameters["beta"])
        return _extra_margin(changed, parameters["margin_px"])
    raise ValueError(f"Unknown synthetic category: {category}")


def _sample(deck, reference, category, orientation, parameters, seed, is_known):
    identity = f"{seed}|{deck}|{reference.card_id}|{category}|{orientation}"
    sample_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return SyntheticSample(
        sample_id=sample_id,
        source_deck=deck,
        source_card_id=reference.card_id,
        expected_card_id=reference.card_id if is_known else None,
        is_known=is_known,
        category=category,
        orientation=orientation,
        transform_parameters=parameters,
        source_image=reference.image,
    )


def _parameters(category, seed, card_id):
    variant = int(hashlib.sha256(f"{seed}|{card_id}|{category}".encode("utf-8")).hexdigest()[:8], 16)
    if category in ("upright_clean", "reversed_clean"):
        return {"transform": category}
    if category == "perspective":
        return {"inset_px": 10 + variant % 7, "shift_px": 5 + variant % 5}
    if category == "blur":
        return {"kernel": 5, "sigma": round(1.2 + (variant % 4) * 0.2, 2)}
    if category == "exposure":
        return {"alpha": round(0.72 + (variant % 4) * 0.08, 2), "beta": 12 + variant % 10}
    if category == "extra_margin":
        return {"margin_px": 22 + variant % 9}
    if category == "yellow_combined":
        return {
            "inset_px": 12 + variant % 6,
            "shift_px": 7 + variant % 5,
            "kernel": 5,
            "sigma": 1.6,
            "alpha": 0.78,
            "beta": 16,
            "margin_px": 28 + variant % 8,
        }
    raise ValueError(f"Unknown synthetic category: {category}")


def _perspective(image, inset, shift):
    height, width = image.shape[:2]
    source = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    target = np.float32([
        [inset + shift, inset],
        [width - 1 - inset, inset + shift],
        [width - 1 - inset - shift, height - 1 - inset],
        [inset, height - 1 - inset - shift],
    ])
    matrix = cv2.getPerspectiveTransform(source, target)
    return cv2.warpPerspective(image, matrix, (width, height), borderMode=cv2.BORDER_CONSTANT)


def _extra_margin(image, margin):
    height, width = image.shape[:2]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    resized = cv2.resize(image, (width - 2 * margin, height - 2 * margin), interpolation=cv2.INTER_AREA)
    canvas[margin:height - margin, margin:width - margin] = resized
    return canvas
