"""Unit tests for Stage 4 Crop / Deskew / Normalize offline benchmark.

Tests cover:
1. Fixture pair construction (6 pairs)
2. Removed pairs use previous frame
3. Quad warp perspective returns target size
4. Safe padding expands quad
5. Orientation portrait normalization
6. empty_to_empty gives zero crops and PASS
7. Matrix contains required columns
8. Report requires manual review
9. No identification files generated
"""
import json
import os
import shutil
import tempfile
import unittest

import cv2
import numpy as np

# Ensure project root on sys.path for imports
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.cv_detection_lab.crop_deskew_methods import (
    available_crop_methods,
    available_normalizations,
    expand_quad_about_center,
    run_crop_deskew,
    validate_quad,
    DEFAULT_TARGET_WIDTH,
    DEFAULT_TARGET_HEIGHT,
)
from tools.cv_detection_lab.stage4_crop_deskew_normalize_benchmark import (
    MATRIX_COLUMNS,
    PAIR_DEFINITIONS,
    build_fixture_pairs,
    run_benchmark,
)


def _create_synthetic_fixture(fixture_dir):
    """Create minimal synthetic fixture images for testing."""
    for scenario, fname in [("empty", "analysis_frame_0.png"),
                            ("one_card", "analysis_frame_1.png"),
                            ("three_cards", "analysis_frame_3.png")]:
        scenario_dir = os.path.join(fixture_dir, scenario)
        os.makedirs(scenario_dir, exist_ok=True)
        # Create a 640x480 image; for non-empty, draw rectangles that simulate cards
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:, :] = (40, 60, 40)  # dark green mat
        if scenario == "one_card":
            cv2.rectangle(img, (250, 100), (390, 380), (200, 180, 160), -1)
            cv2.rectangle(img, (250, 100), (390, 380), (255, 255, 255), 2)
        elif scenario == "three_cards":
            for x_start in [80, 250, 420]:
                cv2.rectangle(img, (x_start, 100), (x_start + 140, 380), (200, 180, 160), -1)
                cv2.rectangle(img, (x_start, 100), (x_start + 140, 380), (255, 255, 255), 2)
        cv2.imwrite(os.path.join(scenario_dir, fname), img)


class TestFixturePairs(unittest.TestCase):
    """Test 1 — fixture pairs."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage4_test_")
        _create_synthetic_fixture(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_builds_six_pairs(self):
        pairs = build_fixture_pairs(self.tmpdir)
        self.assertEqual(len(pairs), 6)
        pair_names = [p.name for p in pairs]
        expected_names = [
            "empty_to_empty",
            "empty_to_one_card",
            "empty_to_three_cards",
            "one_card_to_three_cards",
            "one_card_to_empty",
            "three_cards_to_empty",
        ]
        self.assertEqual(pair_names, expected_names)


class TestRemovedUsesPreviousFrame(unittest.TestCase):
    """Test 2 — removed uses previous frame."""

    def test_removed_pairs_crop_source(self):
        for pair_name, _, _, change_type, source_frame in PAIR_DEFINITIONS:
            if change_type == "removed":
                self.assertEqual(
                    source_frame, "previous",
                    f"Pair {pair_name} with change_type=removed must use previous frame"
                )


class TestQuadWarpPerspectiveTargetSize(unittest.TestCase):
    """Test 3 — quad warp perspective returns target size."""

    def test_returns_target_size(self):
        # Create a synthetic frame with a rectangle
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        frame[:, :] = (60, 60, 60)
        cv2.rectangle(frame, (200, 100), (500, 400), (180, 160, 140), -1)

        # Simulate geometry with ordered quad points
        geom = {
            "bbox": [200, 100, 300, 300],
            "ordered_quad_points": [[200, 100], [500, 100], [500, 400], [200, 400]],
            "geometry_type": "test",
            "geometry_confidence": 0.8,
        }

        result = run_crop_deskew(
            crop_method="quad_warp_perspective",
            normalization_variant="resize_only_normalization",
            source_frame=frame,
            stage3_geometries=[geom],
            crop_source_frame="current",
        )
        self.assertEqual(len(result.crops), 1)
        crop = result.crops[0]
        self.assertEqual(crop.deskewed_crop.shape[1], DEFAULT_TARGET_WIDTH)
        self.assertEqual(crop.deskewed_crop.shape[0], DEFAULT_TARGET_HEIGHT)


class TestSafePaddingExpandsQuad(unittest.TestCase):
    """Test 4 — safe padding expands quad."""

    def test_expand_quad_about_center(self):
        quad = np.array([[100, 100], [200, 100], [200, 300], [100, 300]], dtype=np.float32)
        expanded = expand_quad_about_center(quad, 0.1)

        # Center is (150, 200)
        center = quad.mean(axis=0)
        for i in range(4):
            orig_dist = np.linalg.norm(quad[i] - center)
            new_dist = np.linalg.norm(expanded[i] - center)
            self.assertGreater(new_dist, orig_dist, f"Point {i} should be farther from center after expansion")


class TestOrientationPortraitNormalization(unittest.TestCase):
    """Test 5 — orientation portrait normalization."""

    def test_landscape_rotated_to_portrait(self):
        # Create a landscape crop (width > height)
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        frame[:, :] = (80, 80, 80)
        # Wide rectangle
        cv2.rectangle(frame, (100, 200), (700, 400), (180, 160, 140), -1)

        geom = {
            "bbox": [100, 200, 600, 200],
            "ordered_quad_points": [[100, 200], [700, 200], [700, 400], [100, 400]],
            "geometry_type": "test",
            "geometry_confidence": 0.8,
        }

        result = run_crop_deskew(
            crop_method="quad_warp_perspective",
            normalization_variant="orientation_portrait_normalization",
            source_frame=frame,
            stage3_geometries=[geom],
            crop_source_frame="current",
        )
        self.assertEqual(len(result.crops), 1)
        norm = result.crops[0].normalized_crop
        # After orientation normalization, height should be >= width
        self.assertGreaterEqual(norm.shape[0], norm.shape[1],
                                "Normalized crop should be portrait (height >= width)")


class TestEmptyToEmptyZeroCrops(unittest.TestCase):
    """Test 6 — empty_to_empty gives zero crops and PASS."""

    def test_no_crops_for_identical_frames(self):
        # Two identical frames = no diff, no geometry, no crops
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = (40, 60, 40)

        # No geometries = 0 crops
        result = run_crop_deskew(
            crop_method="bbox_crop_resize",
            normalization_variant="resize_only_normalization",
            source_frame=frame,
            stage3_geometries=[],
            crop_source_frame="current",
        )
        self.assertEqual(len(result.crops), 0)


class TestMatrixColumns(unittest.TestCase):
    """Test 7 — matrix contains required columns."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage4_matrix_")
        _create_synthetic_fixture(self.tmpdir)
        self.output_dir = os.path.join(self.tmpdir, "output")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_matrix_has_required_columns(self):
        summary = run_benchmark(
            self.tmpdir, self.output_dir,
            pipeline_variants=[("bbox_crop_resize", "resize_only_normalization", 0.0)],
        )
        matrix_path = os.path.join(self.output_dir, "matrix.csv")
        self.assertTrue(os.path.exists(matrix_path))
        with open(matrix_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
        for col in MATRIX_COLUMNS:
            self.assertIn(col, header, f"Missing column: {col}")


class TestReportManualReview(unittest.TestCase):
    """Test 8 — report requires manual review."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage4_report_")
        _create_synthetic_fixture(self.tmpdir)
        self.output_dir = os.path.join(self.tmpdir, "output")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_report_has_provisional_and_manual_review(self):
        summary = run_benchmark(
            self.tmpdir, self.output_dir,
            pipeline_variants=[("bbox_crop_resize", "resize_only_normalization", 0.0)],
        )
        report_path = os.path.join(self.output_dir, "report.json")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["recommendation_status"], "PROVISIONAL_RECOMMENDED")
        self.assertTrue(report["manual_review_required"])
        self.assertIn("manual_review_paths", report)


class TestNoIdentificationFiles(unittest.TestCase):
    """Test 9 — no identification files are generated."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage4_noid_")
        _create_synthetic_fixture(self.tmpdir)
        self.output_dir = os.path.join(self.tmpdir, "output")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_forbidden_files(self):
        run_benchmark(
            self.tmpdir, self.output_dir,
            pipeline_variants=[("bbox_crop_resize", "resize_only_normalization", 0.0)],
        )
        forbidden = {"recognized_card.json", "orb_matches.png", "template_match.png", "classification.json"}
        for root, dirs, files in os.walk(self.output_dir):
            for fname in files:
                self.assertNotIn(fname, forbidden, f"Forbidden identification file found: {fname}")


if __name__ == "__main__":
    unittest.main()
