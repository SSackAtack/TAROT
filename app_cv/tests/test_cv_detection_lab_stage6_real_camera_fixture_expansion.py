"""Tests for the minimal Stage 6 real-camera RWS expansion wizard."""
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.cv_detection_lab.stage6_real_camera_fixture_expansion_wizard import (
    build_expansion_plan,
    run_expansion_preflight,
)
from tools.cv_detection_lab.stage6_real_camera_capture_wizard import (
    _run_single_step,
    append_confirmed_sample,
    write_camera_snapshot_session,
)


class TestStage6RealCameraFixtureExpansion(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_expansion_")
        self.aggregate_dir = os.path.join(self.tmpdir, "aggregate")
        self.output_dir = os.path.join(self.tmpdir, "output")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_minimal_rws_plan_has_eight_balanced_samples(self):
        plan = build_expansion_plan()

        self.assertEqual(len(plan), 8)
        self.assertEqual(sum(step.category.endswith("_clear") for step in plan), 4)
        self.assertEqual(sum(step.category.endswith("_glare") for step in plan), 4)
        self.assertEqual(sum("bright" in step.category for step in plan), 4)
        self.assertEqual(sum("dark" in step.category for step in plan), 4)
        self.assertEqual(sum(step.expected_orientation == "reversed" for step in plan), 4)
        self.assertTrue(all(step.deck == "rider-waite-smith" for step in plan))
        self.assertTrue(all(step.expected_behavior == "identify" for step in plan))
        self.assertTrue(all(step.expected_card_id == step.card_label for step in plan))
        self.assertEqual(
            {step.expected_card_id for step in plan if "bright" in step.category},
            {"RWS_03", "RWS_06", "RWS_12", "RWS_20"},
        )
        self.assertEqual(
            {step.expected_card_id for step in plan if "dark" in step.category},
            {"RWS_04", "RWS_08", "RWS_15", "RWS_21"},
        )

    def test_shared_step_output_uses_expansion_total_instead_of_legacy_28(self):
        step = build_expansion_plan()[0]
        output = StringIO()

        with patch(
            "tools.cv_detection_lab.stage6_real_camera_capture_wizard._run_camera_snapshot_step"
        ), redirect_stdout(output):
            _run_single_step(step, "session", "aggregate", "camera_snapshot", 0, "logs", total_steps=8)

        self.assertIn("KROK 1/8", output.getvalue())
        self.assertNotIn("KROK 1/28", output.getvalue())

    def test_main_launcher_defaults_to_minimal_rws_expansion(self):
        launcher = Path(__file__).resolve().parents[2] / "stage6_capture_wizard.bat"
        text = launcher.read_text(encoding="utf-8")

        self.assertIn("Minimal RWS Expansion - 8 samples", text)
        self.assertIn('if /I "%~1"=="legacy"', text)
        self.assertIn("stage6_real_camera_fixture_expansion_wizard.py", text)
        self.assertIn("CAMERA_OWNER_PID", text)

    def test_branch_independent_starter_blocks_when_backend_main_owns_camera(self):
        starter = Path(r"E:\Antigravity\Projekty\START_TAROT_STAGE6_RWS_8_PROBEK.bat")
        text = starter.read_text(encoding="utf-8")

        self.assertIn("CAMERA_OWNER_PID", text)
        self.assertIn("Zamknij backend TarotVision", text)
        self.assertIn("exit /b 2", text)

    def test_expansion_preflight_passes_complete_eight_sample_pack(self):
        for step in build_expansion_plan():
            session_root = os.path.join(self.tmpdir, step.session_id)

            def fake_writer(path, _frame):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as handle:
                    handle.write(b"image")
                return True

            write_camera_snapshot_session(step, object(), session_root, image_writer=fake_writer)
            append_confirmed_sample(step, session_root, self.aggregate_dir)

        report = run_expansion_preflight(self.aggregate_dir, self.output_dir)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["sample_count"], 8)
        self.assertTrue(os.path.isfile(os.path.join(self.output_dir, "preflight_report.json")))

    def test_expansion_preflight_blocks_ground_truth_identity_mismatch(self):
        self._write_complete_pack()
        ground_truth_path = os.path.join(self.aggregate_dir, "ground_truth.json")
        with open(ground_truth_path, encoding="utf-8") as handle:
            ground_truth = json.load(handle)
        first_label = next(iter(ground_truth["labels"].values()))
        first_label["expected_card_id"] = "RWS_77"
        with open(ground_truth_path, "w", encoding="utf-8") as handle:
            json.dump(ground_truth, handle)

        report = run_expansion_preflight(self.aggregate_dir, self.output_dir)

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("GROUND_TRUTH_LABEL_MISMATCH", {item["code"] for item in report["errors"]})

    def test_expansion_preflight_blocks_missing_capture_file(self):
        self._write_complete_pack()
        first = build_expansion_plan()[0]
        os.remove(os.path.join(self.tmpdir, first.session_id, "one_card", "analysis_frame_1.png"))

        report = run_expansion_preflight(self.aggregate_dir, self.output_dir)

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("MISSING_CAPTURE_FILE", {item["code"] for item in report["errors"]})

    def test_expansion_preflight_blocks_incomplete_pack(self):
        os.makedirs(self.aggregate_dir)
        with open(os.path.join(self.aggregate_dir, "manifest.json"), "w", encoding="utf-8") as handle:
            json.dump({"fixture_id": "expansion", "samples": []}, handle)
        with open(os.path.join(self.aggregate_dir, "ground_truth.json"), "w", encoding="utf-8") as handle:
            json.dump({"fixture_id": "expansion", "labels": {}}, handle)

        report = run_expansion_preflight(self.aggregate_dir, self.output_dir)

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("MISSING_EXPANSION_SAMPLE", {item["code"] for item in report["errors"]})

    def _write_complete_pack(self):
        for step in build_expansion_plan():
            session_root = os.path.join(self.tmpdir, step.session_id)

            def fake_writer(path, _frame):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as handle:
                    handle.write(b"image")
                return True

            write_camera_snapshot_session(step, object(), session_root, image_writer=fake_writer)
            append_confirmed_sample(step, session_root, self.aggregate_dir)


if __name__ == "__main__":
    unittest.main()
