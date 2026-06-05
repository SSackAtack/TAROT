import csv
import json
import os
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.region_methods import run_region_method
from tools.cv_detection_lab.stage2_region_benchmark import (
    MATRIX_COLUMNS,
    EXPECTED_CANDIDATE_COUNTS,
    build_fixture_pairs,
    run_benchmark,
    _build_row,
)


class Stage2RegionBenchmarkTest(unittest.TestCase):
    def test_build_fixture_pairs_uses_required_state_first_pairs(self):
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
            cascade = next(pair for pair in pairs if pair.name == "one_card_to_three_cards")
            self.assertEqual(cascade.expected_candidate_count, EXPECTED_CANDIDATE_COUNTS["one_card_to_three_cards"])
            self.assertEqual(cascade.expected_added_count, 2)
            self.assertEqual(cascade.expected_removed_count, 0)

    def test_baseline_components_detects_one_candidate(self):
        frame = _blank_frame()
        mask = np.zeros((120, 160), dtype=np.uint8)
        cv2.rectangle(mask, (50, 25), (90, 95), 255, -1)

        result = run_region_method("baseline_components", mask, frame)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].bbox, [50, 25, 41, 71])
        self.assertGreater(result.candidates[0].foreground_fill_ratio, 0.95)

    def test_empty_to_empty_gives_zero_candidates_and_pass(self):
        frame = _blank_frame()
        mask = np.zeros((120, 160), dtype=np.uint8)
        result = run_region_method("baseline_components", mask, frame)
        pair = _pair_like("empty_to_empty", expected=0, added=0, removed=0, change_type="no_change")

        row = _build_row("baseline_components", pair, result, runtime_ms=1.0)

        self.assertEqual(row["candidate_count"], 0)
        self.assertEqual(row["verdict"], "PASS")

    def test_morph_close_or_dilate_merge_merges_split_object(self):
        frame = _blank_frame()
        mask = np.zeros((120, 160), dtype=np.uint8)
        cv2.rectangle(mask, (45, 25), (65, 95), 255, -1)
        cv2.rectangle(mask, (72, 25), (92, 95), 255, -1)

        result = run_region_method("dilate_merge_components", mask, frame)

        self.assertEqual(len(result.candidates), 1)
        self.assertTrue(result.candidates[0].merge_card_flag)

    def test_oversized_bbox_flag_detects_low_foreground_fill_ratio(self):
        frame = _blank_frame()
        mask = np.zeros((120, 160), dtype=np.uint8)
        mask[20, 20] = 255
        mask[95, 115] = 255
        cv2.line(mask, (20, 20), (115, 95), 255, 1)

        result = run_region_method("baseline_components", mask, frame, min_area_ratio=0.0001)

        self.assertEqual(len(result.candidates), 1)
        self.assertTrue(result.candidates[0].oversized_bbox_flag)

    def test_matrix_csv_contains_required_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "stage2_region")

            run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["baseline_components"],
            )

            with open(os.path.join(output_dir, "matrix.csv"), newline="", encoding="utf-8") as handle:
                first_row = next(csv.DictReader(handle))

            for column in MATRIX_COLUMNS:
                self.assertIn(column, first_row)

    def test_report_marks_recommendation_as_provisional_with_manual_review_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "stage2_region")

            report = run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["baseline_components"],
            )

            self.assertEqual(report["stage"], "stage2_region_segmentation")
            self.assertEqual(report["input_stage1_method"], "gray_absdiff_gaussian")
            self.assertEqual(report["recommendation_status"], "PROVISIONAL_RECOMMENDED")
            self.assertTrue(report["manual_review_required"])
            self.assertEqual(len(report["manual_review_paths"]), 6)

            with open(os.path.join(output_dir, "report.json"), encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["recommendation_status"], "PROVISIONAL_RECOMMENDED")
            self.assertTrue(payload["manual_review_required"])
            self.assertEqual(len(payload["manual_review_paths"]), 6)


def _blank_frame():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    frame[:, :] = (20, 55, 35)
    return frame


def _pair_like(name, expected, added, removed, change_type):
    class Pair:
        pass

    pair = Pair()
    pair.name = name
    pair.change_type = change_type
    pair.expected_candidate_count = expected
    pair.expected_added_count = added
    pair.expected_removed_count = removed
    return pair


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
