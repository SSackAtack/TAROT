import unittest

import cv2
import numpy as np

from tarotvision.card_detection_profiles import (
    DetectionProfile,
    find_card_quads_multi_profile,
)
from tarotvision.background_model import BackgroundModel


class CardDetectionProfilesTest(unittest.TestCase):
    def test_detects_dark_card_on_dark_green_background_with_bright_border(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        frame[:, :] = (20, 55, 35)
        cv2.rectangle(frame, (325, 171), (475, 429), (18, 24, 22), -1)
        cv2.rectangle(frame, (325, 171), (475, 429), (120, 150, 130), 3)

        result = find_card_quads_multi_profile(frame)

        self.assertGreaterEqual(len(result.quads), 1)
        self.assertIn(result.best_profile, {"canny_low", "adaptive_light", "adaptive_dark"})

    def test_deduplicates_same_quad_from_multiple_profiles(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(frame, (325, 171), (475, 429), (255, 255, 255), -1)

        result = find_card_quads_multi_profile(frame)

        self.assertEqual(len(result.quads), 1)

    def test_returns_debug_counts_per_profile(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)

        result = find_card_quads_multi_profile(frame)

        self.assertIn("profiles", result.debug)
        self.assertGreaterEqual(len(result.debug["profiles"]), 3)
        self.assertIn("quads_final", result.debug)
        self.assertIn("background_mask_nonzero_ratio", result.debug)
        for profile in result.debug["profiles"]:
            self.assertIn("min_area_rect_candidates", profile)
            self.assertIn("min_area_rect_accepted", profile)

    def test_accepts_custom_profile_list(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        profiles = [DetectionProfile("custom", "canny", canny_low=10, canny_high=40)]

        result = find_card_quads_multi_profile(frame, profiles=profiles)

        self.assertEqual(result.debug["profiles"][0]["name"], "custom")

    def test_adds_background_diff_profile_when_model_is_active(self):
        empty = np.zeros((600, 800, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        frame = empty.copy()
        cv2.rectangle(frame, (325, 171), (475, 429), (90, 95, 90), -1)
        model = BackgroundModel()
        model.capture(empty)

        result = find_card_quads_multi_profile(frame, background_model=model)

        profile_names = [profile["name"] for profile in result.debug["profiles"]]
        self.assertIn("background_diff", profile_names)
        self.assertIsInstance(result.debug["background_mask_nonzero_ratio"], float)

    def test_min_area_rect_fallback_detects_ragged_card_outline(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(frame, (325, 170), (475, 430), (255, 255, 255), -1)
        # Missing/overexposed edge fragment: strict approxPolyDP no longer sees
        # a convex 4-point contour, but the card envelope is still recoverable.
        cv2.rectangle(frame, (440, 250), (500, 320), (0, 0, 0), -1)

        result = find_card_quads_multi_profile(frame)

        self.assertGreaterEqual(len(result.quads), 1)
        min_rect_profile = next(
            profile for profile in result.debug["profiles"]
            if profile["name"] == "min_area_rect"
        )
        self.assertGreaterEqual(min_rect_profile["min_area_rect_accepted"], 1)

    def test_min_area_rect_fallback_does_not_detect_empty_mat(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        frame[:, :] = (20, 55, 35)

        result = find_card_quads_multi_profile(frame)

        self.assertEqual(len(result.quads), 0)
        min_rect_profile = next(
            profile for profile in result.debug["profiles"]
            if profile["name"] == "min_area_rect"
        )
        self.assertEqual(min_rect_profile["min_area_rect_accepted"], 0)


if __name__ == "__main__":
    unittest.main()
