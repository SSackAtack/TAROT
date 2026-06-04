"""Tests for Stage 6 real-camera ORB error analysis."""
import unittest

from tools.cv_detection_lab.stage6_real_camera_error_analysis import _bool, _counts, classify_probable_cause


class TestStage6RealCameraErrorAnalysis(unittest.TestCase):
    def test_classifies_yellow_as_image_quality_or_crop(self):
        row = {"category": "gilded_yellow", "top3_contains_expected": "False"}
        self.assertEqual(classify_probable_cause(row), "image_quality_or_crop")

    def test_classifies_similar_and_top3_ranking(self):
        similar = {
            "category": "gilded_visually_similar", "top3_contains_expected": "False",
            "confidence_score": "0.10", "confidence_gap": "0.05",
        }
        ranking = {
            "category": "gilded_upright", "top3_contains_expected": "True",
            "confidence_score": "0.10", "confidence_gap": "0.01",
        }
        self.assertEqual(classify_probable_cause(similar), "visual_similarity_or_matcher")
        self.assertEqual(classify_probable_cause(ranking), "matcher_ranking")

    def test_flags_strong_visually_similar_prediction_as_ground_truth_suspect(self):
        row = {
            "category": "gilded_visually_similar", "top3_contains_expected": "False",
            "confidence_score": "0.344", "confidence_gap": "0.328",
        }
        self.assertEqual(classify_probable_cause(row), "ground_truth_mismatch_suspected")

    def test_low_signal_upright_is_image_quality_or_crop(self):
        row = {
            "category": "gilded_upright", "top3_contains_expected": "True",
            "confidence_score": "0.018", "confidence_gap": "0.002",
        }
        self.assertEqual(classify_probable_cause(row), "image_quality_or_crop")

    def test_helpers_are_stable(self):
        self.assertTrue(_bool("True"))
        self.assertFalse(_bool("False"))
        self.assertEqual(_counts(["b", "a", "b"]), {"a": 1, "b": 2})


if __name__ == "__main__":
    unittest.main()
