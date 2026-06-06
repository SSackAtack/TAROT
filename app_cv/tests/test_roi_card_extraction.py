import unittest

import cv2
import numpy as np

from tarotvision.roi_card_extraction import extract_card_quads_from_roi


class RoiCardExtractionTest(unittest.TestCase):
    def test_extracts_single_card_quad_from_diff_mask(self):
        roi_frame = np.zeros((160, 120, 3), dtype=np.uint8)
        roi_frame[:, :] = (20, 50, 35)
        cv2.rectangle(roi_frame, (28, 18), (92, 142), (100, 95, 85), -1)
        cv2.line(roi_frame, (40, 40), (82, 120), (170, 160, 145), 2)

        roi_mask = np.zeros((160, 120), dtype=np.uint8)
        roi_mask[18:143, 28:93] = 255

        result = extract_card_quads_from_roi(roi_frame, roi_mask)

        self.assertEqual(len(result.quads), 1)
        self.assertEqual(result.debug["source"], "offline_roi_extractor")
        self.assertEqual(result.debug["stage2_method"], "contour_external")
        self.assertEqual(result.debug["stage3_method"], "hybrid_edge_plus_contour")
        self.assertEqual(result.debug["stage4_crop_method"], "quad_warp_perspective_fixed_aspect")
        self.assertEqual(result.debug["stage5_quality_method"], "quality_metric_suite_v1")
        self.assertEqual(result.debug["quads_final"], 1)
        self.assertIn(result.debug["quality_status"], ["PASS", "YELLOW"])

        points = result.quads[0].reshape(4, 2)
        self.assertLessEqual(float(points[:, 0].min()), 29.0)
        self.assertGreaterEqual(float(points[:, 0].max()), 91.0)
        self.assertLessEqual(float(points[:, 1].min()), 19.0)
        self.assertGreaterEqual(float(points[:, 1].max()), 141.0)

    def test_empty_mask_returns_no_quad_with_diagnostics(self):
        roi_frame = np.zeros((80, 60, 3), dtype=np.uint8)
        roi_mask = np.zeros((80, 60), dtype=np.uint8)

        result = extract_card_quads_from_roi(roi_frame, roi_mask)

        self.assertEqual(result.quads, [])
        self.assertEqual(result.debug["source"], "offline_roi_extractor")
        self.assertEqual(result.debug["quads_final"], 0)
        self.assertEqual(result.debug["reject_reason"], "empty_roi_mask")


if __name__ == "__main__":
    unittest.main()
