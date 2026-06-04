import unittest

from tarotvision.autotune_scoring import score_autotune_profile, choose_best_profile_result


class AutotuneScoringTest(unittest.TestCase):
    def test_scores_recognition_over_geometry_only(self):
        geometry_only = {
            "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.001},
            "samples": [
                {
                    "geometry_score": 0.95,
                    "candidate_count": 3,
                    "accepted_count": 0,
                    "false_positive_count": 0,
                    "matching_ms": 40.0,
                }
            ],
        }
        recognized = {
            "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.002},
            "samples": [
                {
                    "geometry_score": 0.70,
                    "candidate_count": 3,
                    "accepted_count": 2,
                    "recognition_score": 0.80,
                    "false_positive_count": 0,
                    "matching_ms": 55.0,
                }
            ],
        }

        self.assertGreater(
            score_autotune_profile(recognized)["score"],
            score_autotune_profile(geometry_only)["score"],
        )

    def test_penalizes_false_positive_on_empty_mat(self):
        result = score_autotune_profile({
            "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.0001},
            "samples": [
                {
                    "scenario": "empty",
                    "geometry_score": 0.8,
                    "candidate_count": 2,
                    "accepted_count": 1,
                    "recognition_score": 0.6,
                    "false_positive_count": 1,
                    "matching_ms": 40.0,
                }
            ],
        })

        self.assertLess(result["score"], 0.0)
        self.assertIn("false_positive", result["reasons"][0])

    def test_choose_best_profile_result(self):
        low = {
            "profile": {"name": "low"},
            "samples": [{"geometry_score": 0.2, "accepted_count": 0}],
        }
        high = {
            "profile": {"name": "high"},
            "samples": [{"geometry_score": 0.7, "accepted_count": 2, "recognition_score": 0.8}],
        }

        best = choose_best_profile_result([low, high])

        self.assertEqual(best["profile"]["name"], "high")
        self.assertGreater(best["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
