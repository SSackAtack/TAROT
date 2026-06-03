import argparse
import csv
import json
import os
import time
from dataclasses import asdict, dataclass

import cv2
import numpy as np

from tools.cv_detection_lab.methods import available_methods, run_diff_method


EXPECTED_REGION_COUNTS = {
    "empty_to_empty": 0,
    "empty_to_one_card": 1,
    "empty_to_three_cards": 3,
    "one_card_to_three_cards": 2,
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


@dataclass(frozen=True)
class FixturePair:
    name: str
    previous_path: str
    current_path: str
    expected_regions: int
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
                expected_regions=EXPECTED_REGION_COUNTS[pair_name],
                change_type=change_type,
            )
        )
    return pairs


def run_benchmark(fixture_dir, output_dir, method_names=None):
    method_names = method_names or available_methods()
    os.makedirs(output_dir, exist_ok=True)
    rows = []
    pairs = build_fixture_pairs(fixture_dir)

    for method_name in method_names:
        for pair in pairs:
            previous = _read_image(pair.previous_path)
            current = _read_image(pair.current_path)
            started = time.perf_counter()
            result = run_diff_method(method_name, previous, current)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            regions = _extract_regions(result.mask)
            row = _build_row(method_name, pair, result.mask, regions, runtime_ms)
            rows.append(row)
            _write_debug_images(output_dir, method_name, pair.name, result.diff, result.mask, current, regions)

    summary = {
        "fixture_dir": fixture_dir,
        "methods_tested": list(method_names),
        "rows": rows,
        "recommended_method": _choose_recommended_method(rows, method_names),
    }
    _write_matrix(output_dir, rows)
    _write_json(os.path.join(output_dir, "report.json"), summary)
    _write_markdown_report(output_dir, summary)
    return summary


def _scenario_frame_path(fixture_dir, scenario):
    return os.path.join(fixture_dir, scenario, SCENARIO_FRAME_NAMES[scenario])


def _read_image(path):
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def _extract_regions(mask, min_area_ratio=0.002, max_area_ratio=0.6):
    if mask is None or mask.size == 0:
        return []
    total_area = float(mask.shape[0] * mask.shape[1])
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    regions = []
    for label in range(1, count):
        x, y, width, height, area = stats[label]
        area_ratio = float(area) / total_area
        if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
            continue
        regions.append(
            {
                "bbox": [int(x), int(y), int(width), int(height)],
                "area": int(area),
                "area_ratio": area_ratio,
            }
        )
    return regions


def _build_row(method_name, pair, mask, regions, runtime_ms):
    changed_area_ratio = float(np.count_nonzero(mask)) / float(mask.size) if mask.size else 0.0
    region_count = len(regions)
    expected = pair.expected_regions
    return {
        "method": method_name,
        "pair": pair.name,
        "change_type": pair.change_type,
        "runtime_ms": round(runtime_ms, 3),
        "changed_area_ratio": round(changed_area_ratio, 6),
        "region_count": region_count,
        "expected_region_count": expected,
        "region_count_delta": region_count - expected,
        "global_shift_score": round(changed_area_ratio, 6),
        "ignored_small_count": 0,
        "ignored_large_count": 0,
        "verdict": _verdict(region_count, expected, changed_area_ratio),
        "regions": regions,
    }


def _verdict(region_count, expected, changed_area_ratio):
    if expected == 0:
        return "PASS" if region_count == 0 and changed_area_ratio < 0.01 else "FAIL"
    if region_count == expected:
        return "PASS"
    if abs(region_count - expected) == 1:
        return "YELLOW"
    return "FAIL"


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


def _write_debug_images(output_dir, method_name, pair_name, diff, mask, current, regions):
    pair_dir = os.path.join(output_dir, method_name, pair_name)
    os.makedirs(pair_dir, exist_ok=True)
    cv2.imwrite(os.path.join(pair_dir, "diff.png"), diff)
    cv2.imwrite(os.path.join(pair_dir, "mask.png"), mask)
    overlay = current.copy()
    for region in regions:
        x, y, width, height = region["bbox"]
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (0, 255, 255), 2)
    cv2.imwrite(os.path.join(pair_dir, "regions_overlay.png"), overlay)


def _write_matrix(output_dir, rows):
    fieldnames = [
        "method",
        "pair",
        "change_type",
        "runtime_ms",
        "changed_area_ratio",
        "region_count",
        "expected_region_count",
        "region_count_delta",
        "global_shift_score",
        "ignored_small_count",
        "ignored_large_count",
        "verdict",
    ]
    with open(os.path.join(output_dir, "matrix.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row[name] for name in fieldnames})


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_markdown_report(output_dir, summary):
    lines = [
        "# Stage 1 Difference Detection Benchmark",
        "",
        f"Fixture: `{summary['fixture_dir']}`",
        f"Recommended method: `{summary['recommended_method']}`",
        "",
        "| Method | Pair | Regions | Expected | Verdict | Runtime ms |",
        "|---|---|---:|---:|---|---:|",
    ]
    for row in summary["rows"]:
        lines.append(
            f"| {row['method']} | {row['pair']} | {row['region_count']} | "
            f"{row['expected_region_count']} | {row['verdict']} | {row['runtime_ms']:.3f} |"
        )
    with open(os.path.join(output_dir, "report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Stage 1 offline difference detection benchmark.")
    parser.add_argument("--fixture", required=True, help="Path to event_first_current_debug_verified fixture directory.")
    parser.add_argument("--output", required=True, help="Output directory under logs/offline_replay.")
    parser.add_argument("--method", action="append", dest="methods", help="Method to run. Can be repeated.")
    args = parser.parse_args(argv)
    summary = run_benchmark(args.fixture, args.output, method_names=args.methods)
    print(json.dumps({"recommended_method": summary["recommended_method"], "rows": len(summary["rows"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
