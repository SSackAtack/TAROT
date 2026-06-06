import unittest

import cv2
import numpy as np

from tarotvision.background_model import BackgroundModel
from tarotvision.change_detection import ChangeDetector, ChangeDetectorConfig


class ChangeDetectorTest(unittest.TestCase):
    def empty(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        frame[:, :] = (20, 55, 35)
        return frame

    def with_card(self, frame, color=(90, 90, 85)):
        result = frame.copy()
        cv2.rectangle(result, (120, 50), (180, 150), color, -1)
        return result

    def model(self, empty):
        background = BackgroundModel()
        background.capture(empty)
        return background

    def test_classifies_added_region_using_empty_roi(self):
        empty = self.empty()
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(empty, self.with_card(empty), empty_reference=self.model(empty))

        self.assertFalse(result.global_shift)
        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "added")

    def test_classifies_removed_region_using_previous_and_current_empty_roi(self):
        empty = self.empty()
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(self.with_card(empty), empty, empty_reference=self.model(empty))

        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "removed")

    def test_classifies_moved_or_replaced_when_both_rois_are_foreground(self):
        empty = self.empty()
        previous = self.with_card(empty, color=(90, 90, 85))
        current = self.with_card(empty, color=(140, 130, 120))
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(previous, current, empty_reference=self.model(empty))

        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "moved_or_replaced")

    def test_ignores_tiny_noise(self):
        empty = self.empty()
        current = empty.copy()
        cv2.circle(current, (20, 20), 3, (255, 255, 255), -1)
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03))

        result = detector.detect(empty, current, empty_reference=self.model(empty))

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
