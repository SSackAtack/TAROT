import unittest

import numpy as np

from tarotvision.snapshot_quality import score_snapshot, choose_best_snapshot


class SnapshotQualityTest(unittest.TestCase):
    def test_rejects_too_dark_frame(self):
        frame = np.zeros((40, 40), dtype=np.uint8)

        result = score_snapshot(frame)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reject_reason, "too_dark")

    def test_accepts_high_contrast_readable_frame(self):
        frame = np.zeros((40, 40), dtype=np.uint8)
        frame[10:30, 10:30] = 255

        result = score_snapshot(frame, min_blur_score=10.0)

        self.assertTrue(result.accepted)
        self.assertGreater(result.quality_score, 0.0)

    def test_choose_best_snapshot_ignores_rejected_frames(self):
        dark = np.zeros((40, 40), dtype=np.uint8)
        readable = np.zeros((40, 40), dtype=np.uint8)
        readable[10:30, 10:30] = 255

        selected = choose_best_snapshot([dark, readable], min_blur_score=10.0)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.index, 1)
        self.assertTrue(selected.quality.accepted)

    def test_choose_best_snapshot_returns_none_when_all_rejected(self):
        dark = np.zeros((40, 40), dtype=np.uint8)

        selected = choose_best_snapshot([dark])

        self.assertIsNone(selected)


if __name__ == "__main__":
    unittest.main()
