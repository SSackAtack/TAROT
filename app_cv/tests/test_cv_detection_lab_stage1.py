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
