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

    def test_capture_many_uses_median_reference(self):
        base = np.zeros((40, 60, 3), dtype=np.uint8)
        base[:, :] = (20, 55, 35)
        noisy = base.copy()
        noisy[5, 5] = (255, 255, 255)
        darker = base.copy()
        darker[:, :] = (18, 53, 33)

        model = BackgroundModel()
        model.capture_many([base, noisy, darker])

        mask = model.foreground_mask(base, threshold=20)
        self.assertEqual(int(np.count_nonzero(mask)), 0)

    def test_changed_ratio_reports_foreground_fraction(self):
        empty = np.zeros((100, 100, 3), dtype=np.uint8)
        frame = empty.copy()
        cv2.rectangle(frame, (30, 20), (70, 80), (255, 255, 255), -1)

        model = BackgroundModel()
        model.capture(empty)

        ratio = model.changed_ratio(frame, threshold=20)

        self.assertGreater(ratio, 0.20)
        self.assertLess(ratio, 0.30)

    def test_uncaptured_model_reports_inactive(self):
        model = BackgroundModel()

        self.assertFalse(model.active)
        self.assertIsNone(model.foreground_mask(np.zeros((10, 10, 3), dtype=np.uint8)))

    def test_clear_deactivates_model(self):
        model = BackgroundModel()
        model.capture(np.zeros((10, 10, 3), dtype=np.uint8))

        model.clear()

        self.assertFalse(model.active)


if __name__ == "__main__":
    unittest.main()
