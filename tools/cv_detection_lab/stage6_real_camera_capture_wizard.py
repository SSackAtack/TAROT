"""Operator wizard for Stage 6 real-camera capture.

The wizard is intentionally a manual wrapper around the existing live fixture
capture. It prints the exact environment variables for one immutable session,
waits for the operator to run capture, then records only sessions that already
contain the required files.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os

from tools.cv_detection_lab.stage6_real_camera_fixture import scenario_required_files, stable_sample_id
from tools.cv_detection_lab.stage6_real_camera_manual_review_pack import build_manual_review_pack
from tools.cv_detection_lab.stage6_real_camera_preflight import run_preflight


FIXTURE_ID = "stage6_real_camera_validation"
SCENARIO = "one_card"


@dataclass(frozen=True)
class CaptureStep:
    index: int
    session_id: str
    category: str
    deck: str
    card_label: str
    expected_card_id: str | None
    expected_orientation: str
    expected_behavior: str
    quality_expectation: str
    similarity_group: str | None
    operator_instruction: str


def build_capture_plan():
    steps = []
    cards = [f"Gilded_{index:02d}" for index in range(6)]
    for index, card_id in enumerate(cards, start=1):
        steps.append(_step(
            len(steps) + 1,
            f"stage6_real_gilded_{index:02d}_upright",
            "gilded_upright",
            "gilded",
            card_id,
            card_id,
            "upright",
            "identify",
            "PASS_OR_YELLOW",
            None,
            f"Poloz karte {card_id} z talii Gilded normalnie, awersem do kamery.",
        ))
    for index, card_id in enumerate(cards, start=1):
        steps.append(_step(
            len(steps) + 1,
            f"stage6_real_gilded_{index:02d}_reversed",
            "gilded_reversed",
            "gilded",
            card_id,
            card_id,
            "reversed",
            "identify",
            "PASS_OR_YELLOW",
            None,
            f"Poloz te sama karte {card_id} z talii Gilded odwrocona o 180 stopni.",
        ))
    for index in range(1, 5):
        steps.append(_step(
            len(steps) + 1,
            f"stage6_real_magic_{index:02d}_wrong_deck",
            "wrong_deck_magic",
            "magic",
            f"Magic wrong-deck #{index}",
            None,
            "not_applicable",
            "reject",
            "PASS_OR_YELLOW",
            None,
            "Poloz jedna karte z talii Magic. Oczekiwane zachowanie Stage 6: reject.",
        ))
    for index in range(1, 5):
        steps.append(_step(
            len(steps) + 1,
            f"stage6_real_marchetti_{index:02d}_wrong_deck",
            "wrong_deck_marchetti",
            "marchetti",
            f"Marchetti wrong-deck #{index}",
            None,
            "not_applicable",
            "reject",
            "PASS_OR_YELLOW",
            None,
            "Poloz jedna karte z talii Marchetti. Oczekiwane zachowanie Stage 6: reject.",
        ))
    for index in range(1, 5):
        card_id = f"Gilded_YELLOW_{index:02d}"
        steps.append(_step(
            len(steps) + 1,
            f"stage6_real_gilded_yellow_{index:02d}",
            "gilded_yellow",
            "gilded",
            card_id,
            card_id,
            "upright",
            "identify",
            "YELLOW",
            None,
            "Poloz trudna karte Gilded, ktora realnie daje status Stage 5 YELLOW.",
        ))
    for group_index in range(1, 3):
        for card_index in range(1, 3):
            card_id = f"Gilded_SIM_{group_index:02d}_{card_index:02d}"
            steps.append(_step(
                len(steps) + 1,
                f"stage6_real_gilded_similar_g{group_index:02d}_c{card_index:02d}",
                "gilded_visually_similar",
                "gilded",
                card_id,
                card_id,
                "upright",
                "identify",
                "PASS_OR_YELLOW",
                f"similar-{group_index}",
                "Poloz karte Gilded z grupy wizualnie podobnej wskazanej przez operatora.",
            ))
    return tuple(steps)


def expected_env_commands(step):
    return "\n".join([
        '$env:TAROTVISION_CAPTURE_LIVE_FIXTURES = "1"',
        f'$env:TAROTVISION_LIVE_FIXTURE_NAME = "{step.session_id}"',
        '$env:TAROTVISION_LIVE_FIXTURE_SCENARIO = "one_card"',
    ])


def append_confirmed_sample(step, session_root, aggregate_dir):
    missing = _missing_required_files(session_root, SCENARIO)
    if missing:
        raise ValueError("missing required capture files: " + ", ".join(missing))

    os.makedirs(aggregate_dir, exist_ok=True)
    manifest_path = os.path.join(aggregate_dir, "manifest.json")
    ground_truth_path = os.path.join(aggregate_dir, "ground_truth.json")
    manifest = _read_json(manifest_path, _empty_manifest())
    ground_truth = _read_json(ground_truth_path, _empty_ground_truth())

    sample_id = stable_sample_id(step.session_id, SCENARIO, step.category)
    if any(item.get("sample_id") == sample_id for item in manifest["samples"]):
        return {"status": "ALREADY_RECORDED", "sample_id": sample_id}

    sample = {
        "sample_id": sample_id,
        "session_id": step.session_id,
        "session_path": os.path.relpath(os.path.abspath(session_root), aggregate_dir),
        "scenario": SCENARIO,
        "category": step.category,
        "expected_deck": step.deck,
        "expected_card_id": step.expected_card_id,
        "expected_orientation": step.expected_orientation,
        "expected_behavior": step.expected_behavior,
        "quality_expectation": step.quality_expectation,
        "similarity_group": step.similarity_group,
        "notes": step.operator_instruction,
    }
    manifest["samples"].append(sample)
    ground_truth["labels"][sample_id] = {
        "sample_id": sample_id,
        "expected_deck": step.deck,
        "expected_card_id": step.expected_card_id,
        "expected_orientation": step.expected_orientation,
        "expected_behavior": step.expected_behavior,
        "label_status": "manual_confirmed",
        "notes": step.operator_instruction,
    }
    _write_json(manifest_path, manifest)
    _write_json(ground_truth_path, ground_truth)
    return {"status": "RECORDED", "sample_id": sample_id}


def run_wizard(log_dir, aggregate_dir, output_dir):
    _print_header()
    _wait("Ustaw kamere, ostrosc i ekspozycje. Upewnij sie, ze widzisz wszystkie markery ArUco.")
    _wait("Potwierdz, ze mata jest pusta i stabilna. Wykonaj testowy podglad w Studio, jesli trzeba.")
    plan = build_capture_plan()
    for step in plan:
        if _sample_already_recorded(step, aggregate_dir):
            print(f"\n[{step.index}/28] {step.session_id} jest juz w agregacie. Pomijam.")
            continue
        session_root = os.path.join(log_dir, "live_fixtures", step.session_id)
        _run_single_step(step, session_root, aggregate_dir)
    _run_final_validation(aggregate_dir, output_dir)


def _run_single_step(step, session_root, aggregate_dir):
    print("\n" + "=" * 72)
    print(f"KROK {step.index}/28: {step.category}")
    print(f"Sesja: {step.session_id}")
    print(f"Talia: {step.deck}")
    print(f"Karta: {step.card_label}")
    print(f"Orientacja: {step.expected_orientation}")
    print(f"Instrukcja: {step.operator_instruction}")
    print("\nUstaw te zmienne w terminalu backendu przed capture:")
    print(expected_env_commands(step))
    _wait("Poloz karte zgodnie z instrukcja. Gdy jest stabilnie, uruchom istniejacy capture i poczekaj na zapis snapshotu.")
    while True:
        if not _missing_required_files(session_root, SCENARIO):
            break
        print("\nNie widze kompletu plikow sesji:")
        print(session_root)
        print("Wymagane: " + ", ".join(scenario_required_files(SCENARIO)))
        answer = input("Nacisnij Enter po ponownym capture albo wpisz skip, aby pominac ten krok: ").strip().lower()
        if answer == "skip":
            return
    _wait("Sprawdz wizualnie analysis_frame_1.png i raw_frame_1.png. Enter oznacza reczne potwierdzenie etykiety.")
    result = append_confirmed_sample(step, session_root, aggregate_dir)
    print(f"Zapisano: {result['status']} / {result['sample_id']}")


def _run_final_validation(aggregate_dir, output_dir):
    manifest_path = os.path.join(aggregate_dir, "manifest.json")
    ground_truth_path = os.path.join(aggregate_dir, "ground_truth.json")
    report = run_preflight(manifest_path, ground_truth_path, output_dir)
    print("\nPreflight:", report["status"])
    print(report["required_next_action"])
    if report["status"] == "PASS":
        pack_dir = os.path.join(output_dir, "manual_review_pack")
        build_manual_review_pack(
            manifest_path,
            ground_truth_path,
            os.path.join(output_dir, "preflight_report.json"),
            pack_dir,
        )
        print("Manual review pack:", pack_dir)


def _missing_required_files(session_root, scenario):
    scenario_dir = os.path.join(session_root, scenario)
    return [
        name
        for name in scenario_required_files(scenario)
        if not os.path.isfile(os.path.join(scenario_dir, name))
    ]


def _sample_already_recorded(step, aggregate_dir):
    manifest_path = os.path.join(aggregate_dir, "manifest.json")
    manifest = _read_json(manifest_path, _empty_manifest())
    sample_id = stable_sample_id(step.session_id, SCENARIO, step.category)
    return any(item.get("sample_id") == sample_id for item in manifest.get("samples", []))


def _step(
    index,
    session_id,
    category,
    deck,
    card_label,
    expected_card_id,
    expected_orientation,
    expected_behavior,
    quality_expectation,
    similarity_group,
    operator_instruction,
):
    return CaptureStep(
        index=index,
        session_id=session_id,
        category=category,
        deck=deck,
        card_label=card_label,
        expected_card_id=expected_card_id,
        expected_orientation=expected_orientation,
        expected_behavior=expected_behavior,
        quality_expectation=quality_expectation,
        similarity_group=similarity_group,
        operator_instruction=operator_instruction,
    )


def _empty_manifest():
    return {
        "fixture_id": FIXTURE_ID,
        "manifest_version": 1,
        "capture_policy": "immutable_sessions",
        "samples": [],
    }


def _empty_ground_truth():
    return {"fixture_id": FIXTURE_ID, "labels": {}}


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _wait(message):
    input("\n" + message + "\nNacisnij Enter, aby kontynuowac: ")


def _print_header():
    print("# Stage 6 Real-Camera Capture Wizard")
    print("Tryb: manualny, bez zmian runtime i bez automatycznego startu backendu.")
    print("Jedna sesja capture = jedna probka agregatu.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manual wizard for Stage 6 real-camera capture.")
    parser.add_argument("--log-dir", default="logs", help="Directory containing live_fixtures.")
    parser.add_argument(
        "--aggregate-dir",
        default=os.path.join("logs", "live_fixtures", FIXTURE_ID),
        help="Aggregate manifest/ground_truth directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("logs", "offline_replay", FIXTURE_ID),
        help="Preflight and manual review pack output directory.",
    )
    parser.add_argument("--print-plan", action="store_true", help="Print the 28-step plan and exit.")
    args = parser.parse_args(argv)
    if args.print_plan:
        for step in build_capture_plan():
            print(f"{step.index:02d}. {step.session_id} | {step.category} | {step.card_label}")
        return 0
    run_wizard(args.log_dir, args.aggregate_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
