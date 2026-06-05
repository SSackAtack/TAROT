# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import shutil
import json
from unittest.mock import MagicMock

# Ustawiamy tryb testowy przed importem main.py
os.environ["TAROTVISION_TEST_MODE"] = "1"
import main
from tarotvision.autotune_session import AutotuneSession
from tarotvision.autotune_session_log import AutotuneSessionLog
from tarotvision.tuning_protocol import ControlMessage


class TestCalibrationWizardScoringIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_log_dir = main.LOG_DIR
        main.LOG_DIR = self.temp_dir
        
        # Inicjalizujemy logi sesji na tymczasowym katalogu
        main.autotune_session_log = AutotuneSessionLog(os.path.join(self.temp_dir, "autotune_sessions"))
        
        # Resetujemy zmienne globalne
        main.autotune_session = None
        main.autotune_candidate_profiles = []
        main.autotune_quality_report = None
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
        main.autotune_quality_report = None
        shutil.rmtree(self.temp_dir)

    def test_autotune_start_resets_quality_report(self):
        # Ustawiamy sztucznie raport
        main.autotune_quality_report = {"score": 0.8}
        self.assertIsNotNone(main.autotune_quality_report)
        
        # Wywołujemy start
        msg = ControlMessage(type="autotune_start", scenario="one_card")
        main.handle_control_message(msg, MagicMock())
        
        # Raport powinien być zresetowany do None
        self.assertIsNone(main.autotune_quality_report)
        
        payload = main.autotune_status_payload()
        self.assertIsNone(payload["quality_report"])
        self.assertFalse(payload["ready_for_session"])
        self.assertEqual(payload["operator_messages"], [])

    def test_autotune_cancel_resets_quality_report(self):
        main.autotune_quality_report = {"score": 0.9}
        
        # Wywołujemy cancel
        msg = ControlMessage(type="autotune_cancel")
        main.handle_control_message(msg, MagicMock())
        
        self.assertIsNone(main.autotune_quality_report)
        
        payload = main.autotune_status_payload()
        self.assertIsNone(payload["quality_report"])

    def test_autotune_calibrate_without_samples_keeps_quality_report_none(self):
        # Startujemy sesję
        msg_start = ControlMessage(type="autotune_start", scenario="one_card")
        main.handle_control_message(msg_start, MagicMock())
        
        # Wywołujemy calibrate bez próbek (powinno wyświetlić warning i nie wywoływać scoringu)
        msg_calib = ControlMessage(type="autotune_calibrate")
        main.handle_control_message(msg_calib, MagicMock())
        
        self.assertIsNone(main.autotune_quality_report)
        self.assertTrue(any("Brak kompletnych probek" in w for w in main.operator_warnings))

    def test_autotune_calibrate_sets_quality_report_when_samples_ready(self):
        # Startujemy sesję z limitami 3
        msg_start = ControlMessage(type="autotune_start", scenario="one_card")
        main.handle_control_message(msg_start, MagicMock())
        
        # Symulujemy dodanie 3 próbek (gotowych do scoringu)
        sample = {
            "detected_count": 1,
            "accepted_count": 1,
            "snapshot_quality_score": 0.90,
            "recognition_confidences": [0.85],
            "analysis_ms": 100.0,
        }
        main.record_autotune_sample_from_snapshot(sample)
        main.record_autotune_sample_from_snapshot(sample)
        main.record_autotune_sample_from_snapshot(sample)
        
        self.assertTrue(main.autotune_session.ready_to_score())
        
        # Wywołujemy calibrate
        msg_calib = ControlMessage(type="autotune_calibrate")
        main.handle_control_message(msg_calib, MagicMock())
        
        # Raport powinien być wygenerowany
        self.assertIsNotNone(main.autotune_quality_report)
        self.assertGreater(main.autotune_quality_report["score"], 0.80)
        self.assertTrue(main.autotune_quality_report["ready_for_session"])
        
        payload = main.autotune_status_payload()
        self.assertIsNotNone(payload["quality_report"])
        self.assertTrue(payload["ready_for_session"])
        self.assertEqual(payload["quality_report"]["grade"], "excellent")
        self.assertTrue(any("Ocena stanowiska gotowa" in w for w in main.operator_warnings))

    def test_autotune_apply_is_not_called_by_scoring(self):
        # Weryfikujemy, że scoring nie uruchamia automatycznego apply (parametry w config session nie zmieniają się)
        old_params = dict(main.runtime_config.values)
        
        msg_start = ControlMessage(type="autotune_start", scenario="empty")
        main.handle_control_message(msg_start, MagicMock())
        
        sample = {
            "detected_count": 0,
            "accepted_count": 0,
            "snapshot_quality_score": 0.85,
            "analysis_ms": 50.0,
        }
        main.record_autotune_sample_from_snapshot(sample)
        main.record_autotune_sample_from_snapshot(sample)
        main.record_autotune_sample_from_snapshot(sample)
        
        msg_calib = ControlMessage(type="autotune_calibrate")
        main.handle_control_message(msg_calib, MagicMock())
        
        # Parametry w config_session nie powinny ulec zmianie
        self.assertEqual(main.runtime_config.values, old_params)


if __name__ == "__main__":
    unittest.main()
