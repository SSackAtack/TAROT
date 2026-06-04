"""Tests for the offline Stage 6 real-camera identification benchmark."""
import os
import shutil
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_identification_methods import ReferenceCard
from tools.cv_detection_lab.stage6_real_camera_identification_benchmark import (
    MATRIX_COLUMNS,
    _summaries,
    extract_card,
)


class TestStage6RealCameraIdentificationBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_real_identification_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_extract_card_finds_dark_center_card(self):
        frame = np.full((720, 1280, 3), 190, dtype=np.uint8)
        card = np.full((330, 200, 3), 25, dtype=np.uint8)
        cv2.circle(card, (100, 130), 55, (10, 80, 220), -1)
        frame[220:550, 540:740] = card

        crop = extract_card(frame)

        self.assertEqual(crop.shape, (330, 200, 3))
        self.assertLess(float(crop.mean()), 100.0)

    def test_summaries_report_accuracy_far_similarity_and_runtime(self):
        rows = [
            self._row("orb_bfmatcher_ratio_test", "identify", True, True, False, "similar-1"),
            self._row("orb_bfmatcher_ratio_test", "reject", False, False, True, None),
        ]

        method = _summaries(rows, ("method",))[0]
        similarity = _summaries([rows[0]], ("method", "similarity_group"))[0]

        self.assertEqual(method["accuracy_top1"], 1.0)
        self.assertEqual(method["wrong_deck_false_accept_rate"], 1.0)
        self.assertEqual(method["p95_runtime_ms"], 12.0)
        self.assertEqual(similarity["similarity_group"], "similar-1")

    def test_matrix_contains_required_offline_audit_fields(self):
        for field in [
            "method", "sample_id", "category", "orientation", "similarity_group",
            "expected_behavior", "expected_card_id", "predicted_card_id",
            "top1_correct", "top3_contains_expected", "offline_accepted",
            "false_accept", "runtime_ms",
        ]:
            self.assertIn(field, MATRIX_COLUMNS)

    @staticmethod
    def _row(method, behavior, top1, top3, false_accept, similarity):
        return {
            "method": method, "expected_behavior": behavior, "top1_correct": top1,
            "top3_contains_expected": top3, "false_accept": false_accept,
            "confidence_gap": 0.1, "runtime_ms": 12.0, "similarity_group": similarity,
        }


if __name__ == "__main__":
    unittest.main()
