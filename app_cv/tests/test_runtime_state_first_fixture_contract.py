# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from tools.cv_detection_lab.runtime_state_first_smoke import EXPECTED_PAIRS, run_smoke


class TestRuntimeStateFirstFixtureContract(unittest.TestCase):
    def test_expected_pairs_cover_add_and_remove_workflows(self):
        self.assertEqual(
            EXPECTED_PAIRS,
            [
                ("empty", "empty", 0),
                ("empty", "one_card", 1),
                ("empty", "three_cards", 3),
                ("one_card", "three_cards", 2),
                ("one_card", "empty", 1),
                ("three_cards", "empty", 3),
            ],
        )

    def test_smoke_report_names_each_pair_and_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="state_first_smoke_") as tmpdir:
            root = Path(tmpdir)
            self._write_fixture(root)

            report = run_smoke(root)

        self.assertEqual(report["status"], "FAIL")
        pair_names = {item["pair"] for item in report["pairs"]}
        self.assertEqual(pair_names, {f"{prev}->{cur}" for prev, cur, _ in EXPECTED_PAIRS})
        failing = [item for item in report["pairs"] if item["status"] == "FAIL"]
        self.assertTrue(failing)
        self.assertTrue(all("expected_count" in item and "actual_count" in item for item in failing))

    def _write_fixture(self, root):
        frames = {
            "empty": np.zeros((180, 240, 3), dtype=np.uint8),
            "one_card": np.zeros((180, 240, 3), dtype=np.uint8),
            "three_cards": np.zeros((180, 240, 3), dtype=np.uint8),
        }
        cv2.rectangle(frames["one_card"], (30, 40), (80, 130), (255, 255, 255), -1)
        cv2.rectangle(frames["three_cards"], (30, 40), (80, 130), (255, 255, 255), -1)
        cv2.rectangle(frames["three_cards"], (100, 35), (150, 125), (255, 255, 255), -1)
        cv2.rectangle(frames["three_cards"], (148, 45), (220, 135), (255, 255, 255), -1)

        paths = {
            "empty": root / "empty" / "analysis_frame_0.png",
            "one_card": root / "one_card" / "analysis_frame_1.png",
            "three_cards": root / "three_cards" / "analysis_frame_3.png",
        }
        for name, path in paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            self.assertTrue(cv2.imwrite(str(path), frames[name]))


if __name__ == "__main__":
    unittest.main()
