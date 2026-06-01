import unittest

from tarotvision.detection_diagnostics import (
    empty_detection_diagnostics,
    summarize_detection_diagnostics,
)


class DetectionDiagnosticsTest(unittest.TestCase):
    def test_empty_diagnostics_has_stable_keys(self):
        diagnostics = empty_detection_diagnostics()

        self.assertEqual(diagnostics["profiles"], [])
        self.assertEqual(diagnostics["quads_final"], 0)
        self.assertIn("reject_reasons", diagnostics)
        self.assertIn("background_mask_nonzero_ratio", diagnostics)

    def test_summarizes_profile_counters_for_runtime_metrics(self):
        summary = summarize_detection_diagnostics({
            "quads_final": 1,
            "background_mask_nonzero_ratio": 0.25,
            "profiles": [
                {
                    "contours_total": 10,
                    "candidates_after_quad": 2,
                    "min_area_rect_candidates": 3,
                    "min_area_rect_accepted": 1,
                },
                {
                    "contours_total": 5,
                    "candidates_after_quad": 1,
                    "min_area_rect_candidates": 2,
                    "min_area_rect_accepted": 0,
                },
            ],
        })

        self.assertEqual(summary["snapshot_detection_quads_final"], 1)
        self.assertEqual(summary["snapshot_detection_profile_count"], 2)
        self.assertEqual(summary["snapshot_strict_quad_candidates"], 3)
        self.assertEqual(summary["snapshot_min_area_rect_candidates"], 5)
        self.assertEqual(summary["snapshot_min_area_rect_accepted"], 1)
        self.assertEqual(summary["snapshot_foreground_contours_total"], 15)
        self.assertEqual(summary["snapshot_background_mask_nonzero_ratio"], 0.25)


if __name__ == "__main__":
    unittest.main()
