"""Stage 6 Card Identification benchmark for the isolated offline CV lab."""
import argparse
import csv
import json
import os
import time

import cv2
import numpy as np

from tools.cv_detection_lab.methods import run_diff_method
from tools.cv_detection_lab.region_methods import run_region_method
from tools.cv_detection_lab.card_localization_methods import run_localization_method
from tools.cv_detection_lab.crop_deskew_methods import run_crop_deskew
from tools.cv_detection_lab.crop_quality_methods import evaluate_crop_quality_suite
from tools.cv_detection_lab.stage5_crop_quality_validation_benchmark import (
    INPUT_STAGE1_METHOD,
    INPUT_STAGE2_METHOD,
    INPUT_STAGE3_METHOD,
    INPUT_STAGE4_CROP_METHOD,
    INPUT_STAGE4_NORMALIZATION,
    PAIR_DEFINITIONS,
    build_fixture_pairs,
)
from tools.cv_detection_lab.stage6_identification_methods import (
    FIRST_WAVE_METHODS,
    load_reference_deck,
    run_identification_method,
)


MATRIX_COLUMNS = [
    "method", "pair", "crop_index", "change_type", "crop_source_frame",
    "crop_quality_status", "identification_readiness_score", "expected_card_id",
    "predicted_card_id", "top1_correct", "top3_contains_expected",
    "confidence_score", "confidence_gap", "ambiguous_match", "runtime_ms", "verdict",
]


def run_benchmark(fixture_dir, reference_deck_dir, deck_profile_path, ground_truth_path, output_dir, methods=None):
    methods = methods or FIRST_WAVE_METHODS
    unknown = sorted(set(methods) - set(FIRST_WAVE_METHODS))
    if unknown:
        raise ValueError(f"Unknown Stage 6 methods: {unknown}")
    references = load_reference_deck(reference_deck_dir, deck_profile_path)
    with open(ground_truth_path, "r", encoding="utf-8-sig") as handle:
        ground_truth = json.load(handle)
    os.makedirs(output_dir, exist_ok=True)

    rows = []
    for pair in build_fixture_pairs(fixture_dir):
        previous = _read_image(pair.previous_path)
        current = _read_image(pair.current_path)
        stage1 = run_diff_method(INPUT_STAGE1_METHOD, previous, current)
        stage2 = run_region_method(INPUT_STAGE2_METHOD, stage1.mask, current)
        source = previous if pair.crop_source_frame == "previous" else current
        stage3 = run_localization_method(INPUT_STAGE3_METHOD, source, stage1.mask, stage2.candidates)
        stage4 = run_crop_deskew(
            INPUT_STAGE4_CROP_METHOD, INPUT_STAGE4_NORMALIZATION, source, stage3.geometries, pair.crop_source_frame
        )
        quality = evaluate_crop_quality_suite(stage4.crops)
        labels = {item["crop_index"]: item for item in ground_truth["pairs"][pair.name]}
        for method in methods:
            pair_results = []
            for index, (crop, quality_result) in enumerate(zip(stage4.crops, quality.results), start=1):
                expected = labels.get(index, {})
                started = time.perf_counter()
                result = run_identification_method(
                    method, crop.normalized_crop, references, quality_result.metrics.identification_readiness_score
                )
                runtime_ms = (time.perf_counter() - started) * 1000.0
                top_ids = [item["card_id"] for item in result.top_k_candidates]
                expected_id = expected.get("expected_card_id")
                row = {
                    "method": method,
                    "pair": pair.name,
                    "crop_index": index,
                    "change_type": pair.change_type,
                    "crop_source_frame": pair.crop_source_frame,
                    "crop_quality_status": quality_result.metrics.crop_quality_status,
                    "identification_readiness_score": quality_result.metrics.identification_readiness_score,
                    "expected_card_id": expected_id,
                    "predicted_card_id": result.predicted_card_id,
                    "top1_correct": result.predicted_card_id == expected_id,
                    "top3_contains_expected": expected_id in top_ids,
                    "confidence_score": result.confidence_score,
                    "confidence_gap": result.confidence_gap,
                    "ambiguous_match": result.ambiguous_match,
                    "runtime_ms": round(runtime_ms, 3),
                    "verdict": "PASS" if result.predicted_card_id == expected_id else ("YELLOW" if expected_id in top_ids else "FAIL"),
                }
                rows.append(row)
                pair_results.append((crop.normalized_crop, row, result))
            _write_pair_debug(output_dir, method, pair.name, pair_results)

    summaries = [_method_summary(method, rows) for method in methods]
    recommended = max(summaries, key=lambda item: (item["accuracy_top1"], item["accuracy_top3"], -item["mean_runtime_ms"]))
    summary = {
        "stage": "stage6_card_identification",
        "fixture_dir": fixture_dir,
        "reference_deck_dir": reference_deck_dir,
        "deck_profile_path": deck_profile_path,
        "ground_truth_path": ground_truth_path,
        "methods_tested": list(methods),
        "label_count": sum(len(items) for items in ground_truth["pairs"].values()),
        "method_summaries": summaries,
        "recommended_method": recommended["method"],
        "recommendation_status": "PROVISIONAL_RECOMMENDED",
        "manual_review_required": True,
        "rows": rows,
    }
    _write_matrix(output_dir, rows)
    _write_json(os.path.join(output_dir, "report.json"), summary)
    _write_markdown(output_dir, summary)
    return summary


def _method_summary(method, rows):
    selected = [row for row in rows if row["method"] == method]
    count = len(selected)
    return {
        "method": method,
        "label_count": count,
        "accuracy_top1": round(sum(bool(row["top1_correct"]) for row in selected) / max(1, count), 6),
        "accuracy_top3": round(sum(bool(row["top3_contains_expected"]) for row in selected) / max(1, count), 6),
        "ambiguous_match_rate": round(sum(bool(row["ambiguous_match"]) for row in selected) / max(1, count), 6),
        "mean_confidence_gap": round(sum(float(row["confidence_gap"]) for row in selected) / max(1, count), 6),
        "mean_runtime_ms": round(sum(float(row["runtime_ms"]) for row in selected) / max(1, count), 3),
    }


def _write_pair_debug(output_dir, method, pair_name, results):
    pair_dir = os.path.join(output_dir, method, pair_name)
    os.makedirs(pair_dir, exist_ok=True)
    for index, (crop, row, result) in enumerate(results, start=1):
        _write_json(os.path.join(pair_dir, f"crop_{index:02d}_candidates.json"), {
            "row": row, "top_k_candidates": result.top_k_candidates, "match_evidence": result.match_evidence,
        })
    if results:
        panels = [_debug_panel(crop, row, result) for crop, row, result in results]
        cv2.imwrite(os.path.join(pair_dir, "identification_debug_sheet.png"), np.hstack(panels))


def _debug_panel(crop, row, result):
    image = cv2.resize(crop, (240, 396), interpolation=cv2.INTER_AREA)
    panel = np.zeros((510, 420, 3), dtype=np.uint8)
    panel[:396, :240] = image
    lines = [
        f"expected: {row['expected_card_id']}",
        f"predicted: {row['predicted_card_id']}",
        f"top1={row['top1_correct']} top3={row['top3_contains_expected']}",
        f"confidence={result.confidence_score:.3f} gap={result.confidence_gap:.3f}",
    ]
    for index, line in enumerate(lines):
        cv2.putText(panel, line, (8, 420 + index * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)
    return panel


def _write_matrix(output_dir, rows):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in MATRIX_COLUMNS} for row in rows)


def _write_markdown(output_dir, summary):
    lines = [
        "# Stage 6 Card Identification Benchmark", "",
        f"Recommended method: `{summary['recommended_method']}`",
        f"Recommendation status: `{summary['recommendation_status']}`", "",
        "| Method | Labels | Top1 | Top3 | Ambiguous | Gap | Runtime ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary["method_summaries"]:
        lines.append(
            f"| {item['method']} | {item['label_count']} | {item['accuracy_top1']:.3f} | "
            f"{item['accuracy_top3']:.3f} | {item['ambiguous_match_rate']:.3f} | "
            f"{item['mean_confidence_gap']:.3f} | {item['mean_runtime_ms']:.3f} |"
        )
    lines.extend(["", "## Limitations", "", "- Wynik jest `PROVISIONAL_RECOMMENDED` i wymaga manual review.", "- Wszystkie realne cropy Stage 5 mają status YELLOW."])
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)


def _read_image(path):
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run isolated Stage 6 card identification benchmark.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--reference-deck-dir", required=True)
    parser.add_argument("--deck-profile", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--methods", nargs="*", default=FIRST_WAVE_METHODS)
    args = parser.parse_args(argv)
    summary = run_benchmark(args.fixture, args.reference_deck_dir, args.deck_profile, args.ground_truth, args.output, args.methods)
    print(json.dumps({"recommended_method": summary["recommended_method"], "method_summaries": summary["method_summaries"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
