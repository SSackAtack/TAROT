import csv
import json
import os
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.card_localization_methods import run_localization_method
from tools.cv_detection_lab.stage3_card_localization_benchmark import (
    MATRIX_COLUMNS,
    EXPECTED_LOCALIZED_COUNTS,
    build_fixture_pairs,
    run_benchmark,
    _build_row,
)


class Stage3CardLocalizationBenchmarkTest(unittest.TestCase):
    def test_build_fixture_pairs_uses_required_pairs(self):
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
            self.assertEqual(cascade.expected_localized_count, EXPECTED_LOCALIZED_COUNTS["one_card_to_three_cards"])
            self.assertEqual(cascade.geometry_source_frame, "current")

    def test_removed_pairs_use_previous_frame_for_geometry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)

            pairs = build_fixture_pairs(fixture_dir)

            self.assertEqual(next(pair for pair in pairs if pair.name == "one_card_to_empty").geometry_source_frame, "previous")
            self.assertEqual(next(pair for pair in pairs if pair.name == "three_cards_to_empty").geometry_source_frame, "previous")

    def test_min_area_rect_returns_rotated_geometry(self):
        frame = _blank_frame()
        mask = np.zeros((160, 180), dtype=np.uint8)
        rect = ((90, 80), (50, 95), 12)
        points = cv2.boxPoints(rect).astype(np.int32)
        cv2.fillConvexPoly(mask, points, 255)
        candidate = _candidate([40, 25, 110, 120])

        result = run_localization_method("min_area_rect_candidate", frame, mask, [candidate])

        self.assertEqual(len(result.geometries), 1)
        self.assertIsNotNone(result.geometries[0].rotated_bbox)
        self.assertIsNotNone(result.geometries[0].ordered_quad_points)

    def test_approx_poly_dp_quad_returns_four_points(self):
        frame = _blank_frame()
        mask = np.zeros((160, 180), dtype=np.uint8)
        cv2.rectangle(mask, (55, 30), (110, 130), 255, -1)
        candidate = _candidate([45, 20, 80, 120])

        result = run_localization_method("approx_poly_dp_quad", frame, mask, [candidate])

        self.assertEqual(len(result.geometries), 1)
        self.assertEqual(len(result.geometries[0].ordered_quad_points), 4)
        self.assertEqual(result.geometries[0].geometry_type, "quad")

    def test_empty_to_empty_gives_zero_geometries_and_pass(self):
        pair = _pair_like("empty_to_empty", "no_change", "current", expected=0)
        result = _result_like([])

        row = _build_row("bounding_rect_tight", pair, result, runtime_ms=1.0, candidate_count=0)

        self.assertEqual(row["localized_card_count"], 0)
        self.assertEqual(row["verdict"], "PASS")

    def test_matrix_csv_contains_required_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "stage3_card_localization")

            run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["bounding_rect_tight"],
            )

            with open(os.path.join(output_dir, "matrix.csv"), newline="", encoding="utf-8") as handle:
                first_row = next(csv.DictReader(handle))

            for column in MATRIX_COLUMNS:
                self.assertIn(column, first_row)

    def test_report_marks_recommendation_as_provisional_with_manual_review_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "stage3_card_localization")

            report = run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["bounding_rect_tight"],
            )

            self.assertEqual(report["stage"], "stage3_card_localization")
            self.assertEqual(report["input_stage1_method"], "gray_absdiff_gaussian")
            self.assertEqual(report["input_stage2_method"], "contour_external")
            self.assertEqual(report["recommendation_status"], "PROVISIONAL_RECOMMENDED")
            self.assertTrue(report["manual_review_required"])
            self.assertEqual(len(report["manual_review_paths"]), 6)

            with open(os.path.join(output_dir, "report.json"), encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["recommendation_status"], "PROVISIONAL_RECOMMENDED")
            self.assertTrue(payload["manual_review_required"])

    def test_benchmark_does_not_write_crop_or_recognition_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = _write_fixture(tmpdir)
            output_dir = os.path.join(tmpdir, "stage3_card_localization")

            run_benchmark(
                fixture_dir=fixture_dir,
                output_dir=output_dir,
                method_names=["bounding_rect_tight"],
            )

            forbidden = {"crop.png", "deskew.png", "recognized_card.png"}
            written = set()
            for root, _, files in os.walk(output_dir):
                for name in files:
                    written.add(name)
            self.assertFalse(forbidden & written)


def _blank_frame():
    frame = np.zeros((160, 180, 3), dtype=np.uint8)
    frame[:, :] = (20, 55, 35)
    return frame


def _candidate(bbox):
    return {"bbox": bbox}


def _pair_like(name, change_type, geometry_source_frame, expected):
    class Pair:
        pass

    pair = Pair()
    pair.name = name
    pair.change_type = change_type
    pair.geometry_source_frame = geometry_source_frame
    pair.expected_localized_count = expected
    return pair


def _result_like(geometries):
    class Result:
        pass

    result = Result()
    result.geometries = geometries
    result.rejected_geometries = []
    result.debug_images = {}
    return result


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
