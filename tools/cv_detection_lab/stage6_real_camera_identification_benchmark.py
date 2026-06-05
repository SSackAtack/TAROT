"""Offline-only Stage 6 identification benchmark for approved real-camera fixtures."""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_identification_methods import load_reference_deck, run_identification_method
from tools.cv_detection_lab.stage6_real_camera_fixture import load_aggregate, scenario_required_files, session_fingerprint


METHODS = ["orb_bfmatcher_ratio_test", "akaze_bfmatcher"]
MATRIX_COLUMNS = [
    "method", "sample_id", "category", "orientation", "similarity_group",
    "expected_behavior", "expected_card_id", "predicted_card_id", "top1_correct",
    "top3_contains_expected", "confidence_score", "confidence_gap",
    "offline_accepted", "false_accept", "runtime_ms",
]


def extract_card(frame):
    height, width = frame.shape[:2]
    x0, x1 = int(width * 0.10), int(width * 0.90)
    y0, y1 = int(height * 0.12), int(height * 0.90)
    roi = frame[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    candidates = []
    frame_area = float(width * height)
    masks = [
        cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)[1],
        cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY_INV)[1],
        cv2.dilate(cv2.Canny(blurred, 35, 120), np.ones((5, 5), np.uint8), iterations=2),
    ]
    for mask in masks:
        contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            rect = cv2.minAreaRect(contour)
            short, long = sorted(rect[1])
            ratio = short / long if long else 0.0
            if frame_area * 0.004 <= area <= frame_area * 0.12 and 0.42 <= ratio <= 0.85:
                candidates.append((area, rect))
    if not candidates:
        raise ValueError("No card-like central contour found.")
    _area, rect = max(candidates, key=lambda item: item[0])
    box = cv2.boxPoints(rect)
    box[:, 0] += x0
    box[:, 1] += y0
    ordered = _order_points(box.astype(np.float32))
    target = np.array([[0, 0], [199, 0], [199, 329], [0, 329]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(ordered, target)
    return cv2.warpPerspective(frame, matrix, (200, 330))


def run_benchmark(manifest_path, ground_truth_path, reference_dir, deck_profile, output_dir,
                  methods=None, offline_accept_score_threshold=0.08, warmup_runs=1):
    methods = methods or METHODS
    unknown = sorted(set(methods) - set(METHODS))
    if unknown:
        raise ValueError(f"Unknown real-camera validation methods: {unknown}")
    aggregate = load_aggregate(manifest_path, ground_truth_path)
    references = load_reference_deck(reference_dir, deck_profile)
    before = {sample.session_id: session_fingerprint(sample.resolved_session_path) for sample in aggregate.samples}
    os.makedirs(output_dir, exist_ok=True)
    extracted = {sample.sample_id: _load_sample_crop(sample) for sample in aggregate.samples}
    if aggregate.samples and warmup_runs:
        for method in methods:
            for _ in range(warmup_runs):
                run_identification_method(method, extracted[aggregate.samples[0].sample_id], references)

    rows = []
    for method in methods:
        for sample in aggregate.samples:
            label = aggregate.labels[sample.sample_id]
            started = time.perf_counter()
            result = run_identification_method(method, extracted[sample.sample_id], references)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            top_ids = [item["card_id"] for item in result.top_k_candidates]
            expected_id = label["expected_card_id"]
            identify = label["expected_behavior"] == "identify"
            accepted = result.confidence_score >= offline_accept_score_threshold
            rows.append({
                "method": method,
                "sample_id": sample.sample_id,
                "category": sample.category,
                "orientation": label["expected_orientation"],
                "similarity_group": sample.similarity_group,
                "expected_behavior": label["expected_behavior"],
                "expected_card_id": expected_id,
                "predicted_card_id": result.predicted_card_id,
                "top1_correct": bool(identify and result.predicted_card_id == expected_id),
                "top3_contains_expected": bool(identify and expected_id in top_ids),
                "confidence_score": result.confidence_score,
                "confidence_gap": result.confidence_gap,
                "offline_accepted": accepted,
                "false_accept": bool(not identify and accepted),
                "runtime_ms": round(runtime_ms, 3),
            })

    summary = {
        "stage": "stage6_real_camera_identification_benchmark",
        "fixture_id": aggregate.fixture_id,
        "sample_count": len(aggregate.samples),
        "methods": list(methods),
        "offline_accept_score_threshold": offline_accept_score_threshold,
        "offline_threshold_scope": "validation_only_not_runtime_approved",
        "runtime_measurement": "local_proxy",
        "method_summaries": _summaries(rows, ("method",)),
        "category_summaries": _summaries(rows, ("method", "category")),
        "similarity_group_summaries": _summaries(
            [row for row in rows if row["similarity_group"]], ("method", "similarity_group")
        ),
        "rows": rows,
    }
    _write_outputs(output_dir, summary, rows, extracted)
    after = {sample.session_id: session_fingerprint(sample.resolved_session_path) for sample in aggregate.samples}
    if before != after:
        raise RuntimeError("Session content changed while running real-camera benchmark.")
    return summary


def _load_sample_crop(sample):
    analysis_name = next(name for name in scenario_required_files(sample.scenario) if name.startswith("analysis_frame_"))
    path = os.path.join(sample.resolved_session_path, sample.scenario, analysis_name)
    frame = cv2.imread(path, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError(f"Cannot read analysis frame: {path}")
    try:
        return extract_card(frame)
    except ValueError as error:
        raise ValueError(f"{sample.sample_id}: {error}") from error


def _summaries(rows, keys):
    grouped = {}
    for row in rows:
        grouped.setdefault(tuple(row[key] for key in keys), []).append(row)
    result = []
    for values, selected in sorted(grouped.items()):
        known = [row for row in selected if row["expected_behavior"] == "identify"]
        wrong = [row for row in selected if row["expected_behavior"] == "reject"]
        runtimes = [float(row["runtime_ms"]) for row in selected]
        item = dict(zip(keys, values))
        item.update({
            "count": len(selected),
            "accuracy_top1": _rate(known, "top1_correct"),
            "accuracy_top3": _rate(known, "top3_contains_expected"),
            "wrong_deck_false_accept_rate": _rate(wrong, "false_accept"),
            "mean_confidence_gap": round(statistics.fmean(float(row["confidence_gap"]) for row in selected), 6),
            "mean_runtime_ms": round(statistics.fmean(runtimes), 3),
            "p50_runtime_ms": round(float(np.percentile(runtimes, 50)), 3),
            "p95_runtime_ms": round(float(np.percentile(runtimes, 95)), 3),
        })
        result.append(item)
    return result


def _rate(rows, key):
    return round(sum(bool(row[key]) for row in rows) / len(rows), 6) if rows else None


def _order_points(points):
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums, diffs = points.sum(axis=1), np.diff(points, axis=1).reshape(-1)
    ordered[0], ordered[2] = points[np.argmin(sums)], points[np.argmax(sums)]
    ordered[1], ordered[3] = points[np.argmin(diffs)], points[np.argmax(diffs)]
    return ordered


def _write_outputs(output_dir, summary, rows, extracted):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in MATRIX_COLUMNS} for row in rows)
    with open(os.path.join(output_dir, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    lines = [
        "# Stage 6 Real-Camera Identification Benchmark", "",
        "Offline-only benchmark. Thresholds and runtime integration are not approved.", "",
        "| Method | Top1 | Top3 | Wrong-deck FAR | Runtime mean | p95 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary["method_summaries"]:
        lines.append(
            f"| {item['method']} | {_fmt(item['accuracy_top1'])} | {_fmt(item['accuracy_top3'])} | "
            f"{_fmt(item['wrong_deck_false_accept_rate'])} | {item['mean_runtime_ms']:.3f} | {item['p95_runtime_ms']:.3f} |"
        )
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    crop_dir = os.path.join(output_dir, "extracted_crops")
    os.makedirs(crop_dir, exist_ok=True)
    for sample_id, crop in extracted.items():
        cv2.imwrite(os.path.join(crop_dir, f"{sample_id}.png"), crop)


def _fmt(value):
    return "n/a" if value is None else f"{value:.3f}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run offline Stage 6 real-camera identification benchmark.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--reference-deck-dir", required=True)
    parser.add_argument("--deck-profile", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--offline-accept-score-threshold", type=float, default=0.08)
    args = parser.parse_args(argv)
    summary = run_benchmark(
        args.manifest, args.ground_truth, args.reference_deck_dir, args.deck_profile, args.output,
        offline_accept_score_threshold=args.offline_accept_score_threshold,
    )
    print(json.dumps({"method_summaries": summary["method_summaries"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
