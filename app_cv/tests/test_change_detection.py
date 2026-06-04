import unittest

import cv2
import numpy as np

from tarotvision.background_model import BackgroundModel
from tarotvision.change_detection import ChangeDetector, ChangeDetectorConfig


class ChangeDetectorTest(unittest.TestCase):
    def test_detects_added_card_sized_region(self):
        empty = np.zeros((200, 300, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        previous = empty.copy()
        current = empty.copy()
        cv2.rectangle(current, (120, 50), (180, 150), (90, 90, 85), -1)

        background = BackgroundModel()
        background.capture(empty)
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(previous, current, empty_reference=background)

        self.assertFalse(result.global_shift)
        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "added_or_moved")

    def test_detects_removed_card_sized_region(self):
        empty = np.zeros((200, 300, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        previous = empty.copy()
        cv2.rectangle(previous, (120, 50), (180, 150), (90, 90, 85), -1)
        current = empty.copy()

        background = BackgroundModel()
        background.capture(empty)
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(previous, current, empty_reference=background)

        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "removed")

    def test_ignores_tiny_change(self):
        empty = np.zeros((200, 300, 3), dtype=np.uint8)
        previous = empty.copy()
        current = empty.copy()
        cv2.circle(current, (20, 20), 3, (255, 255, 255), -1)

        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03))

        result = detector.detect(previous, current)

        self.assertEqual(result.regions, [])
        self.assertGreaterEqual(result.ignored_small_count, 1)

    def test_flags_global_shift(self):
        previous = np.zeros((200, 300, 3), dtype=np.uint8)
        current = np.full((200, 300, 3), 80, dtype=np.uint8)

        detector = ChangeDetector(ChangeDetectorConfig(global_shift_ratio=0.45))

        result = detector.detect(previous, current)

        self.assertTrue(result.global_shift)
        self.assertEqual(result.regions, [])


if __name__ == "__main__":
    unittest.main()
