import unittest
import json
from tarotvision.calibration_wizard_scoring import score_calibration_wizard_samples


class TestCalibrationWizardScoring(unittest.TestCase):

    def test_empty_scenario_good_quality_returns_ready(self):
        samples = {
            "empty": [
                {
                    "detected_count": 0,
                    "accepted_count": 0,
                    "snapshot_quality_score": 0.85,
                    "analysis_ms": 100.0,
                },
                {
                    "detected_count": 0,
                    "accepted_count": 0,
                    "snapshot_quality_score": 0.90,
                    "analysis_ms": 90.0,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertTrue(report["ready_for_session"])
        self.assertEqual(report["grade"], "excellent")
        self.assertGreaterEqual(report["score"], 0.90)
        self.assertEqual(len(report["blocking_issues"]), 0)

    def test_empty_scenario_false_candidates_adds_warning(self):
        samples = {
            "empty": [
                {
                    "detected_count": 2,
                    "accepted_count": 0,
                    "snapshot_quality_score": 0.80,
                },
                {
                    "detected_count": 1,
                    "accepted_count": 0,
                    "snapshot_quality_score": 0.85,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertLess(report["score"], 1.0)
        self.assertTrue(any("kandydatow" in w for w in report["warnings"]))

    def test_one_card_good_confidence_returns_good_grade(self):
        samples = {
            "one_card": [
                {
                    "detected_count": 1,
                    "accepted_count": 1,
                    "snapshot_quality_score": 0.85,
                    "recognition_confidences": [0.88],
                    "analysis_ms": 150.0,
                },
                {
                    "detected_count": 1,
                    "accepted_count": 1,
                    "snapshot_quality_score": 0.80,
                    "recognition_confidences": [0.92],
                    "analysis_ms": 140.0,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertTrue(report["ready_for_session"])
        self.assertIn(report["grade"], ("good", "excellent"))
        self.assertEqual(len(report["blocking_issues"]), 0)

    def test_one_card_low_confidence_returns_warning(self):
        samples = {
            "one_card": [
                {
                    "detected_count": 1,
                    "accepted_count": 1,
                    "snapshot_quality_score": 0.85,
                    "recognition_confidences": [0.65],
                    "analysis_ms": 150.0,
                },
                {
                    "detected_count": 1,
                    "accepted_count": 1,
                    "snapshot_quality_score": 0.80,
                    "recognition_confidences": [0.68],
                    "analysis_ms": 140.0,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertEqual(report["grade"], "warning")
        self.assertFalse(report["ready_for_session"])
        self.assertTrue(any("pewnosc" in w.lower() for w in report["warnings"]))

    def test_three_cards_good_samples_returns_ready(self):
        samples = {
            "three_cards": [
                {
                    "detected_count": 3,
                    "accepted_count": 3,
                    "snapshot_quality_score": 0.88,
                    "recognition_confidences": [0.85, 0.80, 0.90],
                    "analysis_ms": 400.0,
                },
                {
                    "detected_count": 3,
                    "accepted_count": 3,
                    "snapshot_quality_score": 0.82,
                    "recognition_confidences": [0.78, 0.82, 0.88],
                    "analysis_ms": 380.0,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertTrue(report["ready_for_session"])
        self.assertIn(report["grade"], ("good", "excellent"))

    def test_three_cards_slow_analysis_adds_warning(self):
        samples = {
            "three_cards": [
                {
                    "detected_count": 3,
                    "accepted_count": 3,
                    "snapshot_quality_score": 0.85,
                    "recognition_confidences": [0.85, 0.80, 0.90],
                    "analysis_ms": 1800.0,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertLess(report["score"], 1.0)
        self.assertTrue(any("wolna" in w or "przekracza" in w for w in report["warnings"]))

    def test_recognition_rejections_reduce_score(self):
        samples = {
            "one_card": [
                {
                    "detected_count": 1,
                    "accepted_count": 1,
                    "snapshot_quality_score": 0.85,
                    "recognition_confidences": [0.85],
                    "recognition_rejections": 3,
                    "candidate_validation_rejections": 1,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        self.assertLess(report["score"], 1.0)
        self.assertTrue(any("odrzuca" in w for w in report["warnings"]))

    def test_missing_fields_do_not_crash(self):
        samples = {
            "one_card": [
                {
                    "accepted_count": 1,
                    # brak detected_count, quality, confidence, itp.
                }
            ]
        }
        try:
            report = score_calibration_wizard_samples(samples)
            self.assertIsNotNone(report)
            self.assertIn("score", report)
        except Exception as exc:
            self.fail(f"Scoring crashed on missing fields: {exc}")

    def test_report_is_json_serializable(self):
        samples = {
            "empty": [
                {
                    "detected_count": 0,
                    "accepted_count": 0,
                    "snapshot_quality_score": 0.85,
                    "analysis_ms": 100.0,
                }
            ]
        }
        report = score_calibration_wizard_samples(samples)
        try:
            json_str = json.dumps(report)
            self.assertIsInstance(json_str, str)
        except Exception as exc:
            self.fail(f"Quality report is not JSON-serializable: {exc}")


if __name__ == "__main__":
    unittest.main()
