import unittest

from tarotvision.calibration_session import score_sample, choose_best_candidate


class CalibrationSessionTest(unittest.TestCase):
    def test_score_rewards_stable_detection_and_tracking(self):
        score = score_sample(
            identified=True,
            good_matches=35,
            false_contours=1,
            jitter=0.1,
            matching_ms=90.0,
        )

        self.assertGreater(score, 1000.0)

    def test_choose_best_candidate(self):
        candidates = [
            {"name": "noisy", "score": 900.0},
            {"name": "stable", "score": 1200.0},
        ]

        self.assertEqual(choose_best_candidate(candidates)["name"], "stable")

    def test_returns_none_without_candidates(self):
        self.assertIsNone(choose_best_candidate([]))


if __name__ == "__main__":
    unittest.main()
