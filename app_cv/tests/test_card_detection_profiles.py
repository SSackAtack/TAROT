import unittest

import cv2
import numpy as np

from tarotvision.card_detection_profiles import (
    DetectionProfile,
    find_card_quads_multi_profile,
)


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

    def test_accepts_custom_profile_list(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        profiles = [DetectionProfile("custom", "canny", canny_low=10, canny_high=40)]

        result = find_card_quads_multi_profile(frame, profiles=profiles)

        self.assertEqual(result.debug["profiles"][0]["name"], "custom")


if __name__ == "__main__":
    unittest.main()
