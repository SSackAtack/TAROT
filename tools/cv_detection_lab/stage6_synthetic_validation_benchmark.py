"""Synthetic Stage 6 validation benchmark isolated from runtime."""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import statistics
import time

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_identification_methods import (
    ReferenceCard,
    load_reference_deck,
    run_identification_method,
)
from tools.cv_detection_lab.stage6_synthetic_dataset import (
    build_validation_samples,
    render_sample,
    samples_manifest,
)


VALIDATION_METHODS = ["orb_bfmatcher_ratio_test", "akaze_bfmatcher"]
MATRIX_COLUMNS = [
    "method", "sample_id", "source_deck", "source_card_id", "is_known",
    "category", "orientation", "expected_card_id", "predicted_card_id",
    "top1_correct", "top3_contains_expected", "confidence_score", "confidence_gap",
    "offline_accepted", "false_accept", "runtime_ms",
]


def run_validation(samples, references, output_dir, methods=None, offline_accept_score_threshold=0.08, warmup_runs=1, seed=6042026):
    methods = methods or VALIDATION_METHODS
    unknown = sorted(set(methods) - set(VALIDATION_METHODS))
    if unknown:
        raise ValueError(f"Unknown validation methods: {unknown}")
    os.makedirs(output_dir, exist_ok=True)
    rendered = {sample.sample_id: render_sample(sample) for sample in samples}
    if samples and warmup_runs:
        for method in methods:
            for _ in range(warmup_runs):
                run_identification_method(method, rendered[samples[0].sample_id], references)

    rows = []
    debug_entries = {}
    for method in methods:
        for sample in samples:
            image = rendered[sample.sample_id]
            started = time.perf_counter()
            result = run_identification_method(method, image, references)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            top_ids = [item["card_id"] for item in result.top_k_candidates]
            accepted = result.confidence_score >= offline_accept_score_threshold
            row = {
                "method": method,
                "sample_id": sample.sample_id,
                "source_deck": sample.source_deck,
                "source_card_id": sample.source_card_id,
                "is_known": sample.is_known,
                "category": sample.category,
                "orientation": sample.orientation,
                "expected_card_id": sample.expected_card_id,
                "predicted_card_id": result.predicted_card_id,
                "top1_correct": bool(sample.is_known and result.predicted_card_id == sample.expected_card_id),
                "top3_contains_expected": bool(sample.is_known and sample.expected_card_id in top_ids),
                "confidence_score": result.confidence_score,
                "confidence_gap": result.confidence_gap,
                "offline_accepted": accepted,
                "false_accept": bool(not sample.is_known and accepted),
                "runtime_ms": round(runtime_ms, 3),
            }
            rows.append(row)
            audit_group = _audit_group(sample)
            if audit_group and audit_group not in debug_entries:
                debug_entries[audit_group] = (image, row)

    summary = {
        "stage": "stage6_synthetic_validation_benchmark",
        "seed": seed,
        "sample_count": len(samples),
        "known_sample_count": sum(sample.is_known for sample in samples),
        "wrong_deck_sample_count": sum(not sample.is_known for sample in samples),
        "methods": list(methods),
        "offline_accept_score_threshold": offline_accept_score_threshold,
        "offline_threshold_scope": "validation_only_not_runtime_approved",
        "runtime_measurement": "local_proxy",
        "method_summaries": _group_summaries(rows, ("method",)),
        "category_summaries": _group_summaries(rows, ("method", "category")),
        "category_orientation_summaries": _group_summaries(rows, ("method", "category", "orientation")),
        "rows": rows,
    }
    _write_json(os.path.join(output_dir, "manifest.json"), {
        "seed": seed,
        "known_categories": sorted({sample.category for sample in samples if sample.is_known}),
        "samples": samples_manifest(samples),
    })
    _write_matrix(output_dir, rows)
    _write_json(os.path.join(output_dir, "report.json"), summary)
    _write_markdown(output_dir, summary)
    _write_debug_sheets(output_dir, debug_entries)
    return summary


def _group_summaries(rows, group_keys):
    grouped = {}
    for row in rows:
        key = tuple(row[name] for name in group_keys)
        grouped.setdefault(key, []).append(row)
    summaries = []
    for key, selected in sorted(grouped.items()):
        known = [row for row in selected if row["is_known"]]
        wrong = [row for row in selected if not row["is_known"]]
        runtimes = [float(row["runtime_ms"]) for row in selected]
        item = {name: value for name, value in zip(group_keys, key)}
        item.update({
            "count": len(selected),
            "known_count": len(known),
            "wrong_deck_count": len(wrong),
            "accuracy_top1": _rate(known, "top1_correct"),
            "accuracy_top3": _rate(known, "top3_contains_expected"),
            "wrong_deck_false_accept_rate": _rate(wrong, "false_accept"),
            "mean_confidence_gap": round(statistics.fmean(float(row["confidence_gap"]) for row in selected), 6),
            "mean_runtime_ms": round(statistics.fmean(runtimes), 3),
            "p50_runtime_ms": round(float(np.percentile(runtimes, 50)), 3),
            "p95_runtime_ms": round(float(np.percentile(runtimes, 95)), 3),
        })
        summaries.append(item)
    return summaries


def _rate(rows, key):
    return round(sum(bool(row[key]) for row in rows) / len(rows), 6) if rows else None


def _audit_group(sample):
    if not sample.is_known:
        return "wrong_deck"
    if sample.category == "reversed_clean":
        return "reversed"
    if sample.category == "yellow_combined":
        return "yellow_combined"
    if sample.category == "upright_clean":
        return "upright"
    return None


def _write_matrix(output_dir, rows):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in MATRIX_COLUMNS} for row in rows)


def _write_markdown(output_dir, summary):
    lines = [
        "# Stage 6 Synthetic Validation Benchmark", "",
        "Runtime measurements are a local proxy, not a direct HP EliteBook 830 G6 measurement.",
        "Offline acceptance threshold is validation-only and is not approved for runtime.", "",
        f"Samples: {summary['sample_count']} ({summary['known_sample_count']} known, {summary['wrong_deck_sample_count']} wrong deck)",
        f"Offline-only acceptance threshold: `{summary['offline_accept_score_threshold']}`", "",
        "| Method | Top1 | Top3 | Wrong-deck FAR | Gap | Runtime mean | p50 | p95 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary["method_summaries"]:
        lines.append(
            f"| {item['method']} | {_fmt(item['accuracy_top1'])} | {_fmt(item['accuracy_top3'])} | "
            f"{_fmt(item['wrong_deck_false_accept_rate'])} | {item['mean_confidence_gap']:.3f} | "
            f"{item['mean_runtime_ms']:.3f} | {item['p50_runtime_ms']:.3f} | {item['p95_runtime_ms']:.3f} |"
        )
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _fmt(value):
    return "n/a" if value is None else f"{value:.3f}"


def _write_debug_sheets(output_dir, entries):
    debug_dir = os.path.join(output_dir, "debug")
    os.makedirs(debug_dir, exist_ok=True)
    for name, (image, row) in entries.items():
        panel = np.zeros((540, 620, 3), dtype=np.uint8)
        resized = cv2.resize(image, (240, 396), interpolation=cv2.INTER_AREA)
        panel[:396, :240] = resized
        lines = [
            f"sample: {row['sample_id']}",
            f"category: {row['category']}",
            f"orientation: {row['orientation']}",
            f"expected: {row['expected_card_id'] or 'UNKNOWN'}",
            f"predicted: {row['predicted_card_id']}",
            f"score={row['confidence_score']:.3f} gap={row['confidence_gap']:.3f}",
        ]
        for index, line in enumerate(lines):
            cv2.putText(panel, line, (255, 55 + index * 45), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (225, 225, 225), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(debug_dir, f"{name}_debug_sheet.png"), panel)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def load_reference_directory(directory, deck_name):
    references = []
    for path in sorted(glob.glob(os.path.join(directory, "*.jpg"))):
        card_id = os.path.splitext(os.path.basename(path))[0]
        if card_id.lower().endswith("_back"):
            continue
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Cannot read wrong-deck reference image: {path}")
        references.append(ReferenceCard(card_id, card_id, path, image))
    if not references:
        raise ValueError(f"No reference cards found for {deck_name}: {directory}")
    return references


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run isolated Stage 6 synthetic validation benchmark.")
    parser.add_argument("--gilded-reference-dir", required=True)
    parser.add_argument("--gilded-deck-profile", required=True)
    parser.add_argument("--wrong-deck-dir", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=6042026)
    parser.add_argument("--offline-accept-score-threshold", type=float, default=0.08)
    args = parser.parse_args(argv)

    references = load_reference_deck(args.gilded_reference_dir, args.gilded_deck_profile)
    wrong_decks = {}
    for directory in args.wrong_deck_dir:
        deck_name = os.path.basename(os.path.dirname(os.path.dirname(directory))).capitalize()
        wrong_decks[deck_name] = load_reference_directory(directory, deck_name)
    samples = build_validation_samples(references, wrong_decks, args.seed)
    summary = run_validation(
        samples, references, args.output,
        offline_accept_score_threshold=args.offline_accept_score_threshold,
        seed=args.seed,
    )
    print(json.dumps({"method_summaries": summary["method_summaries"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
