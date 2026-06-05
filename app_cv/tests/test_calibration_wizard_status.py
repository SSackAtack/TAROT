# -*- coding: utf-8 -*-
import unittest
import json
import os
from unittest.mock import MagicMock

# Ustawiamy tryb testowy przed importem main.py
os.environ["TAROTVISION_TEST_MODE"] = "1"
import main

from tarotvision.calibration_wizard_status import build_calibration_wizard_status
from tarotvision.autotune_session import AutotuneSession


class TestCalibrationWizardStatus(unittest.TestCase):

    def test_idle_status_has_full_contract(self):
        status = build_calibration_wizard_status(session=None, quality_report=None)
        
        # Verify existence of all contract fields
        self.assertEqual(status["schema_version"], 1)
        self.assertEqual(status["mode"], "calibration_wizard")
        self.assertIsNone(status["scenario"])
        self.assertEqual(status["state"], "idle")
        self.assertEqual(status["collected_count"], 0)
        self.assertEqual(status["required_count"], 3)
        self.assertFalse(status["ready_to_score"])
        self.assertIsNone(status["quality_report"])
        self.assertFalse(status["ready_for_session"])
        self.assertFalse(status["current_step_ready"])
        self.assertFalse(status["overall_wizard_ready"])
        self.assertEqual(status["operator_messages"], [])
        self.assertEqual(status["warnings"], [])
        self.assertEqual(status["blocking_issues"], [])
        self.assertIsNone(status["recommendation"])
        self.assertIsNone(status["last_score"])
        self.assertEqual(status["next_action"], "Rozpocznij autotuning z poziomu konsoli.")

    def test_active_status_without_quality_report_has_full_contract(self):
        session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=3)
        status = build_calibration_wizard_status(session=session, quality_report=None)
        
        self.assertEqual(status["scenario"], "one_card")
        self.assertEqual(status["state"], "collecting")
        self.assertEqual(status["collected_count"], 0)
        self.assertEqual(status["required_count"], 3)
        self.assertFalse(status["ready_to_score"])
        self.assertIsNone(status["quality_report"])
        self.assertFalse(status["ready_for_session"])
        self.assertFalse(status["current_step_ready"])
        self.assertEqual(status["operator_messages"], [])

    def test_active_status_with_quality_report_has_full_contract(self):
        session = AutotuneSession(required_scenarios=("three_cards",), samples_per_scenario=3)
        report = {
            "score": 0.85,
            "grade": "good",
            "ready_for_session": True,
            "operator_messages": ["Warunki OK"],
            "warnings": ["Lekki cien"],
            "blocking_issues": []
        }
        status = build_calibration_wizard_status(session=session, quality_report=report)
        
        self.assertEqual(status["quality_report"], report)
        self.assertTrue(status["ready_for_session"])
        self.assertTrue(status["current_step_ready"])
        self.assertEqual(status["operator_messages"], ["Warunki OK"])
        self.assertEqual(status["warnings"], ["Lekki cien"])
        self.assertEqual(status["blocking_issues"], [])

    def test_quality_report_messages_are_lifted_to_top_level(self):
        report = {
            "operator_messages": ["Message 1", "Message 2"]
        }
        status = build_calibration_wizard_status(session=None, quality_report=report)
        self.assertEqual(status["operator_messages"], ["Message 1", "Message 2"])

    def test_quality_report_warnings_are_lifted_to_top_level(self):
        report = {
            "warnings": ["Warning A", "Warning B"]
        }
        status = build_calibration_wizard_status(session=None, quality_report=report)
        self.assertEqual(status["warnings"], ["Warning A", "Warning B"])

    def test_quality_report_blocking_issues_are_lifted_to_top_level(self):
        report = {
            "blocking_issues": ["Issue X"]
        }
        status = build_calibration_wizard_status(session=None, quality_report=report)
        self.assertEqual(status["blocking_issues"], ["Issue X"])

    def test_ready_for_session_maps_to_current_step_ready(self):
        report = {"ready_for_session": True}
        status = build_calibration_wizard_status(session=None, quality_report=report)
        self.assertTrue(status["ready_for_session"])
        self.assertTrue(status["current_step_ready"])

    def test_overall_wizard_ready_defaults_false(self):
        report = {"ready_for_session": True}
        status = build_calibration_wizard_status(session=None, quality_report=report)
        self.assertFalse(status["overall_wizard_ready"])

    def test_recommendation_and_quality_report_are_separate(self):
        session = MagicMock()
        session.recommendation = {"profile": "test_profile", "score": 0.9}
        report = {"score": 0.85, "grade": "good"}
        
        status = build_calibration_wizard_status(session=session, quality_report=report)
        self.assertEqual(status["recommendation"], session.recommendation)
        self.assertEqual(status["quality_report"], report)
        self.assertEqual(status["last_score"], 0.9)

    def test_missing_quality_report_fields_do_not_crash(self):
        report = {
            "score": 0.85
            # missing warnings, blocking_issues, operator_messages, ready_for_session
        }
        try:
            status = build_calibration_wizard_status(session=None, quality_report=report)
            self.assertFalse(status["ready_for_session"])
            self.assertEqual(status["warnings"], [])
        except Exception as exc:
            self.fail(f"Builder crashed on incomplete quality report: {exc}")

    def test_missing_session_methods_do_not_crash(self):
        session = MagicMock(spec=[]) # session without any attributes/methods
        try:
            status = build_calibration_wizard_status(session=session, quality_report=None)
            self.assertIsNone(status["scenario"])
            self.assertEqual(status["state"], "collecting")
            self.assertEqual(status["collected_count"], 0)
        except Exception as exc:
            self.fail(f"Builder crashed on empty mock session: {exc}")

    def test_status_is_json_serializable(self):
        status = build_calibration_wizard_status(session=None, quality_report=None)
        try:
            json_str = json.dumps(status)
            self.assertIsInstance(json_str, str)
        except Exception as exc:
            self.fail(f"Status dict is not JSON-serializable: {exc}")

    def test_autotune_status_payload_uses_status_builder(self):
        # We check that the integration in main.py works as expected
        main.autotune_session = None
        main.autotune_quality_report = None
        
        payload = main.autotune_status_payload()
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["mode"], "calibration_wizard")
        self.assertEqual(payload["state"], "idle")


if __name__ == "__main__":
    unittest.main()
