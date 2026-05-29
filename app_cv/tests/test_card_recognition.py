import unittest
import os

import numpy as np

from tarotvision.card_recognition import (
    build_variant_names,
    NORMALIZED_CARD_WIDTH,
    NORMALIZED_CARD_HEIGHT,
    deskew_card_crop,
    recognize_card_crop,
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


if __name__ == "__main__":
    unittest.main()
