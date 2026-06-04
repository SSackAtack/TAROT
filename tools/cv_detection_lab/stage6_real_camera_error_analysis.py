"""Build an offline review pack for Stage 6 real-camera ORB identification errors."""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_identification_methods import load_reference_deck, run_identification_method


METHOD = "orb_bfmatcher_ratio_test"


def build_error_analysis(matrix_path, report_path, crops_dir, reference_dir, deck_profile, output_dir):
    rows = _read_matrix(matrix_path)
    errors = [
        row for row in rows
        if row["method"] == METHOD and row["expected_behavior"] == "identify" and not _bool(row["top1_correct"])
    ]
    references = load_reference_deck(reference_dir, deck_profile)
    reference_by_id = {reference.card_id: reference for reference in references}
    os.makedirs(os.path.join(output_dir, "error_review_pack"), exist_ok=True)
    analyses = []
    for row in errors:
        crop = _read_image(os.path.join(crops_dir, f"{row['sample_id']}.png"))
        result = run_identification_method(METHOD, crop, references)
        analysis = {
            "sample_id": row["sample_id"],
            "category": row["category"],
            "similarity_group": row["similarity_group"] or None,
            "expected_card_id": row["expected_card_id"],
            "predicted_card_id": row["predicted_card_id"],
            "top3_contains_expected": _bool(row["top3_contains_expected"]),
            "confidence_score": float(row["confidence_score"]),
            "confidence_gap": float(row["confidence_gap"]),
            "probable_cause": classify_probable_cause(row),
            "top_k_candidates": result.top_k_candidates,
            "match_evidence": result.match_evidence,
        }
        analyses.append(analysis)
        _write_sheet(
            crop,
            reference_by_id[row["expected_card_id"]].image,
            reference_by_id[row["predicted_card_id"]].image,
            analysis,
            os.path.join(output_dir, "error_review_pack", f"{row['sample_id']}.png"),
        )

    summary = {
        "stage": "stage6_real_camera_error_analysis",
        "method": METHOD,
        "error_count_top1": len(errors),
        "error_count_top3": sum(not item["top3_contains_expected"] for item in analyses),
        "cause_counts": _counts(item["probable_cause"] for item in analyses),
        "category_counts": _counts(item["category"] for item in analyses),
        "analysis_scope": "offline_only_not_runtime_approved",
        "important_limitation": "Result measures extract_card plus ORB identification, not matcher isolation.",
        "errors": analyses,
    }
    shutil.copy2(matrix_path, os.path.join(output_dir, "matrix.csv"))
    shutil.copy2(report_path, os.path.join(output_dir, "benchmark_report.json"))
    destination_crops = os.path.join(output_dir, "extracted_crops")
    if os.path.isdir(destination_crops):
        shutil.rmtree(destination_crops)
    shutil.copytree(crops_dir, destination_crops)
    _write_json(os.path.join(output_dir, "error_analysis.json"), summary)
    _write_markdown(os.path.join(output_dir, "error_analysis.md"), summary)
    return summary


def classify_probable_cause(row):
    score = float(row.get("confidence_score", 0.0))
    gap = float(row.get("confidence_gap", 0.0))
    if row["category"] == "gilded_visually_similar" and score >= 0.20 and gap >= 0.20:
        return "ground_truth_mismatch_suspected"
    if row["category"] == "gilded_yellow":
        return "image_quality_or_crop"
    if row["category"] == "gilded_visually_similar":
        return "visual_similarity_or_matcher"
    if score < 0.03:
        return "image_quality_or_crop"
    if _bool(row["top3_contains_expected"]):
        return "matcher_ranking"
    return "crop_or_matcher"


def _write_sheet(crop, expected, predicted, analysis, path):
    panel = np.zeros((620, 1000, 3), dtype=np.uint8)
    images = [crop, expected, predicted]
    labels = ["extracted crop", f"expected {analysis['expected_card_id']}", f"predicted {analysis['predicted_card_id']}"]
    for index, (image, label) in enumerate(zip(images, labels)):
        resized = cv2.resize(image, (200, 330), interpolation=cv2.INTER_AREA)
        x = 30 + index * 310
        panel[55:385, x:x + 200] = resized
        cv2.putText(panel, label, (x, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 230, 230), 1, cv2.LINE_AA)
    lines = [
        f"sample: {analysis['sample_id']}",
        f"category: {analysis['category']} similarity: {analysis['similarity_group']}",
        f"top3_contains_expected: {analysis['top3_contains_expected']}",
        f"score={analysis['confidence_score']:.3f} gap={analysis['confidence_gap']:.3f}",
        f"probable_cause: {analysis['probable_cause']}",
        "manual decision required; offline only",
    ]
    for index, line in enumerate(lines):
        cv2.putText(panel, line, (30, 430 + index * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)
    cv2.imwrite(path, panel)


def _read_matrix(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_image(path):
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def _counts(values):
    result = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def _bool(value):
    return value is True or str(value).lower() == "true"


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_markdown(path, summary):
    lines = [
        "# Stage 6 Real-Camera ORB Error Analysis", "",
        f"Top-1 errors: `{summary['error_count_top1']}`",
        f"Outside Top-3: `{summary['error_count_top3']}`", "",
        "This analysis measures `extract_card -> ORB identification`, not matcher isolation.",
        "All conclusions remain offline-only.", "",
        "| Sample | Category | Expected | Predicted | Top3 | Probable cause |",
        "|---|---|---|---|---|---|",
    ]
    for item in summary["errors"]:
        lines.append(
            f"| {item['sample_id']} | {item['category']} | {item['expected_card_id']} | "
            f"{item['predicted_card_id']} | {item['top3_contains_expected']} | {item['probable_cause']} |"
        )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Stage 6 real-camera ORB error analysis pack.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--crops", required=True)
    parser.add_argument("--reference-deck-dir", required=True)
    parser.add_argument("--deck-profile", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    summary = build_error_analysis(
        args.matrix, args.report, args.crops, args.reference_deck_dir, args.deck_profile, args.output
    )
    print(json.dumps({"error_count_top1": summary["error_count_top1"], "cause_counts": summary["cause_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
