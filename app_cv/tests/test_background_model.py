import unittest

import cv2
import numpy as np

from tarotvision.background_model import BackgroundModel


class BackgroundModelTest(unittest.TestCase):
    def test_foreground_mask_detects_card_added_to_empty_mat(self):
        empty = np.zeros((100, 140, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        frame = empty.copy()
        cv2.rectangle(frame, (45, 20), (95, 80), (80, 90, 85), -1)

        model = BackgroundModel()
        model.capture(empty)
        mask = model.foreground_mask(frame, threshold=20)

        changed_ratio = float(np.count_nonzero(mask)) / mask.size
        self.assertGreater(changed_ratio, 0.15)

    def test_uncaptured_model_reports_inactive(self):
        model = BackgroundModel()

        self.assertFalse(model.active)
        self.assertIsNone(model.foreground_mask(np.zeros((10, 10, 3), dtype=np.uint8)))

    def test_clear_deactivates_model(self):
        model = BackgroundModel()
        model.capture(np.zeros((10, 10, 3), dtype=np.uint8))

        model.clear()

        self.assertFalse(model.active)

    def test_capture_many_uses_median_reference(self):
        model = BackgroundModel()
        frames = [
            np.full((10, 10, 3), 10, dtype=np.uint8),
            np.full((10, 10, 3), 20, dtype=np.uint8),
            np.full((10, 10, 3), 30, dtype=np.uint8),
        ]

        model.capture_many(frames)

        self.assertTrue(model.active)
        mask = model.foreground_mask(np.full((10, 10, 3), 20, dtype=np.uint8), threshold=5)
        self.assertEqual(float(np.count_nonzero(mask)), 0.0)

    def test_changed_ratio_reports_foreground_share(self):
        empty = np.zeros((100, 140, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        frame = empty.copy()
        cv2.rectangle(frame, (45, 20), (95, 80), (80, 90, 85), -1)

        model = BackgroundModel()
        model.capture(empty)

        self.assertGreater(model.changed_ratio(frame, threshold=20), 0.15)

    def test_roi_foreground_ratio_uses_same_roi_against_empty_reference(self):
        empty = np.zeros((100, 140, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        frame = empty.copy()
        cv2.rectangle(frame, (45, 20), (95, 80), (80, 90, 85), -1)

        model = BackgroundModel()
        model.capture(empty)

        card_ratio = model.roi_foreground_ratio(frame, (45, 20, 50, 60), threshold=20)
        empty_ratio = model.roi_foreground_ratio(frame, (0, 0, 20, 20), threshold=20)

        self.assertGreater(card_ratio, 0.8)
        self.assertLess(empty_ratio, 0.05)


if __name__ == "__main__":
    unittest.main()
