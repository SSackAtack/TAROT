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
    _load_rws_references,
    run_rws_benchmark,
)

class TestStage6RwsExpansionBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_extract_card_on_synthetic_frame(self):
        # Create a synthetic frame (e.g. 1920x1080) with a card shape in the center ROI.
        frame = np.full((1080, 1920, 3), 200, dtype=np.uint8)
        
        # Center of ROI: ROI is y in [129, 972], x in [192, 1728]
        # Draw a dark card shape at the center of the ROI
        # Card aspect ratio is roughly 0.6 (e.g. 300x500 pixels)
        card_pts = np.array([
            [800, 400],
            [1100, 400],
            [1100, 900],
            [800, 900]
        ], dtype=np.int32)
        cv2.fillPoly(frame, [card_pts], (50, 50, 50))
        
        # Add some texture to make it pass aspect ratio and contour detection
        cv2.rectangle(frame, (820, 420), (1080, 880), (100, 100, 100), -1)

        crop = extract_card(frame)
        self.assertEqual(crop.shape, (330, 200, 3))

    def test_run_rws_benchmark_with_invalid_args_exits(self):
        # Missing manifest/ground truth should exit with status 2
        with self.assertRaises(SystemExit) as cm:
            run_rws_benchmark(
                manifest_path="nonexistent_manifest.json",
                ground_truth_path="nonexistent_gt.json",
                reference_deck_dir=os.path.join(self.tmp_dir, "ref"),
                output_dir=os.path.join(self.tmp_dir, "out")
            )
        self.assertEqual(cm.exception.code, 2)

    def test_run_rws_benchmark_with_missing_references_exits(self):
        # Create fake manifest and ground_truth files
        manifest_path = os.path.join(self.tmp_dir, "manifest.json")
        gt_path = os.path.join(self.tmp_dir, "ground_truth.json")

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"fixture_id": "stage6_real_camera_fixture_expansion_rws_minimal", "manifest_version": 1, "samples": []}, f)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump({"fixture_id": "stage6_real_camera_fixture_expansion_rws_minimal", "labels": {}}, f)

        # Empty reference dir should exit with status 3
        with self.assertRaises(SystemExit) as cm:
            run_rws_benchmark(
                manifest_path=manifest_path,
                ground_truth_path=gt_path,
                reference_deck_dir=os.path.join(self.tmp_dir, "ref"),
                output_dir=os.path.join(self.tmp_dir, "out")
            )
        self.assertEqual(cm.exception.code, 3)


if __name__ == "__main__":
    unittest.main()
