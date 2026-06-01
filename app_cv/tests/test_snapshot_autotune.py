import unittest

from tarotvision.snapshot_autotune import score_snapshot_candidate


class SnapshotAutotuneTest(unittest.TestCase):
    def test_score_rewards_geometry_and_recognition(self):
        recognition = {"match_count": 24, "inlier_ratio": 0.75}

        score = score_snapshot_candidate(quad_score=0.8, recognition=recognition)

        self.assertGreater(score, 1.0)

    def test_score_penalizes_missing_recognition(self):
        score = score_snapshot_candidate(quad_score=0.9, recognition=None)

        self.assertLess(score, 0.9)


if __name__ == "__main__":
    unittest.main()
