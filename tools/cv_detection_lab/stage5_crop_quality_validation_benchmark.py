"""Stage 5 Crop Quality Validation offline benchmark.

CLI:
    python tools/cv_detection_lab/stage5_crop_quality_validation_benchmark.py \
        --fixture logs/live_fixtures/event_first_current_debug_verified \
        --output logs/offline_replay/stage5_crop_quality_validation

Dependencies: OpenCV, NumPy (standard library only).
Does NOT perform card identification, ORB matching, OCR, or runtime integration.
"""
import argparse
import csv
import json
import os
import time

import cv2

from tools.cv_detection_lab.methods import run_diff_method
from tools.cv_detection_lab.region_methods import run_region_method
from tools.cv_detection_lab.card_localization_methods import run_localization_method
from tools.cv_detection_lab.crop_deskew_methods import (
    DEFAULT_TARGET_HEIGHT,
    DEFAULT_TARGET_WIDTH,
    run_crop_deskew,
)
from tools.cv_detection_lab.crop_quality_methods import (
    QUALITY_METHOD,
    THRESHOLD_STATUS,
    build_no_crop_quality_debug_sheet,
    build_quality_debug_sheet,
    evaluate_crop_quality_suite,
)


INPUT_STAGE1_METHOD = "gray_absdiff_gaussian"
INPUT_STAGE2_METHOD = "contour_external"
INPUT_STAGE3_METHOD = "hybrid_edge_plus_contour"
INPUT_STAGE4_CROP_METHOD = "quad_warp_perspective_fixed_aspect"
INPUT_STAGE4_NORMALIZATION = "resize_only_normalization"
INPUT_STAGE4_PIPELINE = f"{INPUT_STAGE4_CROP_METHOD}__{INPUT_STAGE4_NORMALIZATION}"

EXPECTED_CROP_COUNTS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 1,
    "empty_to_three_cards": 3,
    "one_card_to_three_cards": 2,
    "one_card_to_empty": 1,
    "three_cards_to_empty": 3,
}

PAIR_DEFINITIONS = [
    ("empty_to_empty", "empty", "empty", "no_change", "current"),
    ("empty_to_one_card", "empty", "one_card", "added", "current"),
    ("empty_to_three_cards", "empty", "three_cards", "added", "current"),
    ("one_card_to_three_cards", "one_card", "three_cards", "added", "current"),
    ("one_card_to_empty", "one_card", "empty", "removed", "previous"),
    ("three_cards_to_empty", "three_cards", "empty", "removed", "previous"),
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
    "crop_source_frame",
    "runtime_ms",
    "crop_count",
    "expected_crop_count",
    "crop_count_delta",
    "quality_pass_count",
    "quality_yellow_count",
    "quality_fail_count",
    "crop_quality_score_avg",
    "identification_readiness_score_avg",
    "edge_cut_risk_count",
    "background_margin_score_avg",
    "top_margin_ratio_avg",
    "top_reflection_score_avg",
    "border_visible_score_avg",
    "border_continuity_score_avg",
    "corner_visibility_score_avg",
    "card_fill_ratio_avg",
    "brightness_mean_avg",
    "contrast_score_avg",
    "blur_score_avg",
    "texture_density_score_avg",
    "aspect_ratio_error_avg",
    "reject_count",
    "reject_reasons",
    "warning_flags",
    "threshold_status",
    "verdict",
    "verdict_basis",
]


class FixturePair:
    __slots__ = ("name", "previous_path", "current_path", "expected_crop_count", "change_type", "crop_source_frame")

    def __init__(self, name, previous_path, current_path, expected_crop_count, change_type, crop_source_frame):
        self.name = name
        self.previous_path = previous_path
        self.current_path = current_path
        self.expected_crop_count = expected_crop_count
        self.change_type = change_type
        self.crop_source_frame = crop_source_frame


def build_fixture_pairs(fixture_dir):
    pairs = []
    for pair_name, prev_sc, curr_sc, change_type, source_frame in PAIR_DEFINITIONS:
        prev_path = _scenario_frame_path(fixture_dir, prev_sc)
        curr_path = _scenario_frame_path(fixture_dir, curr_sc)
        if not os.path.exists(prev_path):
            raise FileNotFoundError(prev_path)
        if not os.path.exists(curr_path):
            raise FileNotFoundError(curr_path)
        pairs.append(FixturePair(pair_name, prev_path, curr_path, EXPECTED_CROP_COUNTS[pair_name], change_type, source_frame))
    return pairs


def run_benchmark(fixture_dir, output_dir, method=QUALITY_METHOD):
    if method != QUALITY_METHOD:
        raise ValueError(f"Unknown Stage 5 quality method: {method}")

    os.makedirs(output_dir, exist_ok=True)
    rows = []
    pairs = build_fixture_pairs(fixture_dir)

    for pair in pairs:
        previous = _read_image(pair.previous_path)
        current = _read_image(pair.current_path)
        stage1 = run_diff_method(INPUT_STAGE1_METHOD, previous, current)
        stage2 = run_region_method(INPUT_STAGE2_METHOD, stage1.mask, current)
        source = previous if pair.crop_source_frame == "previous" else current
        stage3 = run_localization_method(INPUT_STAGE3_METHOD, source, stage1.mask, stage2.candidates)
        stage4 = run_crop_deskew(
            crop_method=INPUT_STAGE4_CROP_METHOD,
            normalization_variant=INPUT_STAGE4_NORMALIZATION,
            source_frame=source,
            stage3_geometries=stage3.geometries,
            crop_source_frame=pair.crop_source_frame,
            target_width=DEFAULT_TARGET_WIDTH,
            target_height=DEFAULT_TARGET_HEIGHT,
            padding_ratio=0.0,
        )

        started = time.perf_counter()
        suite = evaluate_crop_quality_suite(stage4.crops)
        runtime_ms = (time.perf_counter() - started) * 1000.0
        row = _build_row(pair, suite, stage4, runtime_ms)
        rows.append(row)
        _write_pair_debug_outputs(output_dir, method, pair, suite, row["verdict"])

    summary = {
        "stage": "stage5_crop_quality_validation",
        "input_stage1_method": INPUT_STAGE1_METHOD,
        "input_stage2_method": INPUT_STAGE2_METHOD,
        "input_stage3_method": INPUT_STAGE3_METHOD,
        "input_stage4_pipeline": INPUT_STAGE4_PIPELINE,
        "fixture_dir": fixture_dir,
        "methods_tested": [method],
        "rows": rows,
        "recommended_method": method,
        "recommendation_status": "PROVISIONAL_RECOMMENDED",
        "manual_review_required": True,
        "manual_review_paths": _manual_review_paths(output_dir, method),
        "threshold_status": THRESHOLD_STATUS,
    }
    _write_matrix(output_dir, rows)
    _write_json(os.path.join(output_dir, "report.json"), summary)
    _write_markdown_report(output_dir, summary)
    return summary


def _build_row(pair, suite, stage4, runtime_ms):
    results = suite.results
    crop_count = len(results)
    expected = pair.expected_crop_count
    statuses = [r.metrics.crop_quality_status for r in results]
    flags = sorted({flag for r in results for flag in r.metrics.quality_flags})
    reject_reasons = sorted({r.get("reject_reason", "unknown") for r in stage4.rejected_crops + suite.rejected})
    edge_cut_count = sum(1 for r in results if r.metrics.edge_cut_risk)
    verdict = _verdict(pair, results, crop_count, expected)

    return {
        "method": QUALITY_METHOD,
        "pair": pair.name,
        "change_type": pair.change_type,
        "crop_source_frame": pair.crop_source_frame,
        "runtime_ms": round(runtime_ms, 3),
        "crop_count": crop_count,
        "expected_crop_count": expected,
        "crop_count_delta": crop_count - expected,
        "quality_pass_count": statuses.count("PASS"),
        "quality_yellow_count": statuses.count("YELLOW"),
        "quality_fail_count": statuses.count("FAIL"),
        "crop_quality_score_avg": _avg_metric(results, "crop_quality_score"),
        "identification_readiness_score_avg": _avg_metric(results, "identification_readiness_score"),
        "edge_cut_risk_count": edge_cut_count,
        "background_margin_score_avg": _avg_metric(results, "background_margin_score"),
        "top_margin_ratio_avg": _avg_metric(results, "top_margin_ratio"),
        "top_reflection_score_avg": _avg_metric(results, "top_reflection_score"),
        "border_visible_score_avg": _avg_metric(results, "border_visible_score"),
        "border_continuity_score_avg": _avg_metric(results, "border_continuity_score"),
        "corner_visibility_score_avg": _avg_metric(results, "corner_visibility_score"),
        "card_fill_ratio_avg": _avg_metric(results, "card_fill_ratio"),
        "brightness_mean_avg": _avg_metric(results, "brightness_mean"),
        "contrast_score_avg": _avg_metric(results, "contrast_score"),
        "blur_score_avg": _avg_metric(results, "variance_of_laplacian_blur_score"),
        "texture_density_score_avg": _avg_metric(results, "texture_density_score"),
        "aspect_ratio_error_avg": _avg_metric(results, "aspect_ratio_error"),
        "reject_count": len(stage4.rejected_crops) + len(suite.rejected),
        "reject_reasons": ";".join(reject_reasons),
        "warning_flags": ";".join(flags),
        "threshold_status": THRESHOLD_STATUS,
        "verdict": verdict,
        "verdict_basis": "crop_count_and_quality_metrics",
        "results": [r.to_dict() for r in results],
        "rejected_crops": stage4.rejected_crops + suite.rejected,
    }


def _verdict(pair, results, crop_count, expected):
    if pair.name == "empty_to_empty":
        return "PASS" if crop_count == 0 else "FAIL"
    if pair.change_type == "removed" and pair.crop_source_frame != "previous":
        return "FAIL"
    if crop_count != expected:
        return "FAIL" if abs(crop_count - expected) > 1 else "YELLOW"
    if not results:
        return "FAIL"
    fail_count = sum(1 for r in results if r.metrics.crop_quality_status == "FAIL")
    yellow_count = sum(1 for r in results if r.metrics.crop_quality_status == "YELLOW")
    edge_cut_count = sum(1 for r in results if r.metrics.edge_cut_risk)
    if fail_count > len(results) / 2.0 or edge_cut_count > len(results) / 2.0:
        return "FAIL"
    if fail_count or yellow_count:
        return "YELLOW"
    return "PASS"


def _write_pair_debug_outputs(output_dir, method, pair, suite, verdict):
    pair_dir = os.path.join(output_dir, method, pair.name)
    os.makedirs(pair_dir, exist_ok=True)
    crop_count = len(suite.results)
    sheet = build_quality_debug_sheet(suite.results, pair.name, pair.expected_crop_count, crop_count, verdict)
    if sheet is None:
        sheet = build_no_crop_quality_debug_sheet(pair.name, pair.expected_crop_count, crop_count, verdict)
    cv2.imwrite(os.path.join(pair_dir, "crop_quality_debug_sheet.png"), sheet)

    payload = {
        "pair": pair.name,
        "method": method,
        "crop_count": crop_count,
        "expected_crop_count": pair.expected_crop_count,
        "quality_pass_count": sum(1 for r in suite.results if r.metrics.crop_quality_status == "PASS"),
        "quality_yellow_count": sum(1 for r in suite.results if r.metrics.crop_quality_status == "YELLOW"),
        "quality_fail_count": sum(1 for r in suite.results if r.metrics.crop_quality_status == "FAIL"),
        "threshold_status": THRESHOLD_STATUS,
        "results": [r.to_dict() for r in suite.results],
        "rejected": suite.rejected,
    }
    _write_json(os.path.join(pair_dir, "quality_debug.json"), payload)
    for result in suite.results:
        prefix = f"crop_{result.crop_index:02d}"
        if result.overlay is not None:
            cv2.imwrite(os.path.join(pair_dir, f"{prefix}_quality_overlay.png"), result.overlay)
        _write_json(os.path.join(pair_dir, f"{prefix}_metrics.json"), result.to_dict())


def _write_matrix(output_dir, rows):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in MATRIX_COLUMNS})


def _write_markdown_report(output_dir, summary):
    lines = [
        "# Stage 5 Crop Quality Validation Benchmark",
        "",
        f"Input Stage 1 Method: `{summary['input_stage1_method']}`",
        f"Input Stage 2 Method: `{summary['input_stage2_method']}`",
        f"Input Stage 3 Method: `{summary['input_stage3_method']}`",
        f"Input Stage 4 Pipeline: `{summary['input_stage4_pipeline']}`",
        f"Fixture: `{summary['fixture_dir']}`",
        f"Recommended method: `{summary['recommended_method']}`",
        f"Recommendation status: `{summary['recommendation_status']}`",
        f"Threshold status: `{summary['threshold_status']}`",
        f"Manual review required: `{summary['manual_review_required']}`",
        "",
        "## Matrix summary",
        "",
        "| Method | Pair | Source | Crops | Expected | Verdict | Quality | Readiness | Flags | Runtime ms |",
        "|---|---|---|---:|---:|---|---:|---:|---|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['method']} | {row['pair']} | {row['crop_source_frame']} | "
            f"{row['crop_count']} | {row['expected_crop_count']} | {row['verdict']} | "
            f"{float(row['crop_quality_score_avg']):.3f} | "
            f"{float(row['identification_readiness_score_avg']):.3f} | "
            f"{row['warning_flags'] or 'none'} | {float(row['runtime_ms']):.3f} |"
        )
    lines.extend([
        "",
        "## Manual Review Paths",
        "",
        *[f"- `{path}`" for path in summary.get("manual_review_paths", [])],
        "",
        "## Known limitations",
        "",
        "- Wynik jest tylko `PROVISIONAL_RECOMMENDED`.",
        "- Progi maja status `BENCHMARK_HEURISTIC_ONLY`.",
        "- Benchmark nie identyfikuje kart.",
        "- Nie tworzy plikow ORB/template/classification/OCR.",
        "- Crop quality debug sheets wymagaja recznego review Supervisora.",
    ])
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)


def _avg_metric(results, attr):
    if not results:
        return 0.0
    return round(sum(float(getattr(r.metrics, attr)) for r in results) / float(len(results)), 6)


def _scenario_frame_path(fixture_dir, scenario):
    return os.path.join(fixture_dir, scenario, SCENARIO_FRAME_NAMES[scenario])


def _read_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img


def _manual_review_paths(output_dir, method):
    return [
        os.path.join(output_dir, method, pair_name, "crop_quality_debug_sheet.png").replace("\\", "/")
        for pair_name, _, _, _, _ in PAIR_DEFINITIONS
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Stage 5 offline crop quality benchmark.")
    parser.add_argument("--fixture", required=True, help="Fixture directory path.")
    parser.add_argument("--output", required=True, help="Output directory.")
    parser.add_argument("--method", default=QUALITY_METHOD, help="Quality method name.")
    args = parser.parse_args(argv)

    summary = run_benchmark(args.fixture, args.output, method=args.method)
    print(json.dumps({
        "recommended_method": summary["recommended_method"],
        "recommendation_status": summary["recommendation_status"],
        "threshold_status": summary["threshold_status"],
        "rows": len(summary["rows"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
