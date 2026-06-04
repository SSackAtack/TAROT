"""Minimal operator-assisted RWS fixture expansion for Stage 6 offline review."""
from __future__ import annotations

import argparse
import json
import os

from tools.cv_detection_lab.stage6_real_camera_capture_wizard import (
    CaptureStep,
    _run_single_step,
    _sample_already_recorded,
)
from tools.cv_detection_lab.stage6_real_camera_fixture import (
    load_aggregate,
    session_fingerprint,
    stable_sample_id,
)
from tools.cv_detection_lab.stage6_real_camera_manual_review_pack import build_manual_review_pack


FIXTURE_ID = "stage6_real_camera_fixture_expansion_rws_minimal"
SCENARIO = "one_card"


def build_expansion_plan():
    specifications = (
        ("bright_clear", "RWS_00", "upright", "centrum maty, bez celowego odblasku"),
        ("bright_clear", "RWS_17", "reversed", "lewa strona maty, bez celowego odblasku"),
        ("bright_glare", "RWS_06", "upright", "prawa strona maty, ustaw widoczny odblask"),
        ("bright_glare", "RWS_19", "reversed", "centrum maty, ustaw widoczny odblask"),
        ("dark_clear", "RWS_13", "upright", "prawa strona maty, bez celowego odblasku"),
        ("dark_clear", "RWS_15", "reversed", "centrum maty, bez celowego odblasku"),
        ("dark_glare", "RWS_16", "upright", "lewa strona maty, ustaw widoczny odblask"),
        ("dark_glare", "RWS_18", "reversed", "prawa strona maty, ustaw widoczny odblask"),
    )
    steps = []
    for index, (variant, card_id, orientation, placement) in enumerate(specifications, start=1):
        category = f"rws_{variant}"
        steps.append(CaptureStep(
            index=index,
            session_id=f"stage6_expansion_rws_{index:02d}_{variant}",
            category=category,
            deck="rider-waite-smith",
            card_label=card_id,
            expected_card_id=None,
            expected_orientation=orientation,
            expected_behavior="reject",
            quality_expectation="YELLOW" if variant.endswith("glare") else "PASS_OR_YELLOW",
            similarity_group=None,
            operator_instruction=(
                f"Poloz {card_id} ({orientation}), {placement}. "
                "RWS jest wrong-deck dla aktualnej walidacji Gilded."
            ),
        ))
    return tuple(steps)


def run_expansion_preflight(aggregate_dir, output_dir=None):
    manifest_path = os.path.join(aggregate_dir, "manifest.json")
    ground_truth_path = os.path.join(aggregate_dir, "ground_truth.json")
    errors = []
    try:
        aggregate = load_aggregate(manifest_path, ground_truth_path)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return _write_report(output_dir, _report([], [{"code": "INVALID_AGGREGATE", "message": str(exc)}]))

    expected = {step.session_id: step for step in build_expansion_plan()}
    actual = {sample.session_id: sample for sample in aggregate.samples}
    for session_id, step in expected.items():
        sample = actual.get(session_id)
        if sample is None:
            errors.append({"code": "MISSING_EXPANSION_SAMPLE", "session_id": session_id})
            continue
        if sample.sample_id != stable_sample_id(session_id, SCENARIO, step.category):
            errors.append({"code": "UNSTABLE_SAMPLE_ID", "session_id": session_id})
        label = aggregate.labels.get(sample.sample_id, {})
        if label.get("label_status") != "manual_confirmed":
            errors.append({"code": "LABEL_NOT_MANUALLY_CONFIRMED", "session_id": session_id})
        if label.get("expected_behavior") != "reject":
            errors.append({"code": "WRONG_DECK_BEHAVIOR_INVALID", "session_id": session_id})
        if not os.path.isdir(sample.resolved_session_path) or not session_fingerprint(sample.resolved_session_path):
            errors.append({"code": "MISSING_OR_EMPTY_SESSION", "session_id": session_id})
    for session_id in sorted(set(actual) - set(expected)):
        errors.append({"code": "UNEXPECTED_EXPANSION_SAMPLE", "session_id": session_id})
    return _write_report(output_dir, _report(aggregate.samples, errors))


def run_wizard(log_dir, aggregate_dir, output_dir, camera_index=0):
    print("# Stage 6 Minimal RWS Fixture Expansion")
    print("8 zdjec: jasne/ciemne, clear/glare, upright/reversed, rozne pozycje.")
    print("Nie uruchamia benchmarku. Tworzy tylko preflight i manual review pack.")
    plan = build_expansion_plan()
    for step in plan:
        if _sample_already_recorded(step, aggregate_dir):
            print(f"\n[{step.index}/8] {step.session_id} juz zapisane. Pomijam.")
            continue
        session_root = os.path.join(log_dir, "live_fixtures", step.session_id)
        _run_single_step(step, session_root, aggregate_dir, "camera_snapshot", camera_index, log_dir)
    report = run_expansion_preflight(aggregate_dir, output_dir)
    print("\nExpansion preflight:", report["status"])
    if report["status"] == "PASS":
        pack_dir = os.path.join(output_dir, "manual_review_pack")
        build_manual_review_pack(
            os.path.join(aggregate_dir, "manifest.json"),
            os.path.join(aggregate_dir, "ground_truth.json"),
            os.path.join(output_dir, "preflight_report.json"),
            pack_dir,
        )
        print("Manual review pack:", pack_dir)
        print("STOP: nie uruchamiaj benchmarku przed zatwierdzeniem paczki.")


def _report(samples, errors):
    status = "PROVISIONAL_BLOCKED" if errors else "PASS"
    return {
        "stage": "stage6_real_camera_fixture_expansion_preflight",
        "status": status,
        "sample_count": len(samples),
        "errors": errors,
        "warnings": [],
        "required_next_action": (
            "Submit manual review pack for Supervisor approval. Do not run benchmark."
            if status == "PASS"
            else "Collect or correct the eight RWS expansion samples."
        ),
    }


def _write_report(output_dir, report):
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "preflight_report.json"), "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "preflight_report.md"), "w", encoding="utf-8") as handle:
            handle.write(
                "# Stage 6 RWS Fixture Expansion Preflight\n\n"
                f"Status: `{report['status']}`\n\n"
                f"Sample count: `{report['sample_count']}`\n\n"
                "## Errors\n"
                + ("\n".join(f"- {item['code']}" for item in report["errors"]) or "- None")
                + "\n\n## Required Next Action\n"
                + report["required_next_action"]
                + "\n"
            )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Capture the minimal eight-sample RWS expansion pack.")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument(
        "--aggregate-dir",
        default=os.path.join("logs", "live_fixtures", FIXTURE_ID),
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("logs", "offline_replay", FIXTURE_ID),
    )
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--print-plan", action="store_true")
    args = parser.parse_args(argv)
    if args.print_plan:
        for step in build_expansion_plan():
            print(f"{step.index:02d}. {step.card_label} | {step.category} | {step.expected_orientation}")
        return 0
    run_wizard(args.log_dir, args.aggregate_dir, args.output_dir, args.camera_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
