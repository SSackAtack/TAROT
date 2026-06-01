import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.benchmark_snapshot_recognition import summarize_results


class BenchmarkSnapshotRecognitionTest(unittest.TestCase):
    def test_summarize_results_counts_success_rate(self):
        rows = [
            {"accepted": True, "deck_id": "boski"},
            {"accepted": False, "deck_id": "boski"},
            {"accepted": True, "deck_id": "magic"},
        ]

        summary = summarize_results(rows)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["accepted"], 2)
        self.assertAlmostEqual(summary["accept_rate"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
