import tempfile
import unittest

from tarotvision.profile_store import ProfileStore


class ProfileStoreTest(unittest.TestCase):
    def test_save_and_load_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)
            store.save("studio_day", {"SNAPSHOT_SETTLE_SECONDS": 1.5})

            profile = store.load("studio_day")

        self.assertEqual(profile["SNAPSHOT_SETTLE_SECONDS"], 1.5)

    def test_rejects_path_traversal_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save("../bad", {"SNAPSHOT_SETTLE_SECONDS": 1.5})

    def test_rejects_unknown_parameter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save("studio_day", {"UNKNOWN_PARAM": 1.0})

    def test_save_autotune_recommendation_keeps_metadata_and_parameters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)
            store.save_autotune_recommendation(
                "studio-live-20260602",
                {
                    "profile": {
                        "CARD_DETECT_MIN_AREA_RATIO": 0.001,
                        "CARD_DETECT_MAX_CANDIDATES": 10.0,
                        "WORKSPACE_INFLATE_PERCENT": 6.0,
                    },
                    "score": 1.25,
                    "confidence": "HIGH",
                },
            )

            profile = store.load("studio-live-20260602")

        self.assertEqual(profile["name"], "studio-live-20260602")
        self.assertEqual(profile["source"], "autotune")
        self.assertEqual(profile["score"], 1.25)
        self.assertEqual(profile["confidence"], "HIGH")
        self.assertEqual(profile["parameters"]["CARD_DETECT_MIN_AREA_RATIO"], 0.001)
        self.assertEqual(profile["parameters"]["CARD_DETECT_MAX_CANDIDATES"], 10.0)
        self.assertEqual(profile["parameters"]["WORKSPACE_INFLATE_PERCENT"], 6.0)

    def test_load_parameters_supports_autotune_metadata_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)
            store.save_autotune_recommendation(
                "studio-live-20260602",
                {
                    "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.001},
                    "score": 1.25,
                    "confidence": "HIGH",
                },
            )

            parameters = store.load_parameters("studio-live-20260602")

        self.assertEqual(parameters, {"CARD_DETECT_MIN_AREA_RATIO": 0.001})

    def test_autotune_recommendation_rejects_invalid_parameter_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save_autotune_recommendation(
                    "studio-live-20260602",
                    {
                        "profile": {"CARD_DETECT_MIN_AREA_RATIO": 99.0},
                        "score": 1.25,
                        "confidence": "HIGH",
                    },
                )


if __name__ == "__main__":
    unittest.main()
