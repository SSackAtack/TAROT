"""Stage 4 Crop / Deskew / Normalize offline benchmark.

CLI:
    python tools/cv_detection_lab/stage4_crop_deskew_normalize_benchmark.py \
        --fixture logs/live_fixtures/event_first_current_debug_verified \
        --output  logs/offline_replay/stage4_crop_deskew_normalize

Dependencies: OpenCV, NumPy (standard library only).
Does NOT perform card identification, ORB matching, or runtime integration.
"""
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
from tools.cv_detection_lab.crop_deskew_methods import (
    available_crop_methods,
    available_normalizations,
    build_debug_sheet,
    resize_to_target,
    run_crop_deskew,
    DEFAULT_TARGET_WIDTH,
    DEFAULT_TARGET_HEIGHT,
)


# ---------------------------------------------------------------------------
# Approved upstream pipeline
# ---------------------------------------------------------------------------
INPUT_STAGE1_METHOD = "gray_absdiff_gaussian"
INPUT_STAGE2_METHOD = "contour_external"
INPUT_STAGE3_METHOD = "hybrid_edge_plus_contour"

# ---------------------------------------------------------------------------
# Fixture definitions
# ---------------------------------------------------------------------------
EXPECTED_CROP_COUNTS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 1,
    "empty_to_three_cards": 3,
    "one_card_to_three_cards": 2,
    "one_card_to_empty": 1,
    "three_cards_to_empty": 3,
}

PAIR_DEFINITIONS = [
    # (pair_name, previous_scenario, current_scenario, change_type, crop_source_frame)
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

# Default benchmark pipeline variants
DEFAULT_PIPELINE_VARIANTS = [
    ("bbox_crop_resize", "resize_only_normalization", 0.0),
    ("rotated_rect_warp_affine", "resize_only_normalization", 0.0),
    ("quad_warp_perspective", "resize_only_normalization", 0.0),
    ("quad_warp_perspective_with_safe_padding", "resize_only_normalization", 0.03),
    ("quad_warp_perspective_fixed_aspect", "resize_only_normalization", 0.0),
    ("quad_warp_perspective_keep_border_margin", "resize_only_normalization", 0.03),
    ("quad_warp_perspective_with_safe_padding", "grayscale_normalization", 0.03),
    ("quad_warp_perspective_with_safe_padding", "clahe_normalization", 0.03),
    ("quad_warp_perspective_with_safe_padding", "brightness_contrast_normalization", 0.03),
    ("quad_warp_perspective_with_safe_padding", "orientation_portrait_normalization", 0.03),
]

MATRIX_COLUMNS = [
    "method",
    "normalization_variant",
    "pair",
    "change_type",
    "crop_source_frame",
    "runtime_ms",
    "geometry_count",
    "crop_count",
    "expected_crop_count",
    "crop_count_delta",
    "target_width",
    "target_height",
    "crop_width_avg",
    "crop_height_avg",
    "crop_aspect_ratio_avg",
    "aspect_ratio_error_avg",
    "padding_ratio",
    "border_visible_score_avg",
    "edge_cut_risk_count",
    "foreground_fill_ratio_avg",
    "brightness_mean_avg",
    "contrast_score_avg",
    "blur_score_avg",
    "normalized_contrast_score_avg",
    "reject_count",
    "reject_reasons",
    "verdict",
    "verdict_basis",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
class FixturePair:
    __slots__ = ("name", "previous_path", "current_path", "expected_crop_count", "change_type", "crop_source_frame")

    def __init__(self, name, previous_path, current_path, expected_crop_count, change_type, crop_source_frame):
        self.name = name
        self.previous_path = previous_path
        self.current_path = current_path
        self.expected_crop_count = expected_crop_count
        self.change_type = change_type
        self.crop_source_frame = crop_source_frame


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_fixture_pairs(fixture_dir):
    pairs = []
    for pair_name, prev_sc, curr_sc, change_type, source_frame in PAIR_DEFINITIONS:
        prev_path = _scenario_frame_path(fixture_dir, prev_sc)
        curr_path = _scenario_frame_path(fixture_dir, curr_sc)
        if not os.path.exists(prev_path):
            raise FileNotFoundError(prev_path)
        if not os.path.exists(curr_path):
            raise FileNotFoundError(curr_path)
        pairs.append(FixturePair(
            name=pair_name,
            previous_path=prev_path,
            current_path=curr_path,
            expected_crop_count=EXPECTED_CROP_COUNTS[pair_name],
            change_type=change_type,
            crop_source_frame=source_frame,
        ))
    return pairs


def run_benchmark(fixture_dir, output_dir, pipeline_variants=None):
    """Run the full Stage 4 benchmark.

    Parameters
    ----------
    fixture_dir : str
    output_dir : str
    pipeline_variants : list of (crop_method, normalization, padding_ratio) or None
    """
    pipeline_variants = pipeline_variants or DEFAULT_PIPELINE_VARIANTS
    os.makedirs(output_dir, exist_ok=True)
    pairs = build_fixture_pairs(fixture_dir)
    rows = []

    methods_tested = sorted({v[0] for v in pipeline_variants})
    normalizations_tested = sorted({v[1] for v in pipeline_variants})

    for crop_method, norm_variant, pad_ratio in pipeline_variants:
        variant_key = f"{crop_method}__{norm_variant}"
        for pair in pairs:
            previous = _read_image(pair.previous_path)
            current = _read_image(pair.current_path)

            # Run upstream pipeline
            stage1 = run_diff_method(INPUT_STAGE1_METHOD, previous, current)
            stage2 = run_region_method(INPUT_STAGE2_METHOD, stage1.mask, current)

            # Source frame selection: previous for removed, current otherwise
            source = previous if pair.crop_source_frame == "previous" else current
            stage3 = run_localization_method(INPUT_STAGE3_METHOD, source, stage1.mask, stage2.candidates)
            geometry_count = len(stage3.geometries)

            # Run Stage 4
            started = time.perf_counter()
            result = run_crop_deskew(
                crop_method=crop_method,
                normalization_variant=norm_variant,
                source_frame=source,
                stage3_geometries=stage3.geometries,
                crop_source_frame=pair.crop_source_frame,
                target_width=DEFAULT_TARGET_WIDTH,
                target_height=DEFAULT_TARGET_HEIGHT,
                padding_ratio=pad_ratio,
            )
            runtime_ms = (time.perf_counter() - started) * 1000.0

            row = _build_row(crop_method, norm_variant, pair, result, runtime_ms, geometry_count, pad_ratio)
            rows.append(row)

            # Write debug outputs
            _write_debug_outputs(output_dir, variant_key, pair.name, source, stage3, result)

    recommended = _choose_recommended_pipeline(rows, pipeline_variants)
    summary = {
        "stage": "stage4_crop_deskew_normalize",
        "input_stage1_method": INPUT_STAGE1_METHOD,
        "input_stage2_method": INPUT_STAGE2_METHOD,
        "input_stage3_method": INPUT_STAGE3_METHOD,
        "fixture_dir": fixture_dir,
        "methods_tested": methods_tested,
        "normalizations_tested": normalizations_tested,
        "rows": rows,
        "recommended_pipeline": recommended,
        "recommendation_status": "PROVISIONAL_RECOMMENDED" if recommended else "NO_RECOMMENDATION",
        "manual_review_required": True,
        "manual_review_paths": _manual_review_paths(output_dir, recommended) if recommended else [],
    }
    _write_matrix(output_dir, rows)
    _write_json(os.path.join(output_dir, "report.json"), summary)
    _write_markdown_report(output_dir, summary)
    return summary


# ---------------------------------------------------------------------------
# Row building
# ---------------------------------------------------------------------------

def _build_row(crop_method, norm_variant, pair, result, runtime_ms, geometry_count, pad_ratio):
    crops = result.crops
    crop_count = len(crops)
    expected = pair.expected_crop_count
    edge_cut_count = sum(1 for c in crops if c.edge_cut_risk)
    reject_reasons = sorted({r.get("reject_reason", "unknown") for r in result.rejected_crops}) if result.rejected_crops else []

    return {
        "method": crop_method,
        "normalization_variant": norm_variant,
        "pair": pair.name,
        "change_type": pair.change_type,
        "crop_source_frame": pair.crop_source_frame,
        "runtime_ms": round(runtime_ms, 3),
        "geometry_count": geometry_count,
        "crop_count": crop_count,
        "expected_crop_count": expected,
        "crop_count_delta": crop_count - expected,
        "target_width": DEFAULT_TARGET_WIDTH,
        "target_height": DEFAULT_TARGET_HEIGHT,
        "crop_width_avg": _avg_attr(crops, "crop_width"),
        "crop_height_avg": _avg_attr(crops, "crop_height"),
        "crop_aspect_ratio_avg": _avg_attr(crops, "crop_aspect_ratio"),
        "aspect_ratio_error_avg": _avg_attr(crops, "aspect_ratio_error"),
        "padding_ratio": round(pad_ratio, 4),
        "border_visible_score_avg": _avg_attr(crops, "border_visible_score"),
        "edge_cut_risk_count": edge_cut_count,
        "foreground_fill_ratio_avg": _avg_attr(crops, "foreground_fill_ratio"),
        "brightness_mean_avg": _avg_attr(crops, "brightness_mean"),
        "contrast_score_avg": _avg_attr(crops, "contrast_score"),
        "blur_score_avg": _avg_attr(crops, "blur_score"),
        "normalized_contrast_score_avg": _avg_attr(crops, "normalized_contrast_score"),
        "reject_count": len(result.rejected_crops),
        "reject_reasons": ";".join(reject_reasons),
        "verdict": _verdict(pair, crop_count, expected, edge_cut_count, crops),
        "verdict_basis": "crop_count_and_quality_metrics",
        # Internal (not serialised to CSV)
        "crops": [c.to_dict() for c in crops],
        "rejected_crops": result.rejected_crops,
    }


def _verdict(pair, crop_count, expected, edge_cut_count, crops):
    if pair.name == "empty_to_empty":
        return "PASS" if crop_count == 0 else "FAIL"

    if crop_count != expected:
        return "FAIL" if abs(crop_count - expected) > 1 else "YELLOW"

    if edge_cut_count > 0:
        return "YELLOW"

    # Check transform validity
    if any(not c.transform_valid for c in crops):
        return "YELLOW"

    avg_ar_err = _avg_attr(crops, "aspect_ratio_error")
    if avg_ar_err > 0.25:
        return "YELLOW"

    return "PASS"


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

def _choose_recommended_pipeline(rows, pipeline_variants):
    scores = {}
    for crop_method, norm_variant, pad_ratio in pipeline_variants:
        key = f"{crop_method}__{norm_variant}"
        variant_rows = [r for r in rows if r["method"] == crop_method and r["normalization_variant"] == norm_variant]
        pass_count = sum(1 for r in variant_rows if r["verdict"] == "PASS")
        yellow_count = sum(1 for r in variant_rows if r["verdict"] == "YELLOW")
        edge_risk = sum(int(r["edge_cut_risk_count"]) for r in variant_rows)
        ar_err = sum(float(r["aspect_ratio_error_avg"]) for r in variant_rows) / max(1, len(variant_rows))
        border_score = sum(float(r["border_visible_score_avg"]) for r in variant_rows) / max(1, len(variant_rows))
        blur = sum(float(r["blur_score_avg"]) for r in variant_rows) / max(1, len(variant_rows))
        contrast = sum(float(r["contrast_score_avg"]) for r in variant_rows) / max(1, len(variant_rows))
        avg_runtime = sum(float(r["runtime_ms"]) for r in variant_rows) / max(1, len(variant_rows))
        scores[key] = (
            pass_count,       # higher is better
            yellow_count,     # higher is better (vs FAIL)
            -edge_risk,       # fewer edge cuts
            -ar_err,          # lower aspect ratio error
            border_score,     # higher border visibility
            blur,             # higher blur score = sharper
            contrast,         # higher contrast
            -avg_runtime,     # faster
        )
    if not scores:
        return None
    best = max(scores, key=lambda k: scores[k])
    return best


# ---------------------------------------------------------------------------
# Debug output
# ---------------------------------------------------------------------------

def _write_debug_outputs(output_dir, variant_key, pair_name, source_frame, stage3_result, crop_result):
    pair_dir = os.path.join(output_dir, variant_key, pair_name)
    os.makedirs(pair_dir, exist_ok=True)

    # Stage 3 geometry overlay
    overlay = source_frame.copy()
    for geo in stage3_result.geometries:
        if geo.ordered_quad_points:
            pts = np.array(geo.ordered_quad_points, dtype=np.int32)
            cv2.polylines(overlay, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
        else:
            x, y, w, h = geo.bbox
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(pair_dir, "stage3_geometry_overlay.png"), overlay)

    # Individual crops
    for idx, crop in enumerate(crop_result.crops, start=1):
        prefix = f"crop_{idx:02d}"
        if crop.raw_crop is not None:
            cv2.imwrite(os.path.join(pair_dir, f"{prefix}_raw.png"), crop.raw_crop)
        if crop.deskewed_crop is not None:
            cv2.imwrite(os.path.join(pair_dir, f"{prefix}_deskewed.png"), crop.deskewed_crop)
        if crop.normalized_crop is not None:
            cv2.imwrite(os.path.join(pair_dir, f"{prefix}_normalized.png"), crop.normalized_crop)

    # Debug sheet
    sheet = build_debug_sheet(crop_result.crops, source_frame, DEFAULT_TARGET_WIDTH, DEFAULT_TARGET_HEIGHT)
    if sheet is not None:
        cv2.imwrite(os.path.join(pair_dir, "crop_debug_sheet.png"), sheet)

    # JSON debug
    _write_json(os.path.join(pair_dir, "crop_debug.json"), crop_result.to_dict())


# ---------------------------------------------------------------------------
# CSV / JSON / Markdown writers
# ---------------------------------------------------------------------------

def _write_matrix(output_dir, rows):
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in MATRIX_COLUMNS})


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)


def _write_markdown_report(output_dir, summary):
    lines = [
        "# Stage 4 Crop / Deskew / Normalize Benchmark",
        "",
        f"Input Stage 1 Method: `{summary['input_stage1_method']}`",
        f"Input Stage 2 Method: `{summary['input_stage2_method']}`",
        f"Input Stage 3 Method: `{summary['input_stage3_method']}`",
        f"Fixture: `{summary['fixture_dir']}`",
        f"Recommended pipeline: `{summary['recommended_pipeline']}`",
        f"Recommendation status: `{summary['recommendation_status']}`",
        f"Manual review required: `{summary['manual_review_required']}`",
        "",
        "## Matrix summary",
        "",
        "| Method | Normalization | Pair | Source | Crops | Expected | Verdict | AR err | Border | Edge cut | Runtime ms |",
        "|---|---|---|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['method']} | {row['normalization_variant']} | {row['pair']} | "
            f"{row['crop_source_frame']} | {row['crop_count']} | {row['expected_crop_count']} | "
            f"{row['verdict']} | {row['aspect_ratio_error_avg']:.3f} | "
            f"{row['border_visible_score_avg']:.3f} | {row['edge_cut_risk_count']} | "
            f"{row['runtime_ms']:.3f} |"
        )
    lines.extend([
        "",
        "## Manual Review Paths",
        "",
        *[f"- `{p}`" for p in summary.get("manual_review_paths", [])],
        "",
        "## Known limitations",
        "",
        "- Wynik jest tylko `PROVISIONAL_RECOMMENDED`.",
        "- Benchmark nie identyfikuje kart.",
        "- Nie tworzy plików ORB/template/classification.",
        "- Crop debug sheets wymagają ręcznego review Supervisora.",
    ])
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _avg_attr(items, attr):
    if not items:
        return 0.0
    return round(sum(float(getattr(i, attr)) for i in items) / float(len(items)), 6)


def _scenario_frame_path(fixture_dir, scenario):
    return os.path.join(fixture_dir, scenario, SCENARIO_FRAME_NAMES[scenario])


def _read_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img


def _manual_review_paths(output_dir, recommended_key):
    if not recommended_key:
        return []
    return [
        os.path.join(output_dir, recommended_key, pair_name, "crop_debug_sheet.png").replace("\\", "/")
        for pair_name, _, _, _, _ in PAIR_DEFINITIONS
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Stage 4 offline crop/deskew/normalize benchmark.")
    parser.add_argument("--fixture", required=True, help="Fixture directory path.")
    parser.add_argument("--output", required=True, help="Output directory.")
    parser.add_argument("--method", default=None, help="Crop method filter.")
    parser.add_argument("--normalization", default=None, help="Normalization variant filter.")
    args = parser.parse_args(argv)

    variants = DEFAULT_PIPELINE_VARIANTS
    if args.method or args.normalization:
        variants = [
            (m, n, p) for m, n, p in variants
            if (args.method is None or m == args.method)
            and (args.normalization is None or n == args.normalization)
        ]
        if not variants:
            print(f"No matching variants for method={args.method} normalization={args.normalization}")
            return 1

    summary = run_benchmark(args.fixture, args.output, pipeline_variants=variants)
    print(json.dumps({
        "recommended_pipeline": summary["recommended_pipeline"],
        "recommendation_status": summary["recommendation_status"],
        "rows": len(summary["rows"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
