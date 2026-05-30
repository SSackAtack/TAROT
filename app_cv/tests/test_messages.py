import unittest

from tarotvision.messages import build_status_payload


class StatusPayloadTest(unittest.TestCase):
    def test_payload_contains_required_sections(self):
        payload = build_status_payload(
            cards=[], metrics={"fps": 30.0}, warnings=["low_confidence"]
        )

        self.assertFalse(payload["detected"])
        self.assertEqual(payload["cards"], [])
        self.assertEqual(payload["metrics"]["fps"], 30.0)
        self.assertEqual(payload["warnings"], ["low_confidence"])

    def test_detected_true_with_cards(self):
        cards = [{"name": "17_star", "x": 0.5, "y": -1.0, "angle": 0.1}]
        payload = build_status_payload(cards=cards)

        self.assertTrue(payload["detected"])
        self.assertEqual(len(payload["cards"]), 1)

    def test_defaults_for_optional_fields(self):
        payload = build_status_payload(cards=[])

        self.assertEqual(payload["metrics"], {})
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(payload["debug"], {})

    def test_debug_section_preserved(self):
        debug = {"candidates": [{"name": "00_fool", "confidence": 0.6}]}
        payload = build_status_payload(cards=[], debug=debug)

        self.assertEqual(payload["debug"]["candidates"][0]["name"], "00_fool")

    def test_runtime_section_included(self):
        runtime = {"profile": "cpu_baseline", "capture_width": 1280}
        payload = build_status_payload(cards=[], runtime=runtime)

        self.assertEqual(payload["runtime"]["profile"], "cpu_baseline")

    def test_snapshot_layout_metadata_preserved(self):
        layout = {
            "layout_id": 7,
            "source": "snapshot",
            "state": "holding_last_good",
            "stable_for_ms": 3040,
            "quality_score": 0.82,
        }

        payload = build_status_payload(cards=[], layout=layout)

        self.assertEqual(payload["layout"]["layout_id"], 7)
        self.assertEqual(payload["layout"]["source"], "snapshot")
        self.assertEqual(payload["layout"]["state"], "holding_last_good")

    def test_schema_version_is_included(self):
        payload = build_status_payload(cards=[])
        self.assertEqual(payload["schema_version"], 1)

    def test_studio_section_defaults(self):
        payload = build_status_payload(cards=[])
        self.assertIn("audio", payload["studio"])
        self.assertEqual(payload["studio"]["audio"]["channels"]["bgm"]["volume"], 0.5)
        self.assertFalse(payload["studio"]["audio"]["channels"]["mic"]["muted"])

    def test_studio_section_preserved(self):
        studio = {
            "recording_state": "recording",
            "recording_id": "session_123",
            "elapsed_ms": 5000,
        }
        payload = build_status_payload(cards=[], studio=studio)
        self.assertEqual(payload["studio"]["recording_state"], "recording")
        self.assertEqual(payload["studio"]["recording_id"], "session_123")

    def test_build_status_payload_does_not_mutate_studio(self):
        studio = {"recording_state": "idle"}
        payload = build_status_payload(cards=[], studio=studio)
        
        # Upewniamy się, że w payloadzie jest audio
        self.assertIn("audio", payload["studio"])
        # Upewniamy się, że oryginalny przekazany słownik studio nie został zmutowany
        self.assertNotIn("audio", studio)


if __name__ == "__main__":
    unittest.main()
