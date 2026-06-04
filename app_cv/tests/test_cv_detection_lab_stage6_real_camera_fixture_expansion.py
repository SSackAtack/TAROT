"""Tests for the minimal Stage 6 real-camera RWS expansion wizard."""
import json
import os
import shutil
import tempfile
import unittest

from tools.cv_detection_lab.stage6_real_camera_fixture_expansion_wizard import (
    build_expansion_plan,
    run_expansion_preflight,
)
from tools.cv_detection_lab.stage6_real_camera_capture_wizard import (
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
        self.assertTrue(all(step.expected_behavior == "reject" for step in plan))

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

    def test_expansion_preflight_blocks_incomplete_pack(self):
        os.makedirs(self.aggregate_dir)
        with open(os.path.join(self.aggregate_dir, "manifest.json"), "w", encoding="utf-8") as handle:
            json.dump({"fixture_id": "expansion", "samples": []}, handle)
        with open(os.path.join(self.aggregate_dir, "ground_truth.json"), "w", encoding="utf-8") as handle:
            json.dump({"fixture_id": "expansion", "labels": {}}, handle)

        report = run_expansion_preflight(self.aggregate_dir, self.output_dir)

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("MISSING_EXPANSION_SAMPLE", {item["code"] for item in report["errors"]})


if __name__ == "__main__":
    unittest.main()
