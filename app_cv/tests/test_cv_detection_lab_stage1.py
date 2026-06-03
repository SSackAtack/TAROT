import csv
import json
import os
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.stage1_diff_benchmark import (
    EXPECTED_REGION_COUNTS,
    build_fixture_pairs,
    run_benchmark,
    _extract_regions,
)


class Stage1DiffBenchmarkTest(unittest.TestCase):
    def test_build_fixture_pairs_uses_verified_analysis_frames(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)

            pairs = build_fixture_pairs(fixture_dir)

            self.assertEqual(
                sorted(pair.name for pair in pairs),
                [
                    "empty_to_empty",
                    "empty_to_one_card",
                    "empty_to_three_cards",
                    "one_card_to_empty",
                    "one_card_to_three_cards",
                    "three_cards_to_empty",
                ],
            )
            first = next(pair for pair in pairs if pair.name == "empty_to_one_card")
            self.assertEqual(first.expected_regions, EXPECTED_REGION_COUNTS["empty_to_one_card"])
            self.assertEqual(first.change_type, "added")

    def test_run_benchmark_writes_matrix_report_and_debug_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "offline_replay")

            report = run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["gray_absdiff_fixed"],
            )

            self.assertEqual(len(report["rows"]), 6)
            self.assertTrue(os.path.exists(os.path.join(output_dir, "matrix.csv")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "report.json")))
            self.assertTrue(os.path.exists(os.path.join(output_dir, "report.md")))
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        output_dir,
                        "gray_absdiff_fixed",
                        "empty_to_one_card",
                        "mask.png",
                    )
                )
            )

            with open(os.path.join(output_dir, "matrix.csv"), newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            row = next(item for item in rows if item["pair"] == "empty_to_one_card")
            self.assertEqual(row["method"], "gray_absdiff_fixed")
            self.assertEqual(int(row["expected_region_count"]), 1)
            self.assertGreaterEqual(int(row["region_count"]), 1)

            with open(os.path.join(output_dir, "report.json"), encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("recommended_method", payload)
            self.assertEqual(payload["methods_tested"], ["gray_absdiff_fixed"])

    def test_gray_absdiff_fixed_marks_empty_to_empty_as_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "offline_replay")

            report = run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["gray_absdiff_fixed"],
            )

            row = next(item for item in report["rows"] if item["pair"] == "empty_to_empty")
            self.assertEqual(row["verdict"], "PASS")
            self.assertEqual(row["region_count"], 0)

    def test_merges_nearby_components_without_hiding_raw_count(self):
        mask = np.zeros((120, 160), dtype=np.uint8)
        cv2.rectangle(mask, (40, 30), (70, 90), 255, -1)
        cv2.rectangle(mask, (78, 30), (108, 90), 255, -1)

        result = _extract_regions(mask, min_area_ratio=0.01, max_area_ratio=0.6, merge_padding_px=12)

        self.assertEqual(result.raw_region_count, 2)
        self.assertEqual(result.filtered_region_count, 2)
        self.assertEqual(result.merged_region_count, 1)
        self.assertEqual(len(result.merged_regions), 1)

    def test_counts_small_noise_without_adding_merged_region(self):
        mask = np.zeros((120, 160), dtype=np.uint8)
        cv2.circle(mask, (10, 10), 2, 255, -1)
        cv2.circle(mask, (30, 10), 2, 255, -1)

        result = _extract_regions(mask, min_area_ratio=0.01, max_area_ratio=0.6)

        self.assertEqual(result.raw_region_count, 2)
        self.assertEqual(result.ignored_small_count, 2)
        self.assertEqual(result.merged_region_count, 0)

    def test_counts_large_region_without_adding_merged_region(self):
        mask = np.zeros((120, 160), dtype=np.uint8)
        cv2.rectangle(mask, (0, 0), (159, 119), 255, -1)

        result = _extract_regions(mask, min_area_ratio=0.01, max_area_ratio=0.6)

        self.assertEqual(result.raw_region_count, 1)
        self.assertEqual(result.ignored_large_count, 1)
        self.assertEqual(result.merged_region_count, 0)

    def test_matrix_csv_contains_refined_region_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "offline_replay")

            run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["gray_absdiff_fixed"],
            )

            with open(os.path.join(output_dir, "matrix.csv"), newline="", encoding="utf-8") as handle:
                first_row = next(csv.DictReader(handle))

            for column in [
                "raw_region_count",
                "filtered_region_count",
                "merged_region_count",
                "ignored_small_count",
                "ignored_large_count",
                "largest_region_area_ratio",
                "largest_merged_region_area_ratio",
                "verdict_basis",
            ]:
                self.assertIn(column, first_row)

    def test_report_marks_recommendation_as_provisional_with_manual_review_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "offline_replay")

            report = run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["gray_absdiff_fixed"],
            )

            self.assertEqual(report["recommendation_status"], "PROVISIONAL_RECOMMENDED")
            self.assertTrue(report["manual_review_required"])
            self.assertEqual(len(report["manual_review_paths"]), 6)
            self.assertTrue(report["manual_review_paths"][0].endswith("regions_overlay.png"))

            with open(os.path.join(output_dir, "report.json"), encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["recommendation_status"], "PROVISIONAL_RECOMMENDED")
            self.assertTrue(payload["manual_review_required"])
            self.assertEqual(len(payload["manual_review_paths"]), 6)


def _write_fixture(root):
    fixture_dir = os.path.join(root, "event_first_current_debug_verified")
    scenarios = {
        "empty": ("0", []),
        "one_card": ("1", [((70, 50), (120, 150))]),
        "three_cards": (
            "3",
            [
                ((70, 50), (120, 150)),
                ((145, 50), (195, 150)),
                ((220, 50), (270, 150)),
            ],
        ),
    }
    for scenario, (suffix, cards) in scenarios.items():
        scenario_dir = os.path.join(fixture_dir, scenario)
        os.makedirs(scenario_dir, exist_ok=True)
        frame = np.zeros((200, 320, 3), dtype=np.uint8)
        frame[:, :] = (20, 55, 35)
        for top_left, bottom_right in cards:
            cv2.rectangle(frame, top_left, bottom_right, (120, 110, 95), -1)
        cv2.imwrite(os.path.join(scenario_dir, f"analysis_frame_{suffix}.png"), frame)
    return fixture_dir


if __name__ == "__main__":
    unittest.main()
