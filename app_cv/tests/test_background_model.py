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


if __name__ == "__main__":
    unittest.main()
