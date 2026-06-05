import argparse
import csv
import json
import os
import time
from dataclasses import dataclass

import cv2

from tools.cv_detection_lab.methods import run_diff_method
from tools.cv_detection_lab.region_methods import available_region_methods, run_region_method


INPUT_STAGE1_METHOD = "gray_absdiff_gaussian"

EXPECTED_CANDIDATE_COUNTS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 1,
    "empty_to_three_cards": 3,
    "one_card_to_three_cards": 2,
    "one_card_to_empty": 1,
    "three_cards_to_empty": 3,
}

EXPECTED_ADDED_COUNTS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 1,
    "empty_to_three_cards": 3,
    "one_card_to_three_cards": 2,
    "one_card_to_empty": 0,
    "three_cards_to_empty": 0,
}

EXPECTED_REMOVED_COUNTS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 0,
    "empty_to_three_cards": 0,
    "one_card_to_three_cards": 0,
    "one_card_to_empty": 1,
    "three_cards_to_empty": 3,
}

PAIR_DEFINITIONS = [
    ("empty_to_empty", "empty", "empty", "no_change"),
    ("empty_to_one_card", "empty", "one_card", "added"),
    ("empty_to_three_cards", "empty", "three_cards", "added"),
    ("one_card_to_three_cards", "one_card", "three_cards", "added"),
    ("one_card_to_empty", "one_card", "empty", "removed"),
    ("three_cards_to_empty", "three_cards", "empty", "removed"),
]

SCENARIO_FRAME_NAMES = {
    "empty": "analysis_frame_0.png",
    "one_card": "analysis_frame_1.png",
    "three_cards": "analysis_frame_3.png",
}

MATRIX_COLUMNS = [
    "method",
    "pair",
    "change_type",
    "runtime_ms",
    "candidate_count",
    "expected_candidate_count",
    "candidate_count_delta",
    "added_candidate_count",
    "removed_candidate_count",
    "kept_known_count",
    "unknown_region_count",
    "bbox_area_ratio_avg",
    "mask_area_ratio_avg",
    "foreground_fill_ratio_avg",
    "rectangularity_avg",
    "solidity_avg",
    "extent_avg",
    "edge_density_avg",
    "oversized_bbox_count",
    "split_card_count",
    "merge_card_count",
    "rejected_candidate_count",
    "verdict",
    "verdict_basis",
]


@dataclass(frozen=True)
class FixturePair:
    name: str
    previous_path: str
    current_path: str
    expected_candidate_count: int
    expected_added_count: int
    expected_removed_count: int
    change_type: str


def build_fixture_pairs(fixture_dir):
    pairs = []
    for pair_name, previous_scenario, current_scenario, change_type in PAIR_DEFINITIONS:
        previous_path = _scenario_frame_path(fixture_dir, previous_scenario)
        current_path = _scenario_frame_path(fixture_dir, current_scenario)
        if not os.path.exists(previous_path):
            raise FileNotFoundError(previous_path)
        if not os.path.exists(current_path):
            raise FileNotFoundError(current_path)
        pairs.append(
            FixturePair(
                name=pair_name,
                previous_path=previous_path,
                current_path=current_path,
                expected_candidate_count=EXPECTED_CANDIDATE_COUNTS[pair_name],
                expected_added_count=EXPECTED_ADDED_COUNTS[pair_name],
                expected_removed_count=EXPECTED_REMOVED_COUNTS[pair_name],
                change_type=change_type,
            )
        )
    return pairs


def run_benchmark(fixture_dir, output_dir, method_names=None):
    method_names = method_names or available_region_methods()
    os.makedirs(output_dir, exist_ok=True)
    rows = []
    pairs = build_fixture_pairs(fixture_dir)

    for method_name in method_names:
        for pair in pairs:
            previous = _read_image(pair.previous_path)
            current = _read_image(pair.current_path)
            stage1 = run_diff_method(INPUT_STAGE1_METHOD, previous, current)
            started = time.perf_counter()
            result = run_region_method(method_name, stage1.mask, current)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            row = _build_row(method_name, pair, result, runtime_ms)
            rows.append(row)
            _write_debug_outputs(output_dir, method_name, pair.name, stage1.mask, current, result)

    recommended_method = _choose_recommended_method(rows, method_names)
    summary = {
        "stage": "stage2_region_segmentation",
        "input_stage1_method": INPUT_STAGE1_METHOD,
        "fixture_dir": fixture_dir,
        "methods_tested": list(method_names),
        "rows": rows,
        "recommended_method": recommended_method,
        "recommendation_status": "PROVISIONAL_RECOMMENDED" if recommended_method else "NO_RECOMMENDATION",
        "manual_review_required": True,
        "manual_review_paths": _manual_review_paths(output_dir, recommended_method) if recommended_method else [],
    }
    _write_matrix(output_dir, rows)
    _write_json(os.path.join(output_dir, "report.json"), summary)
    _write_markdown_report(output_dir, summary)
    return summary


def _build_row(method_name, pair, result, runtime_ms):
    candidates = result.candidates
    candidate_count = len(candidates)
    added_count = candidate_count if pair.change_type == "added" else 0
    removed_count = candidate_count if pair.change_type == "removed" else 0
    oversized_count = sum(1 for candidate in candidates if candidate.oversized_bbox_flag)
    split_count = sum(1 for candidate in candidates if candidate.split_card_flag)
    merge_count = sum(1 for candidate in candidates if candidate.merge_card_flag)
    expected = pair.expected_candidate_count
    return {
        "method": method_name,
        "pair": pair.name,
        "change_type": pair.change_type,
        "runtime_ms": round(runtime_ms, 3),
        "candidate_count": candidate_count,
        "expected_candidate_count": expected,
        "candidate_count_delta": candidate_count - expected,
        "added_candidate_count": added_count,
        "removed_candidate_count": removed_count,
        "kept_known_count": 1 if pair.name == "one_card_to_three_cards" else 0,
        "unknown_region_count": 0,
        "bbox_area_ratio_avg": _avg(candidates, "bbox_area_ratio"),
        "mask_area_ratio_avg": _avg(candidates, "mask_area_ratio"),
        "foreground_fill_ratio_avg": _avg(candidates, "foreground_fill_ratio"),
        "rectangularity_avg": _avg(candidates, "rectangularity"),
        "solidity_avg": _avg(candidates, "solidity"),
        "extent_avg": _avg(candidates, "extent"),
        "edge_density_avg": _avg(candidates, "edge_density"),
        "oversized_bbox_count": oversized_count,
        "split_card_count": split_count,
        "merge_card_count": merge_count,
        "rejected_candidate_count": len(result.rejected_candidates),
        "verdict": _verdict(pair, candidate_count, oversized_count, split_count, merge_count),
        "verdict_basis": "candidate_count_and_region_quality_flags",
        "candidates": [candidate.to_dict() for candidate in candidates],
        "rejected_candidates": result.rejected_candidates,
    }


def _verdict(pair, candidate_count, oversized_count, split_count, merge_count):
    expected = pair.expected_candidate_count
    if pair.name == "empty_to_empty":
        return "PASS" if candidate_count == 0 else "FAIL"
    if abs(candidate_count - expected) > 1:
        return "FAIL"
    if candidate_count != expected:
        return "YELLOW"
    if oversized_count > 0 and pair.name in {"empty_to_one_card", "one_card_to_three_cards"}:
        return "YELLOW"
    if split_count > 0 or merge_count > 0:
        return "YELLOW"
    return "PASS"


def _write_debug_outputs(output_dir, method_name, pair_name, stage1_mask, current, result):
    pair_dir = os.path.join(output_dir, method_name, pair_name)
    os.makedirs(pair_dir, exist_ok=True)
    candidate_mask = result.debug_masks.get("candidate_mask", stage1_mask)
    cv2.imwrite(os.path.join(pair_dir, "stage1_mask.png"), stage1_mask)
    cv2.imwrite(os.path.join(pair_dir, "candidate_mask.png"), candidate_mask)
    candidate_overlay = current.copy()
    tightened_overlay = current.copy()
    for candidate in result.candidates:
        x, y, width, height = candidate.bbox
        color = (0, 255, 255) if not candidate.oversized_bbox_flag else (0, 128, 255)
        cv2.rectangle(candidate_overlay, (x, y), (x + width, y + height), color, 2)
        cv2.rectangle(tightened_overlay, (x, y), (x + width, y + height), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(pair_dir, "candidate_overlay.png"), candidate_overlay)
    cv2.imwrite(os.path.join(pair_dir, "tightened_overlay.png"), tightened_overlay)
    _write_json(
        os.path.join(pair_dir, "region_debug.json"),
        {
            "candidates": [candidate.to_dict() for candidate in result.candidates],
            "rejected_candidates": result.rejected_candidates,
        },
    )


def _write_matrix(output_dir, rows):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row[name] for name in MATRIX_COLUMNS})


def _write_markdown_report(output_dir, summary):
    lines = [
        "# Stage 2 Region Segmentation Benchmark",
        "",
        f"Input Stage 1 Method: `{summary['input_stage1_method']}`",
        f"Fixture: `{summary['fixture_dir']}`",
        f"Recommended method: `{summary['recommended_method']}`",
        f"Recommendation status: `{summary['recommendation_status']}`",
        f"Manual review required: `{summary['manual_review_required']}`",
        "",
        "## Matrix summary",
        "",
        "| Method | Pair | Candidates | Expected | Verdict | Oversized | Split | Merge | Runtime ms |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['method']} | {row['pair']} | {row['candidate_count']} | "
            f"{row['expected_candidate_count']} | {row['verdict']} | "
            f"{row['oversized_bbox_count']} | {row['split_card_count']} | "
            f"{row['merge_card_count']} | {row['runtime_ms']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Manual Review Paths",
            "",
            *[f"- `{path}`" for path in summary["manual_review_paths"]],
            "",
            "## Known limitations",
            "",
            "- Wynik jest tylko `PROVISIONAL_RECOMMENDED`.",
            "- Benchmark nie wykonuje cropowania, deskew ani identyfikacji kart.",
            "- Overlaye wymagają ręcznego review Supervisora przed decyzją Stage 2.",
        ]
    )
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _choose_recommended_method(rows, method_names):
    scores = []
    for method_name in method_names:
        method_rows = [row for row in rows if row["method"] == method_name]
        pass_count = sum(1 for row in method_rows if row["verdict"] == "PASS")
        yellow_count = sum(1 for row in method_rows if row["verdict"] == "YELLOW")
        avg_runtime = sum(float(row["runtime_ms"]) for row in method_rows) / max(1, len(method_rows))
        scores.append((pass_count, yellow_count, -avg_runtime, method_name))
    scores.sort(reverse=True)
    return scores[0][3] if scores else None


def _manual_review_paths(output_dir, method_name):
    return [
        os.path.join(output_dir, method_name, pair_name, "candidate_overlay.png").replace("\\", "/")
        for pair_name, _, _, _ in PAIR_DEFINITIONS
    ]


def _avg(candidates, attr):
    if not candidates:
        return 0.0
    return round(sum(float(getattr(candidate, attr)) for candidate in candidates) / float(len(candidates)), 6)


def _scenario_frame_path(fixture_dir, scenario):
    return os.path.join(fixture_dir, scenario, SCENARIO_FRAME_NAMES[scenario])


def _read_image(path):
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Stage 2 offline region segmentation benchmark.")
    parser.add_argument("--fixture", required=True, help="Path to event_first_current_debug_verified fixture directory.")
    parser.add_argument("--output", required=True, help="Output directory under logs/offline_replay.")
    parser.add_argument("--method", action="append", dest="methods", help="Method to run. Can be repeated.")
    args = parser.parse_args(argv)
    summary = run_benchmark(args.fixture, args.output, method_names=args.methods)
    print(json.dumps({"recommended_method": summary["recommended_method"], "rows": len(summary["rows"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
