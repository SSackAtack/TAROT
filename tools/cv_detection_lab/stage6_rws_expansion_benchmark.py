"""Offline-only Stage 6 RWS expansion benchmark."""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import time
import numpy as np
import cv2

from tools.cv_detection_lab.stage6_identification_methods import ReferenceCard, run_identification_method
from tools.cv_detection_lab.stage6_real_camera_quality_gate import (
    evaluate_quality_gate,
    build_quality_gate_overlay,
    ACCEPT,
    MANUAL,
    RETRY,
)
from tools.cv_detection_lab.stage6_real_camera_fixture import load_aggregate, scenario_required_files


MATRIX_COLUMNS = [
    "sample_id",
    "category",
    "expected_card_id",
    "expected_orientation",
    "quality_expectation",
    "quality_gate_decision",
    "quality_gate_reasons",
    "predicted_card_id",
    "top1_correct",
    "top3_contains_expected",
    "confidence_score",
    "confidence_gap",
    "runtime_ms",
    "extracted_ok",
]


def _order_points(points):
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums, diffs = points.sum(axis=1), np.diff(points, axis=1).reshape(-1)
    ordered[0], ordered[2] = points[np.argmin(sums)], points[np.argmax(sums)]
    ordered[1], ordered[3] = points[np.argmin(diffs)], points[np.argmax(diffs)]
    return ordered


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


def _load_rws_references(reference_deck_dir):
    references = []
    for i in range(78):
        card_id = f"RWS_{i:02d}"
        image_name = f"{card_id}.jpg"
        image_path = os.path.join(reference_deck_dir, image_name)
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Cannot read reference card: {image_path}")
        references.append(ReferenceCard(card_id=card_id, card_name=card_id, image_path=image_path, image=image))
    return references


def run_rws_benchmark(manifest_path, ground_truth_path, reference_deck_dir, output_dir):
    # 1. First Checks
    if not os.path.exists(manifest_path) or not os.path.exists(ground_truth_path):
        print("PROVISIONAL_BLOCKED")
        print("BLOCKED_BY_MISSING_LOCAL_FIXTURE")
        sys.exit(2)

    if not os.path.exists(reference_deck_dir) or not os.path.isdir(reference_deck_dir):
        print("PROVISIONAL_BLOCKED")
        print("BLOCKED_BY_MISSING_RWS_REFERENCES")
        sys.exit(3)

    ref_jpgs = [f for f in os.listdir(reference_deck_dir) if f.startswith("RWS_") and f.endswith(".jpg")]
    if len(ref_jpgs) < 78:
        print("PROVISIONAL_BLOCKED")
        print("BLOCKED_BY_MISSING_RWS_REFERENCES")
        sys.exit(3)

    try:
        aggregate = load_aggregate(manifest_path, ground_truth_path)
    except Exception as exc:
        print("PROVISIONAL_BLOCKED")
        print(f"INVALID_FIXTURE: {exc}")
        sys.exit(4)

    if aggregate.fixture_id != "stage6_real_camera_fixture_expansion_rws_minimal":
        print("PROVISIONAL_BLOCKED")
        print(f"INVALID_FIXTURE_ID: expected stage6_real_camera_fixture_expansion_rws_minimal, got {aggregate.fixture_id}")
        sys.exit(4)

    if len(aggregate.samples) != 8:
        print("PROVISIONAL_BLOCKED")
        print(f"INVALID_SAMPLE_COUNT: expected 8, got {len(aggregate.samples)}")
        sys.exit(4)

    for sample in aggregate.samples:
        if sample.expected_deck != "rider-waite-smith" or sample.expected_behavior != "identify":
            print("PROVISIONAL_BLOCKED")
            print("INVALID_SAMPLE_CONTRACT")
            sys.exit(4)

    # 2. Loading RWS References
    try:
        references = _load_rws_references(reference_deck_dir)
    except ValueError as exc:
        print("PROVISIONAL_BLOCKED")
        print(f"BLOCKED_BY_MISSING_RWS_REFERENCES: {exc}")
        sys.exit(3)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "extracted_crops"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "quality_gate_review_pack"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "error_review_pack"), exist_ok=True)

    results = []
    runtimes = []

    for sample in aggregate.samples:
        label = aggregate.labels.get(sample.sample_id, {})
        analysis_name = next(
            name for name in scenario_required_files(sample.scenario) if name.startswith("analysis_frame_")
        )
        frame_path = os.path.join(sample.resolved_session_path, sample.scenario, analysis_name)
        frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(f"Cannot read frame {frame_path} for sample {sample.sample_id}")

        extracted_ok = True
        try:
            crop = extract_card(frame)
            cv2.imwrite(os.path.join(output_dir, "extracted_crops", f"{sample.sample_id}.png"), crop)
        except Exception as exc:
            extracted_ok = False
            crop = np.zeros((330, 200, 3), dtype=np.uint8)

        # Identification
        started = time.perf_counter()
        id_res = run_identification_method("orb_bfmatcher_ratio_test", crop, references)
        runtime_ms = (time.perf_counter() - started) * 1000.0
        runtimes.append(runtime_ms)

        # Quality Gate
        gate_res, highlight_mask = evaluate_quality_gate(
            crop, confidence_score=id_res.confidence_score, confidence_gap=id_res.confidence_gap
        )

        # Overlay image
        overlay = build_quality_gate_overlay(crop, highlight_mask, gate_res)
        cv2.imwrite(os.path.join(output_dir, "quality_gate_review_pack", f"{sample.sample_id}.png"), overlay)

        expected_id = sample.expected_card_id
        top_ids = [item["card_id"] for item in id_res.top_k_candidates]

        result = {
            "sample_id": sample.sample_id,
            "category": sample.category,
            "expected_card_id": expected_id,
            "expected_orientation": sample.expected_orientation,
            "quality_expectation": sample.quality_expectation,
            "quality_gate_decision": gate_res.decision,
            "quality_gate_reasons": gate_res.reasons,
            "predicted_card_id": id_res.predicted_card_id,
            "top1_correct": bool(id_res.predicted_card_id == expected_id),
            "top3_contains_expected": bool(expected_id in top_ids),
            "confidence_score": id_res.confidence_score,
            "confidence_gap": id_res.confidence_gap,
            "runtime_ms": round(runtime_ms, 3),
            "extracted_ok": extracted_ok,
        }

        # If Top-1 is incorrect and sample is ACCEPTED, save to error review pack
        if not result["top1_correct"] and gate_res.decision == ACCEPT:
            cv2.imwrite(os.path.join(output_dir, "error_review_pack", f"{sample.sample_id}.png"), crop)

        results.append(result)

    # 3. Calculate Metrics
    sample_count = len(results)
    processed_count = sum(1 for r in results if r["extracted_ok"])
    
    orb_top1_all = sum(1 for r in results if r["top1_correct"]) / sample_count
    orb_top3_all = sum(1 for r in results if r["top3_contains_expected"]) / sample_count

    accept_subset = [r for r in results if r["quality_gate_decision"] == ACCEPT]
    accept_count = len(accept_subset)
    retry_capture_count = sum(1 for r in results if r["quality_gate_decision"] == RETRY)
    manual_review_count = sum(1 for r in results if r["quality_gate_decision"] == MANUAL)

    orb_top1_accept = (sum(1 for r in accept_subset if r["top1_correct"]) / accept_count) if accept_count > 0 else None
    orb_top3_accept = (sum(1 for r in accept_subset if r["top3_contains_expected"]) / accept_count) if accept_count > 0 else None

    # Group metrics helpers
    def get_group_metrics(subset):
        if not subset:
            return None
        sub_accept = [r for r in subset if r["quality_gate_decision"] == ACCEPT]
        sub_accept_count = len(sub_accept)
        acc_top1 = (sum(1 for r in sub_accept if r["top1_correct"]) / sub_accept_count) if sub_accept_count > 0 else None
        return {
            "count": len(subset),
            "orb_top1_accuracy": sum(1 for r in subset if r["top1_correct"]) / len(subset),
            "orb_top3_accuracy": sum(1 for r in subset if r["top3_contains_expected"]) / len(subset),
            "accept_count": sub_accept_count,
            "retry_capture_count": sum(1 for r in subset if r["quality_gate_decision"] == RETRY),
            "manual_review_count": sum(1 for r in subset if r["quality_gate_decision"] == MANUAL),
            "orb_top1_accuracy_accept_subset": acc_top1,
        }

    categories = ["rws_bright_clear", "rws_bright_glare", "rws_dark_clear", "rws_dark_glare"]
    category_metrics = {cat: get_group_metrics([r for r in results if r["category"] == cat]) for cat in categories}

    bright_metrics = get_group_metrics([r for r in results if "bright" in r["category"]])
    dark_metrics = get_group_metrics([r for r in results if "dark" in r["category"]])
    clear_metrics = get_group_metrics([r for r in results if "clear" in r["category"]])
    glare_metrics = get_group_metrics([r for r in results if "glare" in r["category"]])
    upright_metrics = get_group_metrics([r for r in results if r["expected_orientation"] == "upright"])
    reversed_metrics = get_group_metrics([r for r in results if r["expected_orientation"] == "reversed"])

    # Connection and review pack README
    review_pack_index = {
        ACCEPT: [r["sample_id"] for r in results if r["quality_gate_decision"] == ACCEPT],
        RETRY: [r["sample_id"] for r in results if r["quality_gate_decision"] == RETRY],
        MANUAL: [r["sample_id"] for r in results if r["quality_gate_decision"] == MANUAL],
    }
    with open(os.path.join(output_dir, "quality_gate_review_pack", "index.json"), "w", encoding="utf-8") as handle:
        json.dump(review_pack_index, handle, indent=2)

    errors_count = sum(1 for r in results if not r["top1_correct"] and r["quality_gate_decision"] == ACCEPT)
    with open(os.path.join(output_dir, "error_review_pack", "README.md"), "w", encoding="utf-8") as handle:
        if errors_count == 0:
            handle.write("# Error Review Pack\n\nNo Top-1 errors in the accepted subset.\n")
        else:
            handle.write(f"# Error Review Pack\n\nContains {errors_count} incorrect accepted matches.\n")

    summary = {
        "stage": "stage6_rws_expansion_benchmark",
        "fixture_id": aggregate.fixture_id,
        "sample_count": sample_count,
        "processed_count": processed_count,
        "orb_top1_accuracy_all": round(orb_top1_all, 6),
        "orb_top3_accuracy_all": round(orb_top3_all, 6),
        "orb_top1_accuracy_accept_subset": round(orb_top1_accept, 6) if orb_top1_accept is not None else None,
        "orb_top3_accuracy_accept_subset": round(orb_top3_accept, 6) if orb_top3_accept is not None else None,
        "accept_count": accept_count,
        "retry_capture_count": retry_capture_count,
        "manual_review_count": manual_review_count,
        "quality_gate_decision_counts": {
            ACCEPT: accept_count,
            RETRY: retry_capture_count,
            MANUAL: manual_review_count,
        },
        "bright_clear_metrics": category_metrics["rws_bright_clear"],
        "bright_glare_metrics": category_metrics["rws_bright_glare"],
        "dark_clear_metrics": category_metrics["rws_dark_clear"],
        "dark_glare_metrics": category_metrics["rws_dark_glare"],
        "bright_vs_dark_summary": {
            "bright": bright_metrics,
            "dark": dark_metrics,
        },
        "clear_vs_glare_summary": {
            "clear": clear_metrics,
            "glare": glare_metrics,
        },
        "upright_vs_reversed_summary": {
            "upright": upright_metrics,
            "reversed": reversed_metrics,
        },
        "wrong_deck_far": "NOT_APPLICABLE",
        "wrong_deck_reason": "fixture contains no wrong-deck samples",
        "runtime_proxy_mean_ms": round(statistics.fmean(runtimes), 3),
        "runtime_proxy_p50_ms": round(float(np.percentile(runtimes, 50)), 3),
        "runtime_proxy_p95_ms": round(float(np.percentile(runtimes, 95)), 3),
    }

    # Write output files
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for r in results:
            payload = {k: r[k] for k in MATRIX_COLUMNS}
            payload["quality_gate_reasons"] = "|".join(r["quality_gate_reasons"])
            writer.writerow(payload)

    with open(os.path.join(output_dir, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    def _acc_str(val):
        return "n/a" if val is None else f"{val * 100:.1f}%"

    lines = [
        "# Stage 6 RWS Fixture Expansion Offline Benchmark",
        "",
        "Offline-only benchmark. No runtime thresholds or integration approved.",
        "",
        f"* **Total samples**: {sample_count}",
        f"* **Processed samples**: {processed_count}",
        f"* **ORB Top-1 accuracy (all)**: {_acc_str(orb_top1_all)}",
        f"* **ORB Top-3 accuracy (all)**: {_acc_str(orb_top3_all)}",
        f"* **ORB Top-1 accuracy (accept subset)**: {_acc_str(orb_top1_accept)} (Count: {accept_count})",
        f"* **ORB Top-3 accuracy (accept subset)**: {_acc_str(orb_top3_accept)}",
        "",
        "## Quality Gate Decision Distribution",
        "",
        f"- **ACCEPT_FOR_IDENTIFICATION**: {accept_count}",
        f"- **RETRY_CAPTURE**: {retry_capture_count}",
        f"- **MANUAL_REVIEW**: {manual_review_count}",
        "",
        "## Metrics By Category",
        "",
        "| Category | Count | ORB Top-1 | Accept | Retry | Manual | Accept Top-1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cat in categories:
        m = category_metrics[cat]
        if m:
            lines.append(
                f"| {cat} | {m['count']} | {_acc_str(m['orb_top1_accuracy'])} | {m['accept_count']} | "
                f"{m['retry_capture_count']} | {m['manual_review_count']} | {_acc_str(m['orb_top1_accuracy_accept_subset'])} |"
            )

    lines.extend([
        "",
        "## Summaries",
        "",
        "### Bright vs Dark",
        "",
        "| Group | Count | ORB Top-1 | Accept | Retry | Manual |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Bright | {bright_metrics['count']} | {_acc_str(bright_metrics['orb_top1_accuracy'])} | {bright_metrics['accept_count']} | {bright_metrics['retry_capture_count']} | {bright_metrics['manual_review_count']} |",
        f"| Dark | {dark_metrics['count']} | {_acc_str(dark_metrics['orb_top1_accuracy'])} | {dark_metrics['accept_count']} | {dark_metrics['retry_capture_count']} | {dark_metrics['manual_review_count']} |",
        "",
        "### Clear vs Glare",
        "",
        "| Group | Count | ORB Top-1 | Accept | Retry | Manual |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Clear | {clear_metrics['count']} | {_acc_str(clear_metrics['orb_top1_accuracy'])} | {clear_metrics['accept_count']} | {clear_metrics['retry_capture_count']} | {clear_metrics['manual_review_count']} |",
        f"| Glare | {glare_metrics['count']} | {_acc_str(glare_metrics['orb_top1_accuracy'])} | {glare_metrics['accept_count']} | {glare_metrics['retry_capture_count']} | {glare_metrics['manual_review_count']} |",
        "",
        "### Upright vs Reversed",
        "",
        "| Group | Count | ORB Top-1 | Accept | Retry | Manual |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Upright | {upright_metrics['count']} | {_acc_str(upright_metrics['orb_top1_accuracy'])} | {upright_metrics['accept_count']} | {upright_metrics['retry_capture_count']} | {upright_metrics['manual_review_count']} |",
        f"| Reversed | {reversed_metrics['count']} | {_acc_str(reversed_metrics['orb_top1_accuracy'])} | {reversed_metrics['accept_count']} | {reversed_metrics['retry_capture_count']} | {reversed_metrics['manual_review_count']} |",
        "",
        "## Runtime Performance (Proxy)",
        "",
        f"- **Mean runtime**: {summary['runtime_proxy_mean_ms']:.3f} ms",
        f"- **p50 runtime**: {summary['runtime_proxy_p50_ms']:.3f} ms",
        f"- **p95 runtime**: {summary['runtime_proxy_p95_ms']:.3f} ms",
    ])

    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run RWS offline benchmark.")
    parser.add_argument("--manifest", default="logs/live_fixtures/stage6_real_camera_fixture_expansion_rws_minimal/manifest.json")
    parser.add_argument("--ground-truth", default="logs/live_fixtures/stage6_real_camera_fixture_expansion_rws_minimal/ground_truth.json")
    parser.add_argument("--reference-dir", default="biblioteka_talii/rider-waite-smith/produkcja/wzorce_cv")
    parser.add_argument("--output", default="logs/offline_replay/stage6_rws_expansion_benchmark")
    args = parser.parse_args(argv)

    run_rws_benchmark(args.manifest, args.ground_truth, args.reference_dir, args.output)
    print("Benchmark complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
