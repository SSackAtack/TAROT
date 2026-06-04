"""Unit tests for Stage 5 Crop Quality Validation offline benchmark."""
import csv
import json
import os
import shutil
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.crop_quality_methods import evaluate_crop_quality
from tools.cv_detection_lab.stage5_crop_quality_validation_benchmark import (
    MATRIX_COLUMNS,
    PAIR_DEFINITIONS,
    build_fixture_pairs,
    run_benchmark,
)


def _create_synthetic_fixture(fixture_dir):
    """Create minimal synthetic fixture images for Stage 5 benchmark tests."""
    for scenario, fname in [
        ("empty", "analysis_frame_0.png"),
        ("one_card", "analysis_frame_1.png"),
        ("three_cards", "analysis_frame_3.png"),
    ]:
        scenario_dir = os.path.join(fixture_dir, scenario)
        os.makedirs(scenario_dir, exist_ok=True)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :] = (40, 60, 40)
        if scenario == "one_card":
            _draw_card(img, 250, 100)
        elif scenario == "three_cards":
            for x_start in [80, 250, 420]:
                _draw_card(img, x_start, 100)
        cv2.imwrite(os.path.join(scenario_dir, fname), img)


def _draw_card(img, x, y):
    cv2.rectangle(img, (x, y), (x + 140, y + 280), (205, 185, 155), -1)
    cv2.rectangle(img, (x + 8, y + 8), (x + 132, y + 272), (245, 245, 245), 4)
    cv2.line(img, (x + 20, y + 60), (x + 120, y + 230), (70, 80, 120), 3)
    cv2.circle(img, (x + 70, y + 140), 34, (130, 70, 160), -1)


def _synthetic_crop(width=300, height=495):
    crop = np.zeros((height, width, 3), dtype=np.uint8)
    crop[:, :] = (35, 45, 35)
    cv2.rectangle(crop, (24, 22), (width - 24, height - 22), (205, 185, 155), -1)
    cv2.rectangle(crop, (36, 36), (width - 36, height - 36), (245, 245, 245), 5)
    cv2.line(crop, (70, 90), (width - 70, height - 90), (65, 75, 130), 4)
    cv2.circle(crop, (width // 2, height // 2), 50, (130, 70, 160), -1)
    return crop


class TestStage5FixturePairs(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage5_pairs_")
        _create_synthetic_fixture(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_builds_six_pairs(self):
        pairs = build_fixture_pairs(self.tmpdir)

        self.assertEqual(
            [p.name for p in pairs],
            [
                "empty_to_empty",
                "empty_to_one_card",
                "empty_to_three_cards",
                "one_card_to_three_cards",
                "one_card_to_empty",
                "three_cards_to_empty",
            ],
        )

    def test_removed_pairs_use_previous_frame(self):
        for pair_name, _, _, change_type, source_frame in PAIR_DEFINITIONS:
            if change_type == "removed":
                self.assertEqual(source_frame, "previous", pair_name)


class TestStage5CropQualityMetrics(unittest.TestCase):
    def test_quality_metrics_on_valid_synthetic_crop(self):
        result = evaluate_crop_quality(_synthetic_crop(), crop_index=1)
        metrics = result.metrics

        self.assertGreater(metrics.crop_quality_score, 0.0)
        self.assertGreater(metrics.identification_readiness_score, 0.0)
        self.assertIn(metrics.crop_quality_status, {"PASS", "YELLOW", "FAIL"})
        self.assertGreater(metrics.brightness_mean, 0.0)
        self.assertGreater(metrics.contrast_score, 0.0)
        self.assertGreater(metrics.variance_of_laplacian, 0.0)
        self.assertGreaterEqual(metrics.edge_density_score, 0.0)

    def test_blurry_crop_lowers_sharpness_score(self):
        sharp = _synthetic_crop()
        blurry = cv2.GaussianBlur(sharp, (31, 31), 0)

        sharp_result = evaluate_crop_quality(sharp, crop_index=1)
        blurry_result = evaluate_crop_quality(blurry, crop_index=1)

        self.assertLess(
            blurry_result.metrics.variance_of_laplacian_blur_score,
            sharp_result.metrics.variance_of_laplacian_blur_score,
        )

    def test_overexposed_crop_sets_flag_or_ratio(self):
        crop = np.full((495, 300, 3), 255, dtype=np.uint8)

        result = evaluate_crop_quality(crop, crop_index=1)
        metrics = result.metrics

        self.assertGreater(metrics.overexposed_pixel_ratio, 0.9)
        self.assertTrue(
            "TOO_BRIGHT" in metrics.quality_flags or "TOP_REFLECTION_RISK" in metrics.quality_flags
        )

    def test_bad_aspect_sets_flag_or_lowers_score(self):
        crop = _synthetic_crop(width=300, height=300)

        result = evaluate_crop_quality(crop, crop_index=1)
        metrics = result.metrics

        self.assertTrue("BAD_ASPECT" in metrics.quality_flags or metrics.aspect_ratio_error_score < 0.75)


class TestStage5BenchmarkOutputs(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage5_benchmark_")
        _create_synthetic_fixture(self.tmpdir)
        self.output_dir = os.path.join(self.tmpdir, "output")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_to_empty_gives_no_crops_and_pass(self):
        summary = run_benchmark(self.tmpdir, self.output_dir)
        row = next(item for item in summary["rows"] if item["pair"] == "empty_to_empty")

        self.assertEqual(row["crop_count"], 0)
        self.assertIn(row["verdict"], {"PASS", "PASS_NO_CROPS"})

    def test_matrix_has_required_columns(self):
        run_benchmark(self.tmpdir, self.output_dir)

        with open(os.path.join(self.output_dir, "matrix.csv"), newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))

        for column in MATRIX_COLUMNS:
            self.assertIn(column, header)

    def test_report_has_provisional_manual_review_and_threshold_status(self):
        summary = run_benchmark(self.tmpdir, self.output_dir)

        report_path = os.path.join(self.output_dir, "report.json")
        with open(report_path, "r", encoding="utf-8") as handle:
            report = json.load(handle)

        self.assertEqual(summary["recommended_method"], "quality_metric_suite_v1")
        self.assertEqual(report["recommendation_status"], "PROVISIONAL_RECOMMENDED")
        self.assertTrue(report["manual_review_required"])
        self.assertEqual(report["threshold_status"], "BENCHMARK_HEURISTIC_ONLY")
        self.assertIn("manual_review_paths", report)

    def test_no_identification_files_are_generated(self):
        run_benchmark(self.tmpdir, self.output_dir)

        forbidden = {
            "recognized_card.json",
            "orb_matches.png",
            "template_match.png",
            "classification.json",
            "ocr_result.json",
        }
        for root, _, files in os.walk(self.output_dir):
            for fname in files:
                self.assertNotIn(fname, forbidden, f"Forbidden identification file found: {fname}")

    def test_manual_review_paths_all_exist(self):
        summary = run_benchmark(self.tmpdir, self.output_dir)
        paths = summary["manual_review_paths"]

        self.assertEqual(len(paths), 6)
        for path in paths:
            self.assertTrue(os.path.exists(path), path)
            self.assertIsNotNone(cv2.imread(path, cv2.IMREAD_COLOR), path)


if __name__ == "__main__":
    unittest.main()
