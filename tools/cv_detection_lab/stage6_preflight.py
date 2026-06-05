"""Stage 6 reference deck and ground truth preflight validator.

CLI:
    python tools/cv_detection_lab/stage6_preflight.py \
        --fixture logs/live_fixtures/event_first_current_debug_verified \
        --reference-deck-dir biblioteka_talii/<deck>/produkcja/wzorce_cv \
        --deck-profile biblioteka_talii/<deck>/deck_profile.json \
        --ground-truth logs/live_fixtures/event_first_current_debug_verified/ground_truth.json \
        --output logs/offline_replay/stage6_card_identification_preflight

Dependencies: standard library only.
Does NOT perform card identification, ORB matching, OCR, ML, benchmark execution,
or runtime integration.
"""
import argparse
import json
import os


STAGE = "stage6_card_identification_preflight"
DEFAULT_STAGE5_OUTPUT_DIR = os.path.join(
    "logs",
    "offline_replay",
    "stage5_crop_quality_validation",
    "quality_metric_suite_v1",
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SPECIAL_EXPECTED_CARD_IDS = {"UNKNOWN_DECK", "NO_REFERENCE_MATCH", "NOT_IN_REFERENCE_SCOPE"}

SCENARIO_FRAME_NAMES = {
    "empty": "analysis_frame_0.png",
    "one_card": "analysis_frame_1.png",
    "three_cards": "analysis_frame_3.png",
}

REQUIRED_PAIRS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 1,
    "empty_to_three_cards": 3,
    "one_card_to_three_cards": 2,
    "one_card_to_empty": 1,
    "three_cards_to_empty": 3,
}

DECK_PROFILE_REQUIRED_FIELDS = [
    "deck_id",
    "deck_profile_version",
    "display_name",
    "scope",
    "cards",
]

GROUND_TRUTH_REQUIRED_FIELDS = [
    "deck_profile_id",
    "deck_profile_version",
    "pairs",
]

LABEL_REQUIRED_FIELDS = [
    "crop_index",
    "expected_card_id",
    "orientation",
]


def run_preflight(
    fixture_dir,
    reference_deck_dir,
    deck_profile_path,
    ground_truth_path,
    output_dir=None,
    stage5_output_dir=DEFAULT_STAGE5_OUTPUT_DIR,
):
    """Validate Stage 6 input readiness and optionally write reports."""
    errors = []
    warnings = []
    checks = []

    _check_fixture(fixture_dir, checks, errors)
    reference_image_files = _check_reference_deck(reference_deck_dir, checks, errors)
    deck_profile = _load_json_file(deck_profile_path, "MISSING_DECK_PROFILE", "INVALID_DECK_PROFILE_JSON", errors)
    ground_truth = _load_json_file(ground_truth_path, "MISSING_GROUND_TRUTH", "INVALID_GROUND_TRUTH_JSON", errors)

    deck_summary, deck_cards = _validate_deck_profile(
        deck_profile,
        reference_deck_dir,
        reference_image_files,
        checks,
        errors,
    )
    ground_truth_summary = _validate_ground_truth(ground_truth, deck_profile, deck_cards, checks, errors)
    _check_stage5_outputs(stage5_output_dir, checks, warnings)

    status = _status(errors, warnings)
    report = {
        "stage": STAGE,
        "status": status,
        "fixture_dir": fixture_dir,
        "reference_deck_dir": reference_deck_dir,
        "deck_profile_path": deck_profile_path,
        "ground_truth_path": ground_truth_path,
        "deck_profile": deck_summary,
        "ground_truth": ground_truth_summary,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "required_next_action": _required_next_action(status),
    }

    if output_dir:
        _write_reports(output_dir, report)
    return report


def _check_fixture(fixture_dir, checks, errors):
    if not os.path.isdir(fixture_dir):
        _add_error(errors, "MISSING_FIXTURE_DIR", "Fixture directory does not exist.", path=fixture_dir)
        _add_check(checks, "fixture", "FAIL", "Fixture directory is missing.")
        return

    missing = []
    for scenario, frame_name in SCENARIO_FRAME_NAMES.items():
        frame_path = os.path.join(fixture_dir, scenario, frame_name)
        if not os.path.isfile(frame_path):
            missing.append(frame_path)
            _add_error(errors, "MISSING_FIXTURE_FRAME", "Required fixture frame is missing.", path=frame_path)
    _add_check(checks, "fixture", "PASS" if not missing else "FAIL", f"Missing frames: {len(missing)}.")


def _check_reference_deck(reference_deck_dir, checks, errors):
    if not os.path.isdir(reference_deck_dir):
        _add_error(
            errors,
            "MISSING_REFERENCE_DECK_DIR",
            "Reference deck directory does not exist.",
            path=reference_deck_dir,
        )
        _add_check(checks, "reference_deck", "FAIL", "Reference deck directory is missing.")
        return set()

    image_files = {
        name
        for name in os.listdir(reference_deck_dir)
        if os.path.isfile(os.path.join(reference_deck_dir, name))
        and os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS
    }
    if not image_files:
        _add_error(errors, "NO_REFERENCE_IMAGES", "Reference deck directory contains no supported images.")
    _add_check(checks, "reference_deck", "PASS" if image_files else "FAIL", f"Image files found: {len(image_files)}.")
    return image_files


def _validate_deck_profile(deck_profile, reference_deck_dir, reference_image_files, checks, errors):
    summary = {
        "deck_id": None,
        "deck_profile_version": None,
        "display_name": None,
        "scope": None,
        "declared_card_count": 0,
        "reference_image_count": len(reference_image_files),
        "missing_reference_images": [],
        "duplicate_card_ids": [],
        "empty_card_names": [],
    }
    deck_cards = {}

    if not isinstance(deck_profile, dict):
        _add_check(checks, "deck_profile", "FAIL", "Deck profile could not be loaded.")
        return summary, deck_cards

    for field in DECK_PROFILE_REQUIRED_FIELDS:
        if field not in deck_profile:
            _add_error(errors, "MISSING_DECK_PROFILE_FIELD", f"Missing deck profile field: {field}.", field=field)

    cards = deck_profile.get("cards")
    if not isinstance(cards, list):
        _add_error(errors, "INVALID_DECK_PROFILE_CARDS", "Deck profile cards must be a list.")
        cards = []

    summary.update(
        {
            "deck_id": deck_profile.get("deck_id"),
            "deck_profile_version": deck_profile.get("deck_profile_version"),
            "display_name": deck_profile.get("display_name"),
            "scope": deck_profile.get("scope"),
            "declared_card_count": deck_profile.get("card_count", len(cards)),
        }
    )

    seen_card_ids = set()
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            _add_error(errors, "INVALID_DECK_PROFILE_CARD", "Deck profile card entry must be an object.", index=index)
            continue
        for field in ("card_id", "card_name", "reference_image"):
            if field not in card:
                _add_error(errors, "MISSING_CARD_FIELD", f"Missing card field: {field}.", index=index, field=field)

        card_id = card.get("card_id")
        card_name = card.get("card_name")
        reference_image = card.get("reference_image")

        if card_id in seen_card_ids:
            summary["duplicate_card_ids"].append(card_id)
            _add_error(errors, "DUPLICATE_CARD_ID", "Duplicate card_id in deck profile.", card_id=card_id)
        elif card_id:
            seen_card_ids.add(card_id)
            deck_cards[card_id] = card

        if not isinstance(card_name, str) or not card_name.strip():
            summary["empty_card_names"].append(card_id)
            _add_error(errors, "EMPTY_CARD_NAME", "card_name must not be empty.", card_id=card_id)

        if isinstance(reference_image, str):
            reference_path = os.path.join(reference_deck_dir, reference_image)
            if reference_image not in reference_image_files and not os.path.isfile(reference_path):
                summary["missing_reference_images"].append(reference_image)
                _add_error(
                    errors,
                    "MISSING_REFERENCE_IMAGE",
                    "Deck profile reference_image is missing in reference deck dir.",
                    path=reference_path,
                    card_id=card_id,
                )

    _add_check(checks, "deck_profile", "PASS" if not summary["missing_reference_images"] else "FAIL", "Deck profile validated.")
    return summary, deck_cards


def _validate_ground_truth(ground_truth, deck_profile, deck_cards, checks, errors):
    summary = {
        "pair_count": 0,
        "label_count": 0,
        "unknown_count": 0,
        "not_in_reference_scope_count": 0,
    }
    if not isinstance(ground_truth, dict):
        _add_check(checks, "ground_truth", "FAIL", "Ground truth could not be loaded.")
        return summary

    for field in GROUND_TRUTH_REQUIRED_FIELDS:
        if field not in ground_truth:
            _add_error(errors, "MISSING_GROUND_TRUTH_FIELD", f"Missing ground truth field: {field}.", field=field)

    if isinstance(deck_profile, dict):
        if ground_truth.get("deck_profile_id") != deck_profile.get("deck_id"):
            _add_error(errors, "DECK_PROFILE_ID_MISMATCH", "Ground truth deck_profile_id does not match deck profile.")
        if ground_truth.get("deck_profile_version") != deck_profile.get("deck_profile_version"):
            _add_error(
                errors,
                "DECK_PROFILE_VERSION_MISMATCH",
                "Ground truth deck_profile_version does not match deck profile.",
            )

    pairs = ground_truth.get("pairs")
    if not isinstance(pairs, dict):
        _add_error(errors, "INVALID_GROUND_TRUTH_PAIRS", "Ground truth pairs must be an object.")
        pairs = {}

    summary["pair_count"] = len(pairs)
    for pair_name, expected_count in REQUIRED_PAIRS.items():
        if pair_name not in pairs:
            _add_error(errors, "MISSING_REQUIRED_PAIR", "Required ground truth pair is missing.", pair=pair_name)
            continue
        labels = pairs[pair_name]
        if not isinstance(labels, list):
            _add_error(errors, "INVALID_PAIR_LABELS", "Ground truth pair labels must be a list.", pair=pair_name)
            continue
        if pair_name == "empty_to_empty" and labels:
            _add_error(
                errors,
                "EMPTY_TO_EMPTY_SHOULD_HAVE_NO_LABELS",
                "empty_to_empty must not contain labels.",
                pair=pair_name,
            )
        if len(labels) != expected_count:
            _add_error(
                errors,
                "UNEXPECTED_LABEL_COUNT",
                "Ground truth pair has unexpected label count.",
                pair=pair_name,
                expected_count=expected_count,
                actual_count=len(labels),
            )
        for label in labels:
            _validate_label(label, pair_name, deck_cards, summary, errors)

    _add_check(checks, "ground_truth", "PASS" if not errors else "FAIL", "Ground truth validated.")
    return summary


def _validate_label(label, pair_name, deck_cards, summary, errors):
    if not isinstance(label, dict):
        _add_error(errors, "INVALID_GROUND_TRUTH_LABEL", "Ground truth label must be an object.", pair=pair_name)
        return
    for field in LABEL_REQUIRED_FIELDS:
        if field not in label:
            _add_error(errors, "MISSING_GROUND_TRUTH_LABEL_FIELD", f"Missing label field: {field}.", pair=pair_name)

    summary["label_count"] += 1
    expected_card_id = label.get("expected_card_id")
    if expected_card_id in SPECIAL_EXPECTED_CARD_IDS:
        summary["unknown_count"] += 1
        if expected_card_id == "NOT_IN_REFERENCE_SCOPE":
            summary["not_in_reference_scope_count"] += 1
        return

    if expected_card_id not in deck_cards:
        summary["not_in_reference_scope_count"] += 1
        _add_error(
            errors,
            "NOT_IN_REFERENCE_SCOPE",
            "Expected card id is not present in deck profile.",
            pair=pair_name,
            card_id=expected_card_id,
        )
        return

    expected_card_name = label.get("expected_card_name")
    profile_card_name = deck_cards[expected_card_id].get("card_name")
    if expected_card_name is not None and expected_card_name != profile_card_name:
        _add_error(
            errors,
            "CARD_NAME_MISMATCH",
            "expected_card_name contradicts deck profile.",
            pair=pair_name,
            card_id=expected_card_id,
        )


def _check_stage5_outputs(stage5_output_dir, checks, warnings):
    missing = []
    for pair_name in REQUIRED_PAIRS:
        pair_dir = os.path.join(stage5_output_dir, pair_name)
        for file_name in ("quality_debug.json", "crop_quality_debug_sheet.png"):
            path = os.path.join(pair_dir, file_name)
            if not os.path.isfile(path):
                missing.append(path)
    if missing:
        _add_warning(
            warnings,
            "MISSING_STAGE5_OUTPUT",
            "Stage 5 output is missing; Stage 6 benchmark can regenerate upstream outputs if designed to do so.",
            missing_count=len(missing),
        )
    _add_check(checks, "stage5_output", "PASS" if not missing else "WARNING", f"Missing files: {len(missing)}.")


def _load_json_file(path, missing_code, invalid_code, errors):
    if not os.path.isfile(path):
        _add_error(errors, missing_code, "Required JSON file is missing.", path=path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        _add_error(errors, invalid_code, f"Invalid JSON: {exc}", path=path)
        return None


def _write_reports(output_dir, report):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "preflight_report.json")
    md_path = os.path.join(output_dir, "preflight_report.md")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(_markdown_report(report))


def _markdown_report(report):
    lines = [
        "# Stage 6 Card Identification Preflight Report",
        "",
        "## Status",
        report["status"],
        "",
        "## Inputs",
        f"- fixture_dir: `{report['fixture_dir']}`",
        f"- reference_deck_dir: `{report['reference_deck_dir']}`",
        f"- deck_profile_path: `{report['deck_profile_path']}`",
        f"- ground_truth_path: `{report['ground_truth_path']}`",
        "",
        "## Fixture Check",
        _check_detail(report, "fixture"),
        "",
        "## Reference Deck Check",
        _check_detail(report, "reference_deck"),
        "",
        "## Deck Profile Check",
        _check_detail(report, "deck_profile"),
        "",
        "## Ground Truth Check",
        _check_detail(report, "ground_truth"),
        "",
        "## Required Pair Check",
        _required_pair_summary(report),
        "",
        "## Stage 5 Output Check",
        _check_detail(report, "stage5_output"),
        "",
        "## Errors",
        _issue_lines(report["errors"]),
        "",
        "## Warnings",
        _issue_lines(report["warnings"]),
        "",
        "## Required Next Action",
        report["required_next_action"],
        "",
    ]
    return "\n".join(lines)


def _check_detail(report, check_name):
    matching = [item for item in report["checks"] if item["name"] == check_name]
    if not matching:
        return "NOT_RUN"
    return "\n".join(f"- {item['status']}: {item['detail']}" for item in matching)


def _required_pair_summary(report):
    ground_truth = report["ground_truth"]
    return (
        f"- pair_count: {ground_truth['pair_count']}\n"
        f"- label_count: {ground_truth['label_count']}\n"
        f"- unknown_count: {ground_truth['unknown_count']}\n"
        f"- not_in_reference_scope_count: {ground_truth['not_in_reference_scope_count']}"
    )


def _issue_lines(issues):
    if not issues:
        return "None"
    return "\n".join(f"- {item['code']}: {item['message']}" for item in issues)


def _status(errors, warnings):
    if errors:
        return "PROVISIONAL_BLOCKED"
    if warnings:
        return "WARNING"
    return "PASS"


def _required_next_action(status):
    if status == "PASS":
        return "Create TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001."
    if status == "WARNING":
        return "Review warnings, then create the isolated Stage 6 benchmark if accepted."
    return "Fix reference deck, deck_profile.json or ground_truth.json before Stage 6 benchmark."


def _add_check(checks, name, status, detail):
    checks.append({"name": name, "status": status, "detail": detail})


def _add_error(errors, code, message, **details):
    item = {"code": code, "message": message}
    item.update(details)
    errors.append(item)


def _add_warning(warnings, code, message, **details):
    item = {"code": code, "message": message}
    item.update(details)
    warnings.append(item)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Stage 6 reference deck and ground truth readiness.")
    parser.add_argument("--fixture", required=True, help="Verified state-first fixture directory.")
    parser.add_argument("--reference-deck-dir", required=True, help="Directory with reference deck images.")
    parser.add_argument("--deck-profile", required=True, help="Path to deck_profile.json.")
    parser.add_argument("--ground-truth", required=True, help="Path to ground_truth.json.")
    parser.add_argument("--output", required=True, help="Directory for preflight_report.json and preflight_report.md.")
    parser.add_argument("--stage5-output", default=DEFAULT_STAGE5_OUTPUT_DIR, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    report = run_preflight(
        fixture_dir=args.fixture,
        reference_deck_dir=args.reference_deck_dir,
        deck_profile_path=args.deck_profile,
        ground_truth_path=args.ground_truth,
        output_dir=args.output,
        stage5_output_dir=args.stage5_output,
    )
    print(json.dumps({"status": report["status"], "required_next_action": report["required_next_action"]}, indent=2))
    return 0 if report["status"] in {"PASS", "WARNING"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
