# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Ustawiamy tryb testowy przed importem main.py
os.environ["TAROTVISION_TEST_MODE"] = "1"
import main
from tarotvision.tuning_protocol import ControlMessage


class TestAutotuneLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_log_dir = main.LOG_DIR
        main.LOG_DIR = self.temp_dir
        
        # Inicjalizujemy logi sesji na tymczasowym katalogu
        from tarotvision.autotune_session_log import AutotuneSessionLog
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

    @patch("main.add_operator_warning")
    def test_autotune_start_creates_session(self, mock_warn):
        message = ControlMessage(type="autotune_start", scenario="three_cards")
        camera_mock = MagicMock()
        
        main.handle_control_message(message, camera_mock)
        
        self.assertIsNotNone(main.autotune_session)
        self.assertEqual(main.autotune_session.current_scenario(), "three_cards")
        self.assertEqual(main.calibration_state["state"], "collecting")
        self.assertEqual(main.calibration_state["autotune"]["scenario"], "three_cards")
        self.assertEqual(main.calibration_state["autotune"]["state"], "collecting")
        
        mock_warn.assert_any_call("Autotuning: zbieram probki scenariusza three_cards")

    @patch("main.add_operator_warning")
    def test_autotune_cancel_clears_session(self, mock_warn):
        # Najpierw startujemy
        message_start = ControlMessage(type="autotune_start", scenario="one_card")
        camera_mock = MagicMock()
        main.handle_control_message(message_start, camera_mock)
        
        # Anulujemy
        message_cancel = ControlMessage(type="autotune_cancel")
        main.handle_control_message(message_cancel, camera_mock)
        
        self.assertIsNone(main.autotune_session)
        self.assertEqual(main.calibration_state["state"], "idle")
        self.assertEqual(main.calibration_state["autotune"]["state"], "idle")
        self.assertIsNone(main.calibration_state["autotune"]["scenario"])
        
        mock_warn.assert_any_call("Anulowano autotuning")

    @patch("main.add_operator_warning")
    def test_autotune_calibrate_no_samples_warning(self, mock_warn):
        message_start = ControlMessage(type="autotune_start", scenario="three_cards")
        camera_mock = MagicMock()
        main.handle_control_message(message_start, camera_mock)
        
        # Próba kalibracji bez próbek
        message_cal = ControlMessage(type="autotune_calibrate")
        main.handle_control_message(message_cal, camera_mock)
        
        mock_warn.assert_any_call("Brak kompletnych probek autotuningu do kalibracji")

    @patch("main.add_operator_warning")
    def test_autotune_apply_no_recommendation_warning(self, mock_warn):
        message_start = ControlMessage(type="autotune_start", scenario="three_cards")
        camera_mock = MagicMock()
        main.handle_control_message(message_start, camera_mock)
        
        # Próba apply bez rekomendacji
        message_apply = ControlMessage(type="autotune_apply")
        main.handle_control_message(message_apply, camera_mock)
        
        mock_warn.assert_any_call("Brak rekomendacji autotuningu do zastosowania")

    @patch("main.add_operator_warning")
    def test_autotune_save_no_recommendation_warning(self, mock_warn):
        message_start = ControlMessage(type="autotune_start", scenario="three_cards")
        camera_mock = MagicMock()
        main.handle_control_message(message_start, camera_mock)
        
        # Próba save bez rekomendacji
        message_save = ControlMessage(type="autotune_save", name="my_profile")
        main.handle_control_message(message_save, camera_mock)
        
        mock_warn.assert_any_call("Brak rekomendacji autotuningu do zapisania")

    @patch("main.add_operator_warning")
    @patch("main.profile_store")
    @patch("main.config_session")
    def test_autotune_full_flow_with_mocked_samples(self, mock_config, mock_profile_store, mock_warn):
        message_start = ControlMessage(type="autotune_start", scenario="three_cards")
        camera_mock = MagicMock()
        main.handle_control_message(message_start, camera_mock)
        
        # Dodajemy sztucznie 3 poprawne próbki
        sample = {
            "candidate_count": 3,
            "accepted_count": 3,
            "candidate_validation_rejections": 0,
            "recognition_rejections": 0
        }
        main.autotune_session.add_sample("three_cards", sample)
        main.autotune_session.add_sample("three_cards", sample)
        main.autotune_session.add_sample("three_cards", sample)
        
        self.assertTrue(main.autotune_session.ready_to_score())
        
        # Kalibrujemy
        message_cal = ControlMessage(type="autotune_calibrate")
        main.handle_control_message(message_cal, camera_mock)
        
        self.assertEqual(main.calibration_state["state"], "recommendation_ready")
        self.assertIsNotNone(main.autotune_session.recommendation)
        
        # Zastosujemy
        message_apply = ControlMessage(type="autotune_apply")
        main.handle_control_message(message_apply, camera_mock)
        
        self.assertEqual(main.calibration_state["state"], "applied")
        mock_config.update.assert_called()
        mock_config.commit_stable.assert_called_once()
        
        # Zapisujemy
        message_save = ControlMessage(type="autotune_save", name="my_autotune_profile")
        main.handle_control_message(message_save, camera_mock)
        
        mock_profile_store.save_autotune_recommendation.assert_called_once_with(
            "my_autotune_profile", main.autotune_session.recommendation
        )
        self.assertEqual(main.active_tuning_profile, "my_autotune_profile")

    def test_build_operator_snapshot_contains_autotune(self):
        snapshot = main.build_operator_snapshot()
        self.assertIn("calibration", snapshot)
        self.assertIn("autotune", snapshot["calibration"])
        self.assertEqual(snapshot["calibration"]["autotune"]["state"], "idle")
        self.assertIsNone(snapshot["calibration"]["autotune"]["scenario"])


if __name__ == "__main__":
    unittest.main()
