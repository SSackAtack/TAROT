import unittest

from tarotvision.recognition_debug import RecognitionDebug, top_match_summary


class RecognitionDebugTest(unittest.TestCase):
    def test_top_match_summary_sorts_by_score(self):
        debug = RecognitionDebug(
            crop_keypoints=120,
            top_matches=[
                {"name": "RWS_01", "score": 4.0, "match_count": 8, "inlier_ratio": 0.5},
                {"name": "Boski_02", "score": 9.0, "match_count": 12, "inlier_ratio": 0.75},
            ],
            reject_reason=None,
        )

        result = top_match_summary(debug, limit=1)

        self.assertEqual(result, [{
            "name": "Boski_02",
            "score": 9.0,
            "match_count": 12,
            "inlier_ratio": 0.75,
        }])

    def test_summary_handles_empty_debug(self):
        debug = RecognitionDebug(crop_keypoints=0, top_matches=[], reject_reason="no_descriptors")

        self.assertEqual(top_match_summary(debug), [])


if __name__ == "__main__":
    unittest.main()
