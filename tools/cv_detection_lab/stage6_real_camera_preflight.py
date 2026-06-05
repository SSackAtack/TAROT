"""Offline preflight for Stage 6 real-camera aggregate fixtures."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os

from tools.cv_detection_lab.stage6_real_camera_fixture import (
    load_aggregate,
    scenario_required_files,
    session_fingerprint,
    stable_sample_id,
)


REQUIRED_MINIMUMS = {
    "gilded_upright": 6,
    "gilded_reversed": 6,
    "wrong_deck_magic": 4,
    "wrong_deck_marchetti": 4,
    "gilded_yellow": 4,
    "gilded_visually_similar": 4,
}
PLACEHOLDER_PREFIXES = ("Gilded_YELLOW_", "Gilded_SIM_")


def run_preflight(manifest_path, ground_truth_path, output_dir=None):
    errors = []
    warnings = []
    try:
        aggregate = load_aggregate(manifest_path, ground_truth_path)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        report = _report("PROVISIONAL_BLOCKED", [], [{"code": "INVALID_AGGREGATE", "message": str(exc)}], [])
        return _write_if_requested(output_dir, report)

    before = {sample.session_id: session_fingerprint(sample.resolved_session_path) for sample in aggregate.samples}
    sample_ids = [sample.sample_id for sample in aggregate.samples]
    session_ids = [sample.session_id for sample in aggregate.samples]
    _duplicate_errors(sample_ids, "DUPLICATE_SAMPLE_ID", errors)
    _duplicate_errors(session_ids, "DUPLICATE_SESSION_REFERENCE", errors)

    category_counts = Counter(sample.category for sample in aggregate.samples)
    for category, minimum in REQUIRED_MINIMUMS.items():
        if category_counts[category] < minimum:
            _error(errors, "MINIMUM_CATEGORY_COUNT_NOT_MET", category=category, expected=minimum, actual=category_counts[category])
    if len(aggregate.samples) < 28:
        _error(errors, "MINIMUM_SAMPLE_COUNT_NOT_MET", expected=28, actual=len(aggregate.samples))

    labels = aggregate.labels
    if set(labels) != set(sample_ids):
        _error(errors, "MANIFEST_GROUND_TRUTH_MISMATCH")

    similarity_groups = defaultdict(int)
    for sample in aggregate.samples:
        if sample.sample_id != stable_sample_id(sample.session_id, sample.scenario, sample.category):
            _error(errors, "UNSTABLE_SAMPLE_ID", sample_id=sample.sample_id)
        _validate_session(sample, errors)
        label = labels.get(sample.sample_id)
        if not isinstance(label, dict):
            continue
        if label.get("label_status") != "manual_confirmed":
            _error(errors, "LABEL_NOT_MANUALLY_CONFIRMED", sample_id=sample.sample_id)
        for field in ("expected_deck", "expected_card_id", "expected_orientation", "expected_behavior"):
            if label.get(field) != getattr(sample, field):
                _error(
                    errors,
                    "GROUND_TRUTH_LABEL_MISMATCH",
                    sample_id=sample.sample_id,
                    field=field,
                    manifest_value=getattr(sample, field),
                    ground_truth_value=label.get(field),
                )
        _validate_expected_card_id(sample, label, errors)
        if sample.category.startswith("wrong_deck") and label.get("expected_behavior") != "reject":
            _error(errors, "WRONG_DECK_BEHAVIOR_INVALID", sample_id=sample.sample_id)
        if sample.category == "gilded_reversed" and label.get("expected_orientation") != "reversed":
            _error(errors, "REVERSED_ORIENTATION_INVALID", sample_id=sample.sample_id)
        if sample.category == "gilded_visually_similar":
            similarity_groups[sample.similarity_group] += 1

    if len([count for count in similarity_groups.values() if count >= 2]) < 2:
        _error(errors, "VISUALLY_SIMILAR_GROUPS_INCOMPLETE")

    after = {sample.session_id: session_fingerprint(sample.resolved_session_path) for sample in aggregate.samples}
    if before != after:
        _error(errors, "SESSION_MUTATED_DURING_PREFLIGHT")
    status = "PROVISIONAL_BLOCKED" if errors else ("WARNING" if warnings else "PASS")
    report = _report(status, aggregate.samples, errors, warnings)
    return _write_if_requested(output_dir, report)


def _validate_session(sample, errors):
    if not os.path.isdir(sample.resolved_session_path):
        _error(errors, "MISSING_SESSION", sample_id=sample.sample_id, path=sample.resolved_session_path)
        return
    scenario_dir = os.path.join(sample.resolved_session_path, sample.scenario)
    if not os.path.isdir(scenario_dir):
        _error(errors, "MISSING_SCENARIO", sample_id=sample.sample_id, path=scenario_dir)
        return
    for name in scenario_required_files(sample.scenario):
        path = os.path.join(scenario_dir, name)
        if not os.path.isfile(path):
            _error(errors, "MISSING_CAPTURE_FILE", sample_id=sample.sample_id, path=path)


def _validate_expected_card_id(sample, label, errors):
    card_id = label.get("expected_card_id")
    if isinstance(card_id, str) and card_id.startswith(PLACEHOLDER_PREFIXES):
        _error(errors, "INVALID_EXPECTED_CARD_ID_PLACEHOLDER", sample_id=sample.sample_id, expected_card_id=card_id)
    if sample.expected_behavior == "identify" and sample.expected_deck == "gilded":
        if not isinstance(card_id, str) or not card_id.startswith("Gilded_") or not card_id[7:].isdigit():
            _error(errors, "INVALID_EXPECTED_CARD_ID_FORMAT", sample_id=sample.sample_id, expected_card_id=card_id)


def _duplicate_errors(values, code, errors):
    for value, count in Counter(values).items():
        if count > 1:
            _error(errors, code, value=value, count=count)


def _error(errors, code, **details):
    item = {"code": code}
    item.update(details)
    errors.append(item)


def _report(status, samples, errors, warnings):
    return {
        "stage": "stage6_real_camera_fixture_preflight",
        "status": status,
        "sample_count": len(samples),
        "errors": errors,
        "warnings": warnings,
        "required_next_action": (
            "Generate manual review pack."
            if status == "PASS"
            else "Collect or correct immutable real-camera sessions and manually confirmed ground truth."
        ),
    }


def _write_if_requested(output_dir, report):
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "preflight_report.json"), "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "preflight_report.md"), "w", encoding="utf-8") as handle:
            handle.write(_markdown(report))
    return report


def _markdown(report):
    lines = ["# Stage 6 Real-Camera Fixture Preflight", "", f"Status: `{report['status']}`", "", "## Errors"]
    if report["errors"]:
        lines.extend(f"- {item['code']}" for item in report["errors"])
    else:
        lines.append("- None")
    lines.extend(["", "## Required Next Action", report["required_next_action"], ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Stage 6 real-camera aggregate fixture.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = run_preflight(args.manifest, args.ground_truth, args.output)
    print(json.dumps({"status": report["status"], "required_next_action": report["required_next_action"]}, indent=2))
    return 0 if report["status"] in {"PASS", "WARNING"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
