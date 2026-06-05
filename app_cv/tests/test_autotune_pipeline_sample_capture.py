# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import shutil
import json
import time
from unittest.mock import MagicMock, patch
import numpy as np

# Ustawiamy tryb testowy przed importem main.py
os.environ["TAROTVISION_TEST_MODE"] = "1"
import main
from tarotvision.pipelines import SnapshotFirstPipeline
from tarotvision.autotune_session import AutotuneSession
from tarotvision.autotune_session_log import AutotuneSessionLog


class TestAutotunePipelineSampleCapture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_log_dir = main.LOG_DIR
        main.LOG_DIR = self.temp_dir
        
        # Inicjalizujemy logi sesji na tymczasowym katalogu
        main.autotune_session_log = AutotuneSessionLog(os.path.join(self.temp_dir, "autotune_sessions"))
        
        # Resetujemy zmienne globalne
        main.autotune_session = None
        main.autotune_candidate_profiles = []
        main.calibration_state = {
            "state": "idle",
            "last_score": None,
            "autotune": main.autotune_status_payload()
        }
        main.operator_warnings = []

    def tearDown(self):
        main.LOG_DIR = self.old_log_dir
        main.autotune_session = None
        main.autotune_candidate_profiles = []
        shutil.rmtree(self.temp_dir)

    def test_pipeline_does_not_collect_without_active_autotune_session(self):
        self.assertIsNone(main.autotune_session)
        
        # Symulujemy wywołanie callbacku
        pipeline_sample = {
            "detected_count": 0,
            "accepted_count": 0,
            "analysis_ms": 12.5,
            "snapshot_quality_score": 0.85
        }
        
        # Nic nie powinno się stać (brak crasha)
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        self.assertIsNone(main.autotune_session)

    def test_collects_empty_sample_when_expected_count_zero(self):
        # Startujemy sesję wizardu dla pustej maty
        main.autotune_session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=3)
        
        # Symulujemy próbkę z 0 kartami (empty)
        pipeline_sample = {
            "detected_count": 0,
            "accepted_count": 0,
            "analysis_ms": 10.0,
            "snapshot_quality_score": 0.9
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        # Sprawdzamy czy próbka została dodana
        self.assertEqual(len(main.autotune_session.samples["empty"]), 1)
        self.assertEqual(main.calibration_state["autotune"]["collected_count"], 1)
        self.assertFalse(main.autotune_session.ready_to_score())

    def test_collects_one_card_sample_when_expected_count_one(self):
        main.autotune_session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=3)
        
        # Symulujemy próbkę z 1 kartą
        pipeline_sample = {
            "detected_count": 1,
            "accepted_count": 1,
            "analysis_ms": 15.0,
            "snapshot_quality_score": 0.88,
            "recognition_confidences": [0.92]
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        self.assertEqual(len(main.autotune_session.samples["one_card"]), 1)
        self.assertEqual(main.calibration_state["autotune"]["collected_count"], 1)
        
        saved_sample = main.autotune_session.samples["one_card"][0]
        self.assertEqual(saved_sample["candidate_count"], 1)
        self.assertEqual(saved_sample["false_positive_count"], 0)
        self.assertEqual(saved_sample["geometry_score"], 0.88)
        self.assertEqual(saved_sample["recognition_score"], 0.92)
        self.assertEqual(saved_sample["matching_ms"], 15.0)

    def test_collects_unrecognized_one_card_sample(self):
        main.autotune_session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=3)
        
        # Symulujemy próbkę z 1 wykrytą kartą, ale 0 zaakceptowanymi (rozpoznanymi)
        pipeline_sample = {
            "detected_count": 1,
            "accepted_count": 0,
            "analysis_ms": 15.0,
            "snapshot_quality_score": 0.88,
            "recognition_confidences": []
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        # Próbka POWINNA zostać zebrana pomimo braku rozpoznania (accepted_count == 0)
        self.assertEqual(len(main.autotune_session.samples["one_card"]), 1)
        saved_sample = main.autotune_session.samples["one_card"][0]
        self.assertEqual(saved_sample["candidate_count"], 1)
        self.assertEqual(saved_sample["accepted_count"], 0)
        self.assertEqual(saved_sample["false_positive_count"], 0)
        self.assertEqual(saved_sample["recognition_score"], 0.0)

    def test_collects_three_cards_sample_when_expected_count_three(self):
        main.autotune_session = AutotuneSession(required_scenarios=("three_cards",), samples_per_scenario=3)
        
        # Symulujemy próbkę z 3 kartami
        pipeline_sample = {
            "detected_count": 3,
            "accepted_count": 3,
            "analysis_ms": 22.0,
            "snapshot_quality_score": 0.95,
            "recognition_confidences": [0.9, 0.85, 0.94]
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        self.assertEqual(len(main.autotune_session.samples["three_cards"]), 1)
        saved_sample = main.autotune_session.samples["three_cards"][0]
        self.assertEqual(saved_sample["candidate_count"], 3)
        self.assertEqual(saved_sample["false_positive_count"], 0)

    def test_collects_partially_recognized_three_cards_sample(self):
        main.autotune_session = AutotuneSession(required_scenarios=("three_cards",), samples_per_scenario=3)
        
        # Symulujemy próbkę z 3 wykrytymi kartami, ale tylko 1 zaakceptowaną
        pipeline_sample = {
            "detected_count": 3,
            "accepted_count": 1,
            "analysis_ms": 22.0,
            "snapshot_quality_score": 0.95,
            "recognition_confidences": [0.9]
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        self.assertEqual(len(main.autotune_session.samples["three_cards"]), 1)
        saved_sample = main.autotune_session.samples["three_cards"][0]
        self.assertEqual(saved_sample["candidate_count"], 3)
        self.assertEqual(saved_sample["accepted_count"], 1)
        self.assertEqual(saved_sample["false_positive_count"], 0)
        self.assertEqual(saved_sample["recognition_score"], 0.9)

    def test_collects_empty_sample_with_false_positives(self):
        main.autotune_session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=3)
        
        pipeline_sample = {
            "detected_count": 2,
            "accepted_count": 0,
            "analysis_ms": 10.0,
            "snapshot_quality_score": 0.9
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        self.assertEqual(len(main.autotune_session.samples["empty"]), 1)
        saved_sample = main.autotune_session.samples["empty"][0]
        self.assertEqual(saved_sample["candidate_count"], 2)
        self.assertEqual(saved_sample["false_positive_count"], 2)

    def test_does_not_collect_wrong_card_count_for_scenario(self):
        # Oczekujemy 1 karty
        main.autotune_session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=3)
        
        # Na stole leżą 3 karty (błędna liczba kart dla scenariusza one_card)
        pipeline_sample = {
            "detected_count": 3,
            "accepted_count": 3,
            "analysis_ms": 22.0,
            "snapshot_quality_score": 0.95,
            "recognition_confidences": [0.9, 0.85, 0.94]
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        # Próbka nie powinna zostać zapisana!
        self.assertEqual(len(main.autotune_session.samples["one_card"]), 0)
        self.assertEqual(main.calibration_state["autotune"]["collected_count"], 0)
        self.assertTrue(any("Odrzucono snapshot" in w for w in main.operator_warnings))

    def test_does_not_collect_accepted_cards_on_empty_scenario(self):
        main.autotune_session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=3)
        
        pipeline_sample = {
            "detected_count": 1,
            "accepted_count": 1,
            "analysis_ms": 10.0,
            "snapshot_quality_score": 0.9,
            "recognition_confidences": [0.85]
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        self.assertEqual(len(main.autotune_session.samples["empty"]), 0)
        self.assertTrue(any("Odrzucono pusta mate" in w for w in main.operator_warnings))

    def test_does_not_collect_more_than_required_samples(self):
        main.autotune_session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=2)
        
        pipeline_sample = {
            "detected_count": 1,
            "accepted_count": 1,
            "analysis_ms": 15.0,
            "snapshot_quality_score": 0.88,
            "recognition_confidences": [0.92]
        }
        
        # Dodajemy 3 próbki (limit to 2)
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        self.assertEqual(len(main.autotune_session.samples["one_card"]), 2)
        self.assertTrue(main.autotune_session.ready_to_score())
        self.assertTrue(main.calibration_state["autotune"]["ready_to_score"])

    def test_cancel_stops_sample_collection(self):
        main.autotune_session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=3)
        
        pipeline_sample = {
            "detected_count": 0,
            "accepted_count": 0,
            "analysis_ms": 10.0,
            "snapshot_quality_score": 0.9
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        self.assertEqual(len(main.autotune_session.samples["empty"]), 1)
        
        # Anulujemy
        from tarotvision.tuning_protocol import ControlMessage
        main.handle_control_message(ControlMessage(type="autotune_cancel"), MagicMock())
        
        self.assertIsNone(main.autotune_session)
        
        # Kolejna próbka nie powinna spowodować crasha ani zapisania czegokolwiek
        main.record_autotune_sample_from_snapshot(pipeline_sample)

    def test_sample_payload_is_json_safe_and_does_not_contain_images(self):
        main.autotune_session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=3)
        
        pipeline_sample = {
            "detected_count": 1,
            "accepted_count": 1,
            "analysis_ms": 15.0,
            "snapshot_quality_score": 0.88,
            "recognition_confidences": [0.92]
        }
        
        main.record_autotune_sample_from_snapshot(pipeline_sample)
        
        saved_sample = main.autotune_session.samples["one_card"][0]
        
        # Weryfikacja bezpieczeństwa (brak obrazów)
        self.assertNotIn("frame", saved_sample)
        self.assertNotIn("image", saved_sample)
        self.assertNotIn("crop", saved_sample)
        
        # Sprawdzamy czy serializuje się do JSON
        json_str = json.dumps(saved_sample)
        self.assertTrue(isinstance(json_str, str))

    def test_existing_card_payload_contract_is_unchanged(self):
        # Upewniamy się, że build_operator_snapshot wciąż zwraca prawidłową strukturę
        snapshot = main.build_operator_snapshot(cards=[{"name": "RWS_01", "confidence": 0.88}])
        self.assertIn("calibration", snapshot)
        self.assertIn("autotune", snapshot["calibration"])
        
        # Sprawdzamy czy dane kart dla AR (wysyłane do status store) są nienaruszone
        main.status_store.update_cv_state(
            cards=[{"name": "RWS_01", "confidence": 0.88}],
            metrics={},
            runtime={},
            operator=snapshot
        )
        current_status = main.status_store.get_status()
        self.assertEqual(len(current_status["cards"]), 1)
        self.assertEqual(current_status["cards"][0]["name"], "RWS_01")
        self.assertEqual(current_status["cards"][0]["deck_id"], "rider-waite-smith")


if __name__ == "__main__":
    unittest.main()
