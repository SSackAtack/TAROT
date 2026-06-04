"""Tests for the offline Stage 6 RWS expansion benchmark."""
import unittest
import os
import tempfile
import shutil
import json
import numpy as np
import cv2

from tools.cv_detection_lab.stage6_rws_expansion_benchmark import (
    extract_card,
    run_rws_benchmark,
    build_benchmark_summary,
)
from tools.cv_detection_lab.stage6_real_camera_quality_gate import (
    ACCEPT,
    MANUAL,
    RETRY,
)


class TestStage6RwsExpansionBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_extract_card_on_synthetic_frame(self):
        frame = np.full((1080, 1920, 3), 200, dtype=np.uint8)
        card_pts = np.array([
            [800, 400],
            [1100, 400],
            [1100, 900],
            [800, 900]
        ], dtype=np.int32)
        cv2.fillPoly(frame, [card_pts], (50, 50, 50))
        cv2.rectangle(frame, (820, 420), (1080, 880), (100, 100, 100), -1)

        crop = extract_card(frame)
        self.assertEqual(crop.shape, (330, 200, 3))

    def test_run_rws_benchmark_with_invalid_args_exits(self):
        with self.assertRaises(SystemExit) as cm:
            run_rws_benchmark(
                manifest_path="nonexistent_manifest.json",
                ground_truth_path="nonexistent_gt.json",
                reference_deck_dir=os.path.join(self.tmp_dir, "ref"),
                output_dir=os.path.join(self.tmp_dir, "out")
            )
        self.assertEqual(cm.exception.code, 2)

    def test_run_rws_benchmark_with_missing_references_exits(self):
        manifest_path = os.path.join(self.tmp_dir, "manifest.json")
        gt_path = os.path.join(self.tmp_dir, "ground_truth.json")

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"fixture_id": "stage6_real_camera_fixture_expansion_rws_minimal", "manifest_version": 1, "samples": []}, f)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump({"fixture_id": "stage6_real_camera_fixture_expansion_rws_minimal", "labels": {}}, f)

        with self.assertRaises(SystemExit) as cm:
            run_rws_benchmark(
                manifest_path=manifest_path,
                ground_truth_path=gt_path,
                reference_deck_dir=os.path.join(self.tmp_dir, "ref"),
                output_dir=os.path.join(self.tmp_dir, "out")
            )
        self.assertEqual(cm.exception.code, 3)

    def test_build_benchmark_summary_aggregates_extraction_failures(self):
        # 1. Test case: one extraction failure, one successful ORB run (correct), one successful ORB run (incorrect, retried)
        results = [
            {
                "sample_id": "sample_1",
                "category": "rws_bright_clear",
                "expected_card_id": "RWS_01",
                "expected_orientation": "upright",
                "quality_expectation": "PASS_OR_YELLOW",
                "quality_gate_decision": MANUAL,
                "quality_gate_reasons": ["EXTRACTION_FAILED"],
                "predicted_card_id": None,
                "top1_correct": False,
                "top3_contains_expected": False,
                "confidence_score": 0.0,
                "confidence_gap": 0.0,
                "runtime_ms": "",
                "extracted_ok": False,
                "extraction_error": "No contour",
                "orb_attempted": False,
            },
            {
                "sample_id": "sample_2",
                "category": "rws_bright_clear",
                "expected_card_id": "RWS_02",
                "expected_orientation": "upright",
                "quality_expectation": "PASS_OR_YELLOW",
                "quality_gate_decision": ACCEPT,
                "quality_gate_reasons": [],
                "predicted_card_id": "RWS_02",
                "top1_correct": True,
                "top3_contains_expected": True,
                "confidence_score": 0.5,
                "confidence_gap": 0.3,
                "runtime_ms": 120.0,
                "extracted_ok": True,
                "extraction_error": "",
                "orb_attempted": True,
            },
            {
                "sample_id": "sample_3",
                "category": "rws_bright_glare",
                "expected_card_id": "RWS_03",
                "expected_orientation": "reversed",
                "quality_expectation": "YELLOW",
                "quality_gate_decision": RETRY,
                "quality_gate_reasons": ["GLARE"],
                "predicted_card_id": "RWS_04",
                "top1_correct": False,
                "top3_contains_expected": True,
                "confidence_score": 0.2,
                "confidence_gap": 0.05,
                "runtime_ms": 110.0,
                "extracted_ok": True,
                "extraction_error": "",
                "orb_attempted": True,
            }
        ]
        runtimes = [120.0, 110.0]

        summary = build_benchmark_summary(results, runtimes, fixture_id="test_fixture")

        self.assertEqual(summary["sample_count"], 3)
        self.assertEqual(summary["processed_count"], 2)
        self.assertEqual(summary["extraction_failed_count"], 1)
        self.assertEqual(summary["orb_attempted_count"], 2)

        # ORB accuracy on all samples (including the failed extraction, which is treated as incorrect)
        # 1 correct of 3 -> 0.333333
        self.assertAlmostEqual(summary["orb_top1_accuracy_all"], 0.333333, places=5)
        self.assertAlmostEqual(summary["orb_top3_accuracy_all"], 0.666667, places=5)

        # ORB accuracy on extracted only (excluding the failed extraction)
        # 1 correct of 2 attempted -> 0.5
        self.assertAlmostEqual(summary["orb_top1_accuracy_extracted_only"], 0.5, places=5)
        self.assertAlmostEqual(summary["orb_top3_accuracy_extracted_only"], 1.0, places=5)

        # Quality Gate decisions distribution
        self.assertEqual(summary["accept_count"], 1)
        self.assertEqual(summary["retry_capture_count"], 1)
        self.assertEqual(summary["manual_review_count"], 1) # Failed extraction maps to MANUAL with reason EXTRACTION_FAILED

        # ACCEPT subset accuracy: sample_2 is accepted and correct -> 100%
        self.assertEqual(summary["orb_top1_accuracy_accept_subset"], 1.0)
        self.assertEqual(summary["orb_top3_accuracy_accept_subset"], 1.0)

    def test_build_benchmark_summary_handles_empty_runtimes(self):
        # When no runtimes are recorded, statistical summary shouldn't crash and should return None
        results = [
            {
                "sample_id": "sample_1",
                "category": "rws_bright_clear",
                "expected_card_id": "RWS_01",
                "expected_orientation": "upright",
                "quality_expectation": "PASS_OR_YELLOW",
                "quality_gate_decision": MANUAL,
                "quality_gate_reasons": ["EXTRACTION_FAILED"],
                "predicted_card_id": None,
                "top1_correct": False,
                "top3_contains_expected": False,
                "confidence_score": 0.0,
                "confidence_gap": 0.0,
                "runtime_ms": "",
                "extracted_ok": False,
                "extraction_error": "No contour",
                "orb_attempted": False,
            }
        ]
        runtimes = []
        summary = build_benchmark_summary(results, runtimes, fixture_id="test_fixture")

        self.assertIsNone(summary["runtime_proxy_mean_ms"])
        self.assertIsNone(summary["runtime_proxy_p50_ms"])
        self.assertIsNone(summary["runtime_proxy_p95_ms"])


if __name__ == "__main__":
    unittest.main()
