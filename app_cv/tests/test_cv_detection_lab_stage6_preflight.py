"""Unit tests for Stage 6 reference deck and ground truth preflight."""
import json
import os
import shutil
import tempfile
import unittest

from tools.cv_detection_lab.stage6_preflight import REQUIRED_PAIRS, run_preflight


class TestStage6Preflight(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_preflight_")
        self.fixture_dir = os.path.join(self.tmpdir, "fixture")
        self.reference_deck_dir = os.path.join(self.tmpdir, "references")
        self.deck_profile_path = os.path.join(self.tmpdir, "deck_profile.json")
        self.ground_truth_path = os.path.join(self.tmpdir, "ground_truth.json")
        self.stage5_output_dir = os.path.join(self.tmpdir, "stage5", "quality_metric_suite_v1")
        self._write_fixture()
        self._write_reference_deck()
        self._write_deck_profile()
        self._write_ground_truth()
        self._write_stage5_outputs()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_deck_profile_passes(self):
        report = self._run()

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["deck_profile"]["deck_id"], "test_deck")
        self.assertEqual(report["ground_truth"]["label_count"], 10)
        self.assertEqual(report["errors"], [])

    def test_missing_reference_image_blocks(self):
        os.remove(os.path.join(self.reference_deck_dir, "card_02.jpg"))

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("MISSING_REFERENCE_IMAGE", self._codes(report["errors"]))

    def test_duplicate_card_id_blocks(self):
        profile = self._load(self.deck_profile_path)
        profile["cards"][2]["card_id"] = profile["cards"][1]["card_id"]
        self._dump(self.deck_profile_path, profile)

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("DUPLICATE_CARD_ID", self._codes(report["errors"]))

    def test_missing_ground_truth_blocks(self):
        os.remove(self.ground_truth_path)

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("MISSING_GROUND_TRUTH", self._codes(report["errors"]))

    def test_ground_truth_card_outside_deck_reports_not_in_reference_scope(self):
        ground_truth = self._load(self.ground_truth_path)
        ground_truth["pairs"]["empty_to_one_card"][0]["expected_card_id"] = "CARD_99"
        self._dump(self.ground_truth_path, ground_truth)

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("NOT_IN_REFERENCE_SCOPE", self._codes(report["errors"]))

    def test_missing_required_pair_blocks(self):
        ground_truth = self._load(self.ground_truth_path)
        ground_truth["pairs"].pop("one_card_to_empty")
        self._dump(self.ground_truth_path, ground_truth)

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("MISSING_REQUIRED_PAIR", self._codes(report["errors"]))

    def test_empty_to_empty_with_label_blocks(self):
        ground_truth = self._load(self.ground_truth_path)
        ground_truth["pairs"]["empty_to_empty"] = [self._label("CARD_00", 1)]
        self._dump(self.ground_truth_path, ground_truth)

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        codes = self._codes(report["errors"])
        self.assertIn("EMPTY_TO_EMPTY_SHOULD_HAVE_NO_LABELS", codes)

    def test_one_card_to_three_cards_wrong_label_count_blocks(self):
        ground_truth = self._load(self.ground_truth_path)
        ground_truth["pairs"]["one_card_to_three_cards"] = [self._label("CARD_01", 1)]
        self._dump(self.ground_truth_path, ground_truth)

        report = self._run()

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("UNEXPECTED_LABEL_COUNT", self._codes(report["errors"]))

    def test_missing_stage5_output_warns(self):
        shutil.rmtree(self.stage5_output_dir)

        report = self._run()

        self.assertEqual(report["status"], "WARNING")
        self.assertIn("MISSING_STAGE5_OUTPUT", self._codes(report["warnings"]))
        self.assertEqual(report["errors"], [])

    def _run(self):
        return run_preflight(
            fixture_dir=self.fixture_dir,
            reference_deck_dir=self.reference_deck_dir,
            deck_profile_path=self.deck_profile_path,
            ground_truth_path=self.ground_truth_path,
            stage5_output_dir=self.stage5_output_dir,
        )

    def _write_fixture(self):
        for scenario, frame_name in [
            ("empty", "analysis_frame_0.png"),
            ("one_card", "analysis_frame_1.png"),
            ("three_cards", "analysis_frame_3.png"),
        ]:
            scenario_dir = os.path.join(self.fixture_dir, scenario)
            os.makedirs(scenario_dir, exist_ok=True)
            with open(os.path.join(scenario_dir, frame_name), "wb") as handle:
                handle.write(b"fixture")

    def _write_reference_deck(self):
        os.makedirs(self.reference_deck_dir, exist_ok=True)
        for index in range(3):
            with open(os.path.join(self.reference_deck_dir, f"card_{index:02d}.jpg"), "wb") as handle:
                handle.write(b"reference")

    def _write_deck_profile(self):
        profile = {
            "deck_id": "test_deck",
            "deck_profile_version": 1,
            "display_name": "Test Deck",
            "scope": "test_three_cards",
            "card_count": 3,
            "cards": [
                {"card_id": "CARD_00", "card_name": "Card Zero", "reference_image": "card_00.jpg"},
                {"card_id": "CARD_01", "card_name": "Card One", "reference_image": "card_01.jpg"},
                {"card_id": "CARD_02", "card_name": "Card Two", "reference_image": "card_02.jpg"},
            ],
        }
        self._dump(self.deck_profile_path, profile)

    def _write_ground_truth(self):
        ground_truth = {
            "deck_profile_id": "test_deck",
            "deck_profile_version": 1,
            "pairs": {
                "empty_to_empty": [],
                "empty_to_one_card": [self._label("CARD_00", 1, "Card Zero")],
                "empty_to_three_cards": [
                    self._label("CARD_00", 1, "Card Zero"),
                    self._label("CARD_01", 2, "Card One"),
                    self._label("CARD_02", 3, "Card Two"),
                ],
                "one_card_to_three_cards": [
                    self._label("CARD_01", 1, "Card One"),
                    self._label("CARD_02", 2, "Card Two"),
                ],
                "one_card_to_empty": [self._label("CARD_00", 1, "Card Zero")],
                "three_cards_to_empty": [
                    self._label("CARD_00", 1, "Card Zero"),
                    self._label("CARD_01", 2, "Card One"),
                    self._label("CARD_02", 3, "Card Two"),
                ],
            },
        }
        self._dump(self.ground_truth_path, ground_truth)

    def _write_stage5_outputs(self):
        for pair_name in REQUIRED_PAIRS:
            pair_dir = os.path.join(self.stage5_output_dir, pair_name)
            os.makedirs(pair_dir, exist_ok=True)
            with open(os.path.join(pair_dir, "quality_debug.json"), "w", encoding="utf-8") as handle:
                json.dump({"pair": pair_name}, handle)
            with open(os.path.join(pair_dir, "crop_quality_debug_sheet.png"), "wb") as handle:
                handle.write(b"debug")

    def _label(self, card_id, crop_index, card_name=None):
        label = {
            "crop_index": crop_index,
            "expected_card_id": card_id,
            "orientation": "upright",
        }
        if card_name is not None:
            label["expected_card_name"] = card_name
        return label

    def _load(self, path):
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _dump(self, path, data):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)

    def _codes(self, issues):
        return {item["code"] for item in issues}


if __name__ == "__main__":
    unittest.main()
