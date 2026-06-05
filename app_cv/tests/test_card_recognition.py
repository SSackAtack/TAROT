import unittest
import os
from unittest.mock import MagicMock, patch

import numpy as np

from tarotvision.card_recognition import (
    build_variant_names,
    NORMALIZED_CARD_WIDTH,
    NORMALIZED_CARD_HEIGHT,
    deskew_card_crop,
    recognize_card_crop,
    recognize_card_crop_with_debug,
    load_reference_cards,
    resolve_orientation_with_margin,
)


class VariantNamesTest(unittest.TestCase):
    def test_builds_upright_and_reversed(self):
        variants = build_variant_names("17_star")
        self.assertEqual(variants, ["17_star:upright", "17_star:reversed"])

    def test_builds_for_any_card_name(self):
        variants = build_variant_names("00_fool")
        self.assertEqual(variants, ["00_fool:upright", "00_fool:reversed"])


class ResolveOrientationWithMarginTest(unittest.TestCase):
    def test_defaults_to_upright_when_reversed_score_is_only_slightly_better(self):
        orientation = resolve_orientation_with_margin(
            upright_score=100.0,
            reversed_score=104.0,
            margin_ratio=0.10,
        )

        self.assertEqual(orientation, "upright")

    def test_reports_reversed_when_reversed_score_has_clear_margin(self):
        orientation = resolve_orientation_with_margin(
            upright_score=100.0,
            reversed_score=125.0,
            margin_ratio=0.10,
        )

        self.assertEqual(orientation, "reversed")

    def test_reports_reversed_when_no_upright_match_exists(self):
        orientation = resolve_orientation_with_margin(
            upright_score=0.0,
            reversed_score=12.0,
            margin_ratio=0.10,
        )

        self.assertEqual(orientation, "reversed")


class NormalizedSizeTest(unittest.TestCase):
    def test_aspect_ratio_is_tarot(self):
        ratio = NORMALIZED_CARD_HEIGHT / NORMALIZED_CARD_WIDTH
        self.assertAlmostEqual(ratio, 1.72, places=2)


class DeskewCardCropTest(unittest.TestCase):
    def test_returns_normalized_size(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        # Syntetyczny quad — prosty prostokat bez perspektywy
        quad = np.array([
            [[100, 100]],
            [[100, 272]],
            [[200, 272]],
            [[200, 100]],
        ], dtype=np.float32)

        source_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Rysujemy bialy prostokat w tym obszarze zeby miec cos do cropowania
        cv2.rectangle(source_frame, (100, 100), (200, 272), (255, 255, 255), -1)

        crop = deskew_card_crop(source_frame, quad)

        self.assertEqual(crop.shape[1], NORMALIZED_CARD_WIDTH)
        self.assertEqual(crop.shape[0], NORMALIZED_CARD_HEIGHT)

    def test_returns_grayscale(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        quad = np.array([
            [[100, 100]], [[100, 272]], [[200, 272]], [[200, 100]]
        ], dtype=np.float32)
        source_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        crop = deskew_card_crop(source_frame, quad)

        # Wynik powinien byc grayscale (2D)
        self.assertEqual(len(crop.shape), 2)


class RecognizeCardCropTest(unittest.TestCase):
    def test_returns_none_for_empty_reference(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        gray_crop = np.zeros((NORMALIZED_CARD_HEIGHT, NORMALIZED_CARD_WIDTH),
                             dtype=np.uint8)
        orb = cv2.ORB_create(nfeatures=500)
        flann_params = dict(algorithm=6, table_number=6, key_size=12,
                            multi_probe_level=1)
        matcher = cv2.FlannBasedMatcher(flann_params, dict(checks=50))

        result = recognize_card_crop(gray_crop, {}, orb, matcher)

        self.assertIsNone(result)

    def test_debug_reports_best_rejected_match_when_good_matches_below_threshold(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        mock_card_matcher = MagicMock()
        mock_card_matcher.knnMatch.return_value = [
            [cv2.DMatch(i, i, 1.0), cv2.DMatch(i, i, 10.0)] for i in range(10)
        ]
        reference_cards = {
            "Gilded_08": {
                "keypoints": [cv2.KeyPoint(float(i), 0.0, 1.0) for i in range(20)],
                "descriptors": np.zeros((20, 32), dtype=np.uint8),
                "matcher": mock_card_matcher,
            }
        }
        mock_orb = MagicMock()
        mock_orb.detectAndCompute.return_value = (
            [cv2.KeyPoint(float(i), 0.0, 1.0) for i in range(20)],
            np.zeros((20, 32), dtype=np.uint8),
        )

        result, debug = recognize_card_crop_with_debug(
            np.zeros((NORMALIZED_CARD_HEIGHT, NORMALIZED_CARD_WIDTH), dtype=np.uint8),
            reference_cards,
            mock_orb,
            MagicMock(),
            min_good_matches=12,
        )

        self.assertIsNone(result)
        self.assertEqual(debug.reject_reason, "insufficient_good_matches")
        self.assertEqual(debug.crop_keypoints, 20)
        self.assertEqual(debug.top_matches[0]["name"], "Gilded_08")
        self.assertEqual(debug.top_matches[0]["match_count"], 10)


class LoadReferenceCardsTest(unittest.TestCase):
    def test_returns_empty_dict_for_missing_directory(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        orb = cv2.ORB_create(nfeatures=500)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        result = load_reference_cards("/nonexistent/path", orb, clahe)

        self.assertEqual(result, {})


class HomographyOrientationTest(unittest.TestCase):
    @patch("cv2.findHomography")
    def test_homography_keeps_upright_when_no_rotation(self, mock_find_homography):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        H_identity = np.eye(3, dtype=np.float32)
        mock_find_homography.return_value = (H_identity, np.ones(20, dtype=np.uint8))

        ref_cards = {
            "15_devil": {
                "keypoints": [cv2.KeyPoint(0, 0, 1)] * 20,
                "descriptors": np.zeros((20, 32), dtype=np.uint8),
                "reversed_keypoints": [cv2.KeyPoint(0, 0, 1)] * 20,
                "reversed_descriptors": np.zeros((20, 32), dtype=np.uint8),
            }
        }

        mock_orb = MagicMock()
        mock_orb.detectAndCompute.return_value = (
            [cv2.KeyPoint(0, 0, 1)] * 20,
            np.zeros((20, 32), dtype=np.uint8),
        )

        mock_matcher = MagicMock()
        mock_matcher.knnMatch.return_value = [
            [cv2.DMatch(i, i, 1.0), cv2.DMatch(i, i, 10.0)] for i in range(20)
        ]

        crop = np.zeros((516, 300), dtype=np.uint8)
        result = recognize_card_crop(crop, ref_cards, mock_orb, mock_matcher)

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "15_devil")
        self.assertEqual(result["orientation"], "upright")
        self.assertEqual(result["homography_angle_deg"], 0.0)

    @patch("cv2.findHomography")
    def test_homography_flips_to_reversed_when_180_rotation(self, mock_find_homography):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        H_reversed = np.array([
            [-1.0, 0.0, 100.0],
            [0.0, -1.0, 200.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        mock_find_homography.return_value = (H_reversed, np.ones(20, dtype=np.uint8))

        ref_cards = {
            "15_devil": {
                "keypoints": [cv2.KeyPoint(0, 0, 1)] * 20,
                "descriptors": np.zeros((20, 32), dtype=np.uint8),
                "reversed_keypoints": [cv2.KeyPoint(0, 0, 1)] * 20,
                "reversed_descriptors": np.zeros((20, 32), dtype=np.uint8),
            }
        }

        mock_orb = MagicMock()
        mock_orb.detectAndCompute.return_value = (
            [cv2.KeyPoint(0, 0, 1)] * 20,
            np.zeros((20, 32), dtype=np.uint8),
        )

        mock_matcher = MagicMock()
        mock_matcher.knnMatch.return_value = [
            [cv2.DMatch(i, i, 1.0), cv2.DMatch(i, i, 10.0)] for i in range(20)
        ]

        crop = np.zeros((516, 300), dtype=np.uint8)
        result = recognize_card_crop(crop, ref_cards, mock_orb, mock_matcher)

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "15_devil")
        self.assertEqual(result["orientation"], "reversed")
        self.assertAlmostEqual(abs(result["homography_angle_deg"]), 180.0, places=1)


class FastMatcherHomographyTest(unittest.TestCase):
    @patch("cv2.findHomography")
    def test_fast_path_keeps_upright_when_no_rotation(self, mock_find_homography):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        H_identity = np.eye(3, dtype=np.float32)
        mock_find_homography.return_value = (H_identity, np.ones(20, dtype=np.uint8))

        mock_card_matcher = MagicMock()
        mock_card_matcher.knnMatch.return_value = [
            [cv2.DMatch(i, i, 1.0), cv2.DMatch(i, i, 10.0)] for i in range(20)
        ]

        ref_cards = {
            "15_devil": {
                "keypoints": [cv2.KeyPoint(0, 0, 1)] * 20,
                "descriptors": np.zeros((20, 32), dtype=np.uint8),
                "matcher": mock_card_matcher,
            }
        }

        mock_orb = MagicMock()
        mock_orb.detectAndCompute.return_value = (
            [cv2.KeyPoint(0, 0, 1)] * 20,
            np.zeros((20, 32), dtype=np.uint8),
        )

        # Global matcher passed in is not used in fast path
        mock_global_matcher = MagicMock()

        crop = np.zeros((516, 300), dtype=np.uint8)
        result = recognize_card_crop(crop, ref_cards, mock_orb, mock_global_matcher)

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "15_devil")
        self.assertEqual(result["orientation"], "upright")
        self.assertEqual(result["homography_angle_deg"], 0.0)
        
        # Verify card matcher was called, and global matcher was NOT called
        mock_card_matcher.knnMatch.assert_called_once()
        mock_global_matcher.knnMatch.assert_not_called()

    @patch("cv2.findHomography")
    def test_fast_path_flips_to_reversed_when_180_rotation(self, mock_find_homography):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        H_reversed = np.array([
            [-1.0, 0.0, 100.0],
            [0.0, -1.0, 200.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)
        mock_find_homography.return_value = (H_reversed, np.ones(20, dtype=np.uint8))

        mock_card_matcher = MagicMock()
        mock_card_matcher.knnMatch.return_value = [
            [cv2.DMatch(i, i, 1.0), cv2.DMatch(i, i, 10.0)] for i in range(20)
        ]

        ref_cards = {
            "15_devil": {
                "keypoints": [cv2.KeyPoint(0, 0, 1)] * 20,
                "descriptors": np.zeros((20, 32), dtype=np.uint8),
                "matcher": mock_card_matcher,
            }
        }

        mock_orb = MagicMock()
        mock_orb.detectAndCompute.return_value = (
            [cv2.KeyPoint(0, 0, 1)] * 20,
            np.zeros((20, 32), dtype=np.uint8),
        )

        mock_global_matcher = MagicMock()

        crop = np.zeros((516, 300), dtype=np.uint8)
        result = recognize_card_crop(crop, ref_cards, mock_orb, mock_global_matcher)

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "15_devil")
        self.assertEqual(result["orientation"], "reversed")
        self.assertAlmostEqual(abs(result["homography_angle_deg"]), 180.0, places=1)
        
        mock_card_matcher.knnMatch.assert_called_once()
        mock_global_matcher.knnMatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
