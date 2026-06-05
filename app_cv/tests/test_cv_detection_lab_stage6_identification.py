"""Unit tests for Stage 6 Card Identification offline benchmark."""
import json
import os
import shutil
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_identification_methods import (
    FIRST_WAVE_METHODS,
    load_reference_deck,
    run_identification_method,
)
from tools.cv_detection_lab.stage6_card_identification_benchmark import (
    MATRIX_COLUMNS,
    run_benchmark,
)


def _card_image(index):
    image = np.full((495, 300, 3), (35, 45, 40), dtype=np.uint8)
    colors = [(180, 80, 50), (60, 170, 220), (170, 70, 180)]
    cv2.rectangle(image, (8, 8), (291, 486), (230, 230, 230), 5)
    cv2.circle(image, (150, 180), 60 + index * 8, colors[index], -1)
    cv2.putText(image, f"CARD {index}", (55, 390), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (250, 250, 250), 3)
    for offset in range(5):
        cv2.line(image, (35 + offset * 25, 50), (250, 320 - offset * 20), colors[index], 3)
    return image


class TestStage6IdentificationMethods(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_identification_")
        self.reference_dir = os.path.join(self.tmpdir, "references")
        os.makedirs(self.reference_dir)
        cards = []
        for index in range(3):
            card_id = f"CARD_{index:02d}"
            file_name = f"{card_id}.jpg"
            cv2.imwrite(os.path.join(self.reference_dir, file_name), _card_image(index))
            cards.append({"card_id": card_id, "card_name": card_id, "reference_image": file_name})
        self.profile_path = os.path.join(self.tmpdir, "deck_profile.json")
        with open(self.profile_path, "w", encoding="utf-8") as handle:
            json.dump({"deck_id": "test", "deck_profile_version": 1, "cards": cards}, handle)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_reference_deck_loads_profile_cards(self):
        references = load_reference_deck(self.reference_dir, self.profile_path)

        self.assertEqual(len(references), 3)
        self.assertEqual(references[0].card_id, "CARD_00")

    def test_first_wave_methods_return_ranked_top_three(self):
        references = load_reference_deck(self.reference_dir, self.profile_path)

        for method in FIRST_WAVE_METHODS:
            with self.subTest(method=method):
                result = run_identification_method(method, _card_image(1), references, readiness_score=0.8)
                self.assertEqual(len(result.top_k_candidates), 3)
                self.assertEqual(result.top_k_candidates[0]["card_id"], "CARD_01")
                self.assertGreaterEqual(result.confidence_score, 0.0)
                self.assertGreaterEqual(result.confidence_gap, 0.0)

    def test_unknown_method_raises_value_error(self):
        references = load_reference_deck(self.reference_dir, self.profile_path)

        with self.assertRaises(ValueError):
            run_identification_method("not_a_method", _card_image(0), references)


class TestStage6IdentificationBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_benchmark_")
        self.fixture_dir = os.path.join(self.tmpdir, "fixture")
        self.reference_dir = os.path.join(self.tmpdir, "references")
        self.output_dir = os.path.join(self.tmpdir, "output")
        os.makedirs(self.reference_dir)
        self._write_fixture()
        self.profile_path = self._write_profile()
        self.ground_truth_path = self._write_ground_truth()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_benchmark_writes_reports_and_scores_manual_labels(self):
        summary = run_benchmark(
            fixture_dir=self.fixture_dir,
            reference_deck_dir=self.reference_dir,
            deck_profile_path=self.profile_path,
            ground_truth_path=self.ground_truth_path,
            output_dir=self.output_dir,
            methods=["histogram_similarity_hsv", "ssim_like_luma"],
        )

        self.assertEqual(summary["label_count"], 10)
        self.assertEqual(summary["methods_tested"], ["histogram_similarity_hsv", "ssim_like_luma"])
        self.assertTrue(os.path.isfile(os.path.join(self.output_dir, "matrix.csv")))
        self.assertTrue(os.path.isfile(os.path.join(self.output_dir, "report.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.output_dir, "report.md")))
        self.assertIn("accuracy_top1", summary["method_summaries"][0])

    def test_matrix_columns_include_top1_top3_and_quality_context(self):
        for column in [
            "expected_card_id",
            "predicted_card_id",
            "top1_correct",
            "top3_contains_expected",
            "confidence_score",
            "confidence_gap",
            "crop_quality_status",
            "identification_readiness_score",
        ]:
            self.assertIn(column, MATRIX_COLUMNS)

    def _write_fixture(self):
        empty = np.full((600, 900, 3), (35, 55, 40), dtype=np.uint8)
        one = empty.copy()
        three = empty.copy()
        one[55:550, 300:600] = _card_image(1)
        three[55:550, 20:320] = _card_image(0)
        three[55:550, 300:600] = _card_image(1)
        three[55:550, 580:880] = _card_image(2)
        for scenario, name, image in [
            ("empty", "analysis_frame_0.png", empty),
            ("one_card", "analysis_frame_1.png", one),
            ("three_cards", "analysis_frame_3.png", three),
        ]:
            scenario_dir = os.path.join(self.fixture_dir, scenario)
            os.makedirs(scenario_dir, exist_ok=True)
            cv2.imwrite(os.path.join(scenario_dir, name), image)

    def _write_profile(self):
        cards = []
        for index in range(3):
            card_id = f"CARD_{index:02d}"
            file_name = f"{card_id}.jpg"
            cv2.imwrite(os.path.join(self.reference_dir, file_name), _card_image(index))
            cards.append({"card_id": card_id, "card_name": card_id, "reference_image": file_name})
        path = os.path.join(self.tmpdir, "deck_profile.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"deck_id": "test", "deck_profile_version": 1, "cards": cards}, handle)
        return path

    def _write_ground_truth(self):
        def label(index, card_id):
            return {"crop_index": index, "expected_card_id": card_id, "orientation": "upright"}

        payload = {
            "deck_profile_id": "test",
            "deck_profile_version": 1,
            "label_status": "manual_confirmed",
            "pairs": {
                "empty_to_empty": [],
                "empty_to_one_card": [label(1, "CARD_01")],
                "empty_to_three_cards": [label(1, "CARD_00"), label(2, "CARD_01"), label(3, "CARD_02")],
                "one_card_to_three_cards": [label(1, "CARD_00"), label(2, "CARD_02")],
                "one_card_to_empty": [label(1, "CARD_01")],
                "three_cards_to_empty": [label(1, "CARD_00"), label(2, "CARD_01"), label(3, "CARD_02")],
            },
        }
        path = os.path.join(self.tmpdir, "ground_truth.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return path


if __name__ == "__main__":
    unittest.main()
