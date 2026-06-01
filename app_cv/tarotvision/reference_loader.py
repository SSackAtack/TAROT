from dataclasses import dataclass
import glob
import json
import os

import cv2

from tarotvision.image_io import imread_grayscale_unicode


@dataclass(frozen=True)
class ReferenceLoadResult:
    cards: dict
    loaded_deck_ids: list
    skipped_files: list
    keypoint_counts: dict


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_matcher(descriptors):
    if descriptors is None or len(descriptors) == 0:
        return None
    try:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        matcher.add([descriptors])
        matcher.train()
        return matcher
    except cv2.error:
        return None


def _load_one_card(file_path, orb, clahe):
    card_name = os.path.basename(file_path).replace(".jpg", "")
    img = imread_grayscale_unicode(file_path)
    if img is None:
        return card_name, None

    img = clahe.apply(img)
    keypoints, descriptors = orb.detectAndCompute(img, None)
    if descriptors is not None:
        keypoints = keypoints[:500]
        descriptors = descriptors[:500]

    reversed_img = cv2.rotate(img, cv2.ROTATE_180)
    reversed_keypoints, reversed_descriptors = orb.detectAndCompute(reversed_img, None)

    return card_name, {
        "image": img,
        "keypoints": keypoints,
        "descriptors": descriptors,
        "reversed_image": reversed_img,
        "reversed_keypoints": reversed_keypoints,
        "reversed_descriptors": reversed_descriptors,
        "matcher": _build_matcher(descriptors),
    }


def load_active_reference_cards(project_root, manifest_path, active_decks_path,
                                fallback_deck_id, orb, clahe, active_ids=None,
                                fallback_cv_path=None, _allow_fallback=True):
    manifest = _load_json(manifest_path, {"decks": []})
    if active_ids is None:
        active_data = _load_json(active_decks_path, {"active_decks": []})
        active_ids = active_data.get("active_decks", [])
    if not active_ids:
        active_ids = [fallback_deck_id]

    decks_by_id = {deck.get("id"): deck for deck in manifest.get("decks", [])}
    cards = {}
    loaded_deck_ids = []
    skipped_files = []
    keypoint_counts = {}

    for deck_id in active_ids:
        deck = decks_by_id.get(deck_id)
        if deck is None and deck_id == fallback_deck_id and fallback_cv_path:
            deck = {"id": fallback_deck_id, "cv_path": fallback_cv_path}
        if not deck:
            continue

        cv_path = os.path.abspath(os.path.join(project_root, deck.get("cv_path", "")))
        file_paths = sorted(glob.glob(os.path.join(cv_path, "*.jpg")))
        if not file_paths:
            continue

        deck_card_count = 0
        for file_path in file_paths:
            card_name, card_data = _load_one_card(file_path, orb, clahe)
            if card_data is None:
                skipped_files.append(file_path)
                continue
            cards[card_name] = card_data
            keypoint_counts[card_name] = len(card_data.get("keypoints") or [])
            deck_card_count += 1

        if deck_card_count > 0:
            loaded_deck_ids.append(deck_id)

    if not cards and fallback_cv_path and _allow_fallback:
        fallback_cards = load_active_reference_cards(
            project_root=project_root,
            manifest_path=manifest_path,
            active_decks_path=active_decks_path,
            fallback_deck_id=fallback_deck_id,
            orb=orb,
            clahe=clahe,
            active_ids=[fallback_deck_id],
            fallback_cv_path=fallback_cv_path,
            _allow_fallback=False,
        )
        return fallback_cards

    return ReferenceLoadResult(
        cards=cards,
        loaded_deck_ids=loaded_deck_ids,
        skipped_files=skipped_files,
        keypoint_counts=keypoint_counts,
    )
