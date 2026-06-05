"""Tests for the offline Stage 6 real-camera quality gate."""
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_real_camera_quality_gate import (
    ACCEPT, MANUAL, RETRY, build_highlight_mask, evaluate_quality_gate,
)
from tools.cv_detection_lab.stage6_real_camera_quality_gate_benchmark import _rate


class TestStage6RealCameraQualityGate(unittest.TestCase):
    def test_large_local_glare_requests_retry_or_manual_review(self):
        crop = _textured_crop()
        cv2.circle(crop, (100, 160), 58, (210, 210, 210), -1)

        result, mask = evaluate_quality_gate(crop, confidence_score=0.01, confidence_gap=0.0)

        self.assertIn(result.decision, {RETRY, MANUAL})
        self.assertGreater(np.count_nonzero(mask), 0)
        self.assertEqual(result.threshold_scope, "BENCHMARK_HEURISTIC_ONLY")

    def test_clear_textured_crop_is_accepted(self):
        result, _mask = evaluate_quality_gate(_textured_crop(), confidence_score=0.20, confidence_gap=0.15)
        self.assertEqual(result.decision, ACCEPT)

    def test_low_match_signal_escalates_clear_crop_to_manual_review(self):
        result, _mask = evaluate_quality_gate(_textured_crop(), confidence_score=0.01, confidence_gap=0.0)
        self.assertEqual(result.decision, MANUAL)
        self.assertIn("LOW_MATCH_SIGNAL", result.reasons)

    def test_benchmark_rate_handles_empty_and_nonempty_sets(self):
        self.assertIsNone(_rate([], lambda row: True))
        self.assertEqual(_rate([{"ok": True}, {"ok": False}], lambda row: row["ok"]), 0.5)

    def test_highlight_mask_matches_crop_shape(self):
        crop = _textured_crop()
        mask = build_highlight_mask(crop)
        self.assertEqual(mask.shape, crop.shape[:2])


def _textured_crop():
    image = np.full((330, 200, 3), (25, 85, 165), dtype=np.uint8)
    cv2.rectangle(image, (8, 8), (191, 321), (220, 60, 20), 4)
    for y in range(30, 310, 25):
        cv2.line(image, (20, y), (180, y + 10), (20, 70, 230), 2)
    cv2.circle(image, (100, 150), 50, (220, 40, 20), 3)
    return image


if __name__ == "__main__":
    unittest.main()
