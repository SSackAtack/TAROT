import json
import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from tarotvision.live_fixture_capture import LiveFixtureCapture


class LiveFixtureCaptureTest(unittest.TestCase):
    def test_saves_basic_fixture_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            capture = LiveFixtureCapture(
                log_dir=tmpdir,
                enabled=True,
                fixture_name="event_first_test",
                commit="abc123",
                branch="task/test",
                deck="Gilded",
            )

            result = capture.save_snapshot(
                scenario="three_cards",
                raw_frame=np.zeros((12, 16, 3), dtype=np.uint8),
                analysis_frame=np.full((10, 14, 3), 127, dtype=np.uint8),
                metrics={
                    "roi_count": 1,
                    "roi_diagnostics": [{"roi_index": 0, "roi_bbox": [1, 2, 3, 4]}],
                },
                payload={
                    "detected": True,
                    "cards": [{"name": "Gilded_01"}],
                    "runtime": {
                        "table": {"calibrated": True, "marker_ids": [10, 11, 12, 13]},
                        "background_reference_active": True,
                    },
                },
                expected_cards_count=3,
            )

            self.assertTrue(result.ok, result.error)
            fixture_dir = os.path.join(tmpdir, "live_fixtures", "event_first_test")
            scenario_dir = os.path.join(fixture_dir, "three_cards")
            for name in [
                "manifest.json",
                "three_cards/raw_frame_3.png",
                "three_cards/analysis_frame_3.png",
                "three_cards/metrics.json",
                "three_cards/payload.json",
                "three_cards/roi_diagnostics.json",
            ]:
                self.assertTrue(os.path.exists(os.path.join(fixture_dir, name)), name)

            with open(os.path.join(fixture_dir, "manifest.json"), encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["fixture_id"], "event_first_test")
            self.assertIn("three_cards", manifest["scenarios"])

            with open(os.path.join(scenario_dir, "payload.json"), encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["scenario"], "three_cards")
            self.assertEqual(payload["actual_cards_count"], 1)
            self.assertEqual(payload["expected_cards_count"], 3)
            self.assertEqual(payload["marker_ids"], [10, 11, 12, 13])

    def test_uses_scenario_card_count_suffix_for_image_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            capture = LiveFixtureCapture(
                log_dir=tmpdir,
                enabled=True,
                fixture_name="event_first_test",
            )

            for scenario, suffix in [
                ("empty", "0"),
                ("one_card", "1"),
                ("three_cards", "3"),
            ]:
                result = capture.save_snapshot(
                    scenario=scenario,
                    raw_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                    analysis_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                    metrics={},
                    payload={},
                )

                self.assertTrue(result.ok, result.error)
                scenario_dir = os.path.join(tmpdir, "live_fixtures", "event_first_test", scenario)
                self.assertTrue(os.path.exists(os.path.join(scenario_dir, f"raw_frame_{suffix}.png")))
                self.assertTrue(os.path.exists(os.path.join(scenario_dir, f"analysis_frame_{suffix}.png")))
                self.assertFalse(os.path.exists(os.path.join(scenario_dir, "raw_frame.png")))
                self.assertFalse(os.path.exists(os.path.join(scenario_dir, "analysis_frame.png")))

    def test_does_not_overwrite_existing_scenario_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            capture = LiveFixtureCapture(
                log_dir=tmpdir,
                enabled=True,
                fixture_name="event_first_test",
            )

            first = capture.save_snapshot(
                scenario="empty",
                raw_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                analysis_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                metrics={},
                payload={"cards": []},
            )
            second = capture.save_snapshot(
                scenario="empty",
                raw_frame=np.full((4, 4, 3), 255, dtype=np.uint8),
                analysis_frame=np.full((4, 4, 3), 255, dtype=np.uint8),
                metrics={},
                payload={"cards": [{"name": "should_not_overwrite"}]},
            )

            self.assertTrue(first.ok, first.error)
            self.assertFalse(second.ok)
            self.assertEqual(second.reason, "already_exists")

            scenario_dir = os.path.join(tmpdir, "live_fixtures", "event_first_test", "empty")
            with open(os.path.join(scenario_dir, "payload.json"), encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["cards_len"], 0)

    def test_returns_error_status_when_write_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            capture = LiveFixtureCapture(log_dir=tmpdir, enabled=True)

            with patch("cv2.imwrite", side_effect=OSError("disk full")):
                result = capture.save_snapshot(
                    scenario="empty",
                    raw_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                    analysis_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                    metrics={},
                    payload={},
                )

            self.assertFalse(result.ok)
            self.assertIn("disk full", result.error)

    def test_json_payload_converts_numpy_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            capture = LiveFixtureCapture(log_dir=tmpdir, enabled=True, fixture_name="numpy_case")

            result = capture.save_snapshot(
                scenario="one_card",
                raw_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                analysis_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                metrics={
                    "roi_count": np.int64(2),
                    "change_mask_ratio": np.float32(0.25),
                    "roi_diagnostics": [{"roi_area": np.int32(12)}],
                },
                payload={"detected": np.bool_(True), "cards": []},
            )

            self.assertTrue(result.ok, result.error)
            metrics_path = os.path.join(
                tmpdir,
                "live_fixtures",
                "numpy_case",
                "one_card",
                "metrics.json",
            )
            with open(metrics_path, encoding="utf-8") as handle:
                metrics = json.load(handle)
            self.assertEqual(metrics["roi_count"], 2)
            self.assertAlmostEqual(metrics["change_mask_ratio"], 0.25)
            self.assertEqual(metrics["roi_diagnostics"][0]["roi_area"], 12)

    def test_capture_is_inactive_without_env_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {}, clear=True):
                capture = LiveFixtureCapture.from_env(log_dir=tmpdir)
                result = capture.save_snapshot(
                    scenario="empty",
                    raw_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                    analysis_frame=np.zeros((4, 4, 3), dtype=np.uint8),
                    metrics={},
                    payload={},
                )

            self.assertFalse(result.ok)
            self.assertEqual(result.reason, "disabled")
            self.assertFalse(os.path.exists(os.path.join(tmpdir, "live_fixtures")))


if __name__ == "__main__":
    unittest.main()
