import argparse
import csv
import json
import os
import time
from dataclasses import dataclass

import cv2
import numpy as np

from tools.cv_detection_lab.card_localization_methods import available_localization_methods, run_localization_method
from tools.cv_detection_lab.methods import run_diff_method
from tools.cv_detection_lab.region_methods import run_region_method


INPUT_STAGE1_METHOD = "gray_absdiff_gaussian"
INPUT_STAGE2_METHOD = "contour_external"

EXPECTED_LOCALIZED_COUNTS = {
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
    "geometry_source_frame",
    "runtime_ms",
    "candidate_count",
    "localized_card_count",
    "expected_localized_count",
    "localization_delta",
    "quad_count",
    "bbox_count",
    "rotated_bbox_count",
    "aspect_ratio_avg",
    "aspect_ratio_error_avg",
    "quad_area_ratio_avg",
    "bbox_area_ratio_avg",
    "rectangularity_score_avg",
    "border_score_avg",
    "edge_support_score_avg",
    "corner_score_avg",
    "angle_stability_score_avg",
    "candidate_to_stage2_area_ratio_avg",
    "geometry_confidence_avg",
    "reject_count",
    "reject_reasons",
    "verdict",
    "verdict_basis",
]


@dataclass(frozen=True)
class FixturePair:
    name: str
    previous_path: str
    current_path: str
    expected_localized_count: int
    change_type: str
    geometry_source_frame: str


def build_fixture_pairs(fixture_dir):
    pairs = []
    for pair_name, previous_scenario, current_scenario, change_type, source_frame in PAIR_DEFINITIONS:
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
                expected_localized_count=EXPECTED_LOCALIZED_COUNTS[pair_name],
                change_type=change_type,
                geometry_source_frame=source_frame,
            )
        )
    return pairs


def run_benchmark(fixture_dir, output_dir, method_names=None):
    method_names = method_names or available_localization_methods()
    os.makedirs(output_dir, exist_ok=True)
    rows = []
    pairs = build_fixture_pairs(fixture_dir)

    for method_name in method_names:
        for pair in pairs:
            previous = _read_image(pair.previous_path)
            current = _read_image(pair.current_path)
            stage1 = run_diff_method(INPUT_STAGE1_METHOD, previous, current)
            stage2 = run_region_method(INPUT_STAGE2_METHOD, stage1.mask, current)
            source = previous if pair.geometry_source_frame == "previous" else current
            started = time.perf_counter()
            result = run_localization_method(method_name, source, stage1.mask, stage2.candidates)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            row = _build_row(method_name, pair, result, runtime_ms, candidate_count=len(stage2.candidates))
            rows.append(row)
            _write_debug_outputs(output_dir, method_name, pair.name, current, source, stage2.candidates, result)

    recommended_method = _choose_recommended_method(rows, method_names)
    summary = {
        "stage": "stage3_card_localization",
        "input_stage1_method": INPUT_STAGE1_METHOD,
        "input_stage2_method": INPUT_STAGE2_METHOD,
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


def _build_row(method_name, pair, result, runtime_ms, candidate_count):
    geometries = result.geometries
    localized = len(geometries)
    expected = pair.expected_localized_count
    reject_reasons = sorted({item.get("reject_reason", "unknown") for item in result.rejected_geometries})
    return {
        "method": method_name,
        "pair": pair.name,
        "change_type": pair.change_type,
        "geometry_source_frame": pair.geometry_source_frame,
        "runtime_ms": round(runtime_ms, 3),
        "candidate_count": candidate_count,
        "localized_card_count": localized,
        "expected_localized_count": expected,
        "localization_delta": localized - expected,
        "quad_count": sum(1 for geometry in geometries if geometry.ordered_quad_points),
        "bbox_count": sum(1 for geometry in geometries if geometry.bbox),
        "rotated_bbox_count": sum(1 for geometry in geometries if geometry.rotated_bbox),
        "aspect_ratio_avg": _avg(geometries, "aspect_ratio"),
        "aspect_ratio_error_avg": _avg(geometries, "aspect_ratio_error"),
        "quad_area_ratio_avg": _avg(geometries, "quad_area_ratio"),
        "bbox_area_ratio_avg": _avg(geometries, "bbox_area_ratio"),
        "rectangularity_score_avg": _avg(geometries, "rectangularity_score"),
        "border_score_avg": _avg(geometries, "border_score"),
        "edge_support_score_avg": _avg(geometries, "edge_support_score"),
        "corner_score_avg": _avg(geometries, "corner_score"),
        "angle_stability_score_avg": _avg(geometries, "angle_stability_score"),
        "candidate_to_stage2_area_ratio_avg": _avg(geometries, "candidate_to_stage2_area_ratio"),
        "geometry_confidence_avg": _avg(geometries, "geometry_confidence"),
        "reject_count": len(result.rejected_geometries),
        "reject_reasons": ";".join(reject_reasons),
        "verdict": _verdict(pair, localized, geometries),
        "verdict_basis": "localized_count_and_geometry_quality",
        "geometries": [geometry.to_dict() for geometry in geometries],
        "rejected_geometries": result.rejected_geometries,
    }


def _verdict(pair, localized_count, geometries):
    expected = pair.expected_localized_count
    if pair.name == "empty_to_empty":
        return "PASS" if localized_count == 0 else "FAIL"
    if abs(localized_count - expected) > 1:
        return "FAIL"
    if localized_count != expected:
        return "YELLOW"
    confidence = _avg(geometries, "geometry_confidence")
    aspect_error = _avg(geometries, "aspect_ratio_error")
    rotated_or_quad = any(geometry.rotated_bbox or geometry.quad_points for geometry in geometries)
    if confidence < 0.25 or aspect_error > 0.45:
        return "YELLOW"
    if not rotated_or_quad:
        return "YELLOW"
    return "PASS"


def _write_debug_outputs(output_dir, method_name, pair_name, current, source, stage2_candidates, result):
    pair_dir = os.path.join(output_dir, method_name, pair_name)
    os.makedirs(pair_dir, exist_ok=True)
    stage2_overlay = current.copy()
    for candidate in stage2_candidates:
        x, y, width, height = candidate.bbox
        cv2.rectangle(stage2_overlay, (x, y), (x + width, y + height), (0, 255, 255), 2)
    cv2.imwrite(os.path.join(pair_dir, "stage2_candidate_overlay.png"), stage2_overlay)

    geometry_overlay = source.copy()
    for geometry in result.geometries:
        if geometry.ordered_quad_points:
            points = np.array(geometry.ordered_quad_points, dtype=np.int32)
            cv2.polylines(geometry_overlay, [points], isClosed=True, color=(0, 255, 0), thickness=2)
        else:
            x, y, width, height = geometry.bbox
            cv2.rectangle(geometry_overlay, (x, y), (x + width, y + height), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(pair_dir, "card_geometry_overlay.png"), geometry_overlay)
    cv2.imwrite(os.path.join(pair_dir, "edge_debug.png"), result.debug_images.get("edge_debug", np.zeros(source.shape[:2], dtype=np.uint8)))
    cv2.imwrite(os.path.join(pair_dir, "contour_debug.png"), result.debug_images.get("contour_debug", np.zeros(source.shape[:2], dtype=np.uint8)))
    _write_json(
        os.path.join(pair_dir, "geometry_debug.json"),
        {
            "geometries": [geometry.to_dict() for geometry in result.geometries],
            "rejected_geometries": result.rejected_geometries,
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
        "# Stage 3 Card Localization Benchmark",
        "",
        f"Input Stage 1 Method: `{summary['input_stage1_method']}`",
        f"Input Stage 2 Method: `{summary['input_stage2_method']}`",
        f"Fixture: `{summary['fixture_dir']}`",
        f"Recommended method: `{summary['recommended_method']}`",
        f"Recommendation status: `{summary['recommendation_status']}`",
        f"Manual review required: `{summary['manual_review_required']}`",
        "",
        "## Matrix summary",
        "",
        "| Method | Pair | Source | Localized | Expected | Verdict | Confidence | Aspect err | Runtime ms |",
        "|---|---|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['method']} | {row['pair']} | {row['geometry_source_frame']} | "
            f"{row['localized_card_count']} | {row['expected_localized_count']} | {row['verdict']} | "
            f"{row['geometry_confidence_avg']:.3f} | {row['aspect_ratio_error_avg']:.3f} | {row['runtime_ms']:.3f} |"
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
            "- Overlaye wymagają ręcznego review Supervisora przed decyzją Stage 3.",
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
        avg_confidence = sum(float(row["geometry_confidence_avg"]) for row in method_rows) / max(1, len(method_rows))
        avg_aspect_error = sum(float(row["aspect_ratio_error_avg"]) for row in method_rows) / max(1, len(method_rows))
        avg_runtime = sum(float(row["runtime_ms"]) for row in method_rows) / max(1, len(method_rows))
        scores.append((pass_count, yellow_count, avg_confidence, -avg_aspect_error, -avg_runtime, method_name))
    scores.sort(reverse=True)
    return scores[0][5] if scores else None


def _manual_review_paths(output_dir, method_name):
    return [
        os.path.join(output_dir, method_name, pair_name, "card_geometry_overlay.png").replace("\\", "/")
        for pair_name, _, _, _, _ in PAIR_DEFINITIONS
    ]


def _avg(items, attr):
    if not items:
        return 0.0
    return round(sum(float(getattr(item, attr)) for item in items) / float(len(items)), 6)


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
    parser = argparse.ArgumentParser(description="Run Stage 3 offline card localization benchmark.")
    parser.add_argument("--fixture", required=True, help="Path to event_first_current_debug_verified fixture directory.")
    parser.add_argument("--output", required=True, help="Output directory under logs/offline_replay.")
    parser.add_argument("--method", action="append", dest="methods", help="Method to run. Can be repeated.")
    args = parser.parse_args(argv)
    summary = run_benchmark(args.fixture, args.output, method_names=args.methods)
    print(json.dumps({"recommended_method": summary["recommended_method"], "rows": len(summary["rows"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
