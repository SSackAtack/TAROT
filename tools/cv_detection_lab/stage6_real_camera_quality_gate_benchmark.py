"""Offline benchmark for the Stage 6 real-camera quality gate."""
from __future__ import annotations

import argparse
import csv
import json
import os

import cv2

from tools.cv_detection_lab.stage6_real_camera_quality_gate import (
    ACCEPT, MANUAL, RETRY, build_quality_gate_overlay, evaluate_quality_gate,
)


KNOWN_BAD_CROPS = {
    "47ba5f4ff2946f7d0c1d",
    "377ce08663f0c7430c6b",
    "c332dd59cef00d668e54",
}
MATRIX_COLUMNS = [
    "sample_id", "category", "expected_behavior", "top1_correct", "known_bad_crop",
    "decision", "reasons", "local_specular_component_ratio", "highlight_occlusion_ratio",
    "usable_detail_ratio", "highlight_pixel_ratio", "confidence_score", "confidence_gap",
]


def run_benchmark(identification_matrix_path, crops_dir, output_dir):
    rows = _read_orb_rows(identification_matrix_path)
    os.makedirs(os.path.join(output_dir, "quality_gate_review_pack"), exist_ok=True)
    results = []
    for row in rows:
        crop = cv2.imread(os.path.join(crops_dir, f"{row['sample_id']}.png"), cv2.IMREAD_COLOR)
        if crop is None:
            raise ValueError(f"Cannot read crop for {row['sample_id']}")
        gate, mask = evaluate_quality_gate(crop, float(row["confidence_score"]), float(row["confidence_gap"]))
        result = {
            "sample_id": row["sample_id"],
            "category": row["category"],
            "expected_behavior": row["expected_behavior"],
            "top1_correct": _bool(row["top1_correct"]),
            "known_bad_crop": row["sample_id"] in KNOWN_BAD_CROPS,
            **gate.to_dict(),
        }
        results.append(result)
        overlay = build_quality_gate_overlay(crop, mask, gate)
        cv2.imwrite(os.path.join(output_dir, "quality_gate_review_pack", f"{row['sample_id']}.png"), overlay)

    known_bad = [row for row in results if row["known_bad_crop"]]
    good = [row for row in results if not row["known_bad_crop"] and row["expected_behavior"] == "identify" and row["top1_correct"]]
    wrong = [row for row in results if row["expected_behavior"] == "reject"]
    accepted_known = [row for row in results if row["expected_behavior"] == "identify" and row["decision"] == ACCEPT]
    summary = {
        "stage": "stage6_real_camera_quality_gate_benchmark",
        "scope": "OFFLINE_BENCHMARK_ONLY",
        "sample_count": len(results),
        "bad_crop_retry_recall": _rate(known_bad, lambda row: row["decision"] in {RETRY, MANUAL}),
        "good_crop_false_retry_rate": _rate(good, lambda row: row["decision"] == RETRY),
        "good_crop_non_accept_rate": _rate(good, lambda row: row["decision"] != ACCEPT),
        "wrong_deck_false_retry_rate": _rate(wrong, lambda row: row["decision"] == RETRY),
        "orb_accuracy_on_accept_subset": _rate(accepted_known, lambda row: row["top1_correct"]),
        "decision_counts": _counts(row["decision"] for row in results),
        "category_decision_counts": _category_counts(results),
        "rows": results,
    }
    _write_outputs(output_dir, summary, results)
    return summary


def _read_orb_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row["method"] == "orb_bfmatcher_ratio_test"]


def _write_outputs(output_dir, summary, rows):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in rows:
            payload = {key: row[key] for key in MATRIX_COLUMNS}
            payload["reasons"] = "|".join(row["reasons"])
            writer.writerow(payload)
    with open(os.path.join(output_dir, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    lines = [
        "# Stage 6 Real-Camera Quality Gate Benchmark", "",
        "Offline-only. No runtime threshold or integration approval.", "",
        f"- bad_crop_retry_recall: `{summary['bad_crop_retry_recall']}`",
        f"- good_crop_false_retry_rate: `{summary['good_crop_false_retry_rate']}`",
        f"- good_crop_non_accept_rate: `{summary['good_crop_non_accept_rate']}`",
        f"- wrong_deck_false_retry_rate: `{summary['wrong_deck_false_retry_rate']}`",
        f"- orb_accuracy_on_accept_subset: `{summary['orb_accuracy_on_accept_subset']}`",
    ]
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    with open(os.path.join(output_dir, "quality_gate_review_pack", "index.json"), "w", encoding="utf-8") as handle:
        json.dump({
            decision: [row["sample_id"] for row in rows if row["decision"] == decision]
            for decision in [ACCEPT, RETRY, MANUAL]
        }, handle, indent=2)


def _rate(rows, predicate):
    return round(sum(bool(predicate(row)) for row in rows) / len(rows), 6) if rows else None


def _counts(values):
    result = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def _category_counts(rows):
    result = {}
    for row in rows:
        result.setdefault(row["category"], {})
        decision = row["decision"]
        result[row["category"]][decision] = result[row["category"]].get(decision, 0) + 1
    return result


def _bool(value):
    return value is True or str(value).lower() == "true"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run offline Stage 6 real-camera quality gate benchmark.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--crops", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    summary = run_benchmark(args.matrix, args.crops, args.output)
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
