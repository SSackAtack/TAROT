"""Tests for Stage 6 real-camera aggregate fixture offline tooling."""
import json
import os
import shutil
import tempfile
import unittest

from tools.cv_detection_lab.stage6_real_camera_fixture import (
    load_aggregate,
    session_fingerprint,
    stable_sample_id,
)
from tools.cv_detection_lab.stage6_real_camera_manual_review_pack import build_manual_review_pack
from tools.cv_detection_lab.stage6_real_camera_preflight import run_preflight
from tools.cv_detection_lab.stage6_real_camera_capture_wizard import (
    append_confirmed_sample,
    build_capture_plan,
    capture_status_message,
    expected_env_commands,
    resolve_manual_card_identity,
)


class TestStage6RealCameraFixture(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_real_camera_")
        self.sessions_dir = os.path.join(self.tmpdir, "sessions")
        self.aggregate_dir = os.path.join(self.tmpdir, "aggregate")
        self.output_dir = os.path.join(self.tmpdir, "output")
        os.makedirs(self.sessions_dir)
        os.makedirs(self.aggregate_dir)
        self.samples = self._build_minimum_sessions()
        self.manifest_path = os.path.join(self.aggregate_dir, "manifest.json")
        self.ground_truth_path = os.path.join(self.aggregate_dir, "ground_truth.json")
        self._write_aggregate(self.samples)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_stable_sample_id_changes_with_each_identity_component(self):
        baseline = stable_sample_id("session-a", "one_card", "gilded_upright")

        self.assertEqual(baseline, stable_sample_id("session-a", "one_card", "gilded_upright"))
        self.assertNotEqual(baseline, stable_sample_id("session-b", "one_card", "gilded_upright"))
        self.assertNotEqual(baseline, stable_sample_id("session-a", "three_cards", "gilded_upright"))
        self.assertNotEqual(baseline, stable_sample_id("session-a", "one_card", "gilded_reversed"))

    def test_load_aggregate_is_read_only_and_matches_ground_truth(self):
        before = session_fingerprint(os.path.join(self.sessions_dir, self.samples[0]["session_id"]))

        aggregate = load_aggregate(self.manifest_path, self.ground_truth_path)

        after = session_fingerprint(os.path.join(self.sessions_dir, self.samples[0]["session_id"]))
        self.assertEqual(before, after)
        self.assertEqual(len(aggregate.samples), 28)
        self.assertEqual(set(aggregate.labels), {sample.sample_id for sample in aggregate.samples})

    def test_preflight_passes_complete_minimum_fixture_without_mutating_sessions(self):
        before = self._all_fingerprints()

        report = run_preflight(self.manifest_path, self.ground_truth_path, self.output_dir)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(before, self._all_fingerprints())
        self.assertTrue(os.path.isfile(os.path.join(self.output_dir, "preflight_report.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.output_dir, "preflight_report.md")))

    def test_preflight_blocks_duplicate_session_reference(self):
        manifest = self._load(self.manifest_path)
        manifest["samples"][1]["session_id"] = manifest["samples"][0]["session_id"]
        manifest["samples"][1]["session_path"] = manifest["samples"][0]["session_path"]
        self._dump(self.manifest_path, manifest)

        report = run_preflight(self.manifest_path, self.ground_truth_path)

        self.assertEqual(report["status"], "PROVISIONAL_BLOCKED")
        self.assertIn("DUPLICATE_SESSION_REFERENCE", {item["code"] for item in report["errors"]})

    def test_preflight_blocks_wrong_deck_and_reversed_contract_errors(self):
        ground_truth = self._load(self.ground_truth_path)
        wrong_id = next(item["sample_id"] for item in self.samples if item["category"] == "wrong_deck_magic")
        reversed_id = next(item["sample_id"] for item in self.samples if item["category"] == "gilded_reversed")
        ground_truth["labels"][wrong_id]["expected_behavior"] = "identify"
        ground_truth["labels"][reversed_id]["expected_orientation"] = "upright"
        self._dump(self.ground_truth_path, ground_truth)

        report = run_preflight(self.manifest_path, self.ground_truth_path)
        codes = {item["code"] for item in report["errors"]}

        self.assertIn("WRONG_DECK_BEHAVIOR_INVALID", codes)
        self.assertIn("REVERSED_ORIENTATION_INVALID", codes)

    def test_preflight_blocks_ground_truth_label_contradiction(self):
        ground_truth = self._load(self.ground_truth_path)
        sample_id = self.samples[0]["sample_id"]
        ground_truth["labels"][sample_id]["expected_card_id"] = "Gilded_wrong"
        self._dump(self.ground_truth_path, ground_truth)

        report = run_preflight(self.manifest_path, self.ground_truth_path)

        self.assertIn("GROUND_TRUTH_LABEL_MISMATCH", {item["code"] for item in report["errors"]})

    def test_preflight_blocks_unconfirmed_and_missing_minimum_category(self):
        manifest = self._load(self.manifest_path)
        removed = manifest["samples"].pop()
        self._dump(self.manifest_path, manifest)
        ground_truth = self._load(self.ground_truth_path)
        ground_truth["labels"].pop(removed["sample_id"])
        ground_truth["labels"][manifest["samples"][0]["sample_id"]]["label_status"] = "draft"
        self._dump(self.ground_truth_path, ground_truth)

        report = run_preflight(self.manifest_path, self.ground_truth_path)
        codes = {item["code"] for item in report["errors"]}

        self.assertIn("LABEL_NOT_MANUALLY_CONFIRMED", codes)
        self.assertIn("MINIMUM_SAMPLE_COUNT_NOT_MET", codes)

    def test_blocked_preflight_markdown_does_not_claim_no_errors(self):
        manifest = self._load(self.manifest_path)
        manifest["samples"].pop()
        self._dump(self.manifest_path, manifest)

        run_preflight(self.manifest_path, self.ground_truth_path, self.output_dir)

        with open(os.path.join(self.output_dir, "preflight_report.md"), encoding="utf-8") as handle:
            markdown = handle.read()
        errors_section = markdown.split("## Errors", 1)[1].split("## Required Next Action", 1)[0]
        self.assertIn("MANIFEST_GROUND_TRUTH_MISMATCH", errors_section)
        self.assertNotIn("- None", errors_section)

    def test_manual_review_pack_requires_pass_and_preserves_sessions(self):
        preflight = run_preflight(self.manifest_path, self.ground_truth_path, self.output_dir)
        preflight_path = os.path.join(self.output_dir, "preflight_report.json")
        pack_dir = os.path.join(self.output_dir, "manual_review_pack")
        before = self._all_fingerprints()

        result = build_manual_review_pack(self.manifest_path, self.ground_truth_path, preflight_path, pack_dir)

        self.assertEqual(result["sample_count"], 28)
        self.assertEqual(before, self._all_fingerprints())
        self.assertTrue(os.path.isfile(os.path.join(pack_dir, "README_FOR_SUPERVISOR.md")))
        self.assertTrue(os.path.isfile(os.path.join(pack_dir, "category_index.json")))
        self.assertTrue(os.path.isfile(os.path.join(pack_dir, "similarity_groups.json")))
        self.assertEqual(len(os.listdir(os.path.join(pack_dir, "samples"))), 28)

    def test_capture_wizard_plan_contains_required_28_operator_steps(self):
        plan = build_capture_plan()

        self.assertEqual(len(plan), 28)
        self.assertEqual(sum(1 for step in plan if step.category == "gilded_upright"), 6)
        self.assertEqual(sum(1 for step in plan if step.category == "gilded_reversed"), 6)
        self.assertEqual(sum(1 for step in plan if step.category == "wrong_deck_magic"), 4)
        self.assertEqual(sum(1 for step in plan if step.category == "wrong_deck_marchetti"), 4)
        self.assertEqual(sum(1 for step in plan if step.category == "gilded_yellow"), 4)
        self.assertEqual(sum(1 for step in plan if step.category == "gilded_visually_similar"), 4)
        self.assertEqual(
            [step.expected_card_id for step in plan if step.category == "gilded_upright"],
            [step.expected_card_id for step in plan if step.category == "gilded_reversed"],
        )
        self.assertTrue(all(step.expected_card_id is None for step in plan if step.category == "gilded_yellow"))
        self.assertTrue(all(step.expected_card_id is None for step in plan if step.category == "gilded_visually_similar"))

    def test_capture_wizard_prints_existing_live_capture_env_commands(self):
        step = build_capture_plan()[0]

        commands = expected_env_commands(step)

        self.assertIn('$env:TAROTVISION_CAPTURE_LIVE_FIXTURES = "1"', commands)
        self.assertIn(f'$env:TAROTVISION_LIVE_FIXTURE_NAME = "{step.session_id}"', commands)
        self.assertIn('$env:TAROTVISION_LIVE_FIXTURE_SCENARIO = "one_card"', commands)

    def test_capture_wizard_appends_confirmed_session_to_aggregate(self):
        aggregate_dir = os.path.join(self.tmpdir, "wizard_aggregate")
        session_id = "stage6_real_gilded_01_upright"
        self._write_session(session_id, 91)
        step = build_capture_plan()[0]
        step = step.__class__(
            index=step.index,
            session_id=session_id,
            category=step.category,
            deck=step.deck,
            card_label=step.card_label,
            expected_card_id=step.expected_card_id,
            expected_orientation=step.expected_orientation,
            expected_behavior=step.expected_behavior,
            quality_expectation=step.quality_expectation,
            similarity_group=step.similarity_group,
            operator_instruction=step.operator_instruction,
        )

        result = append_confirmed_sample(
            step,
            session_root=os.path.join(self.sessions_dir, session_id),
            aggregate_dir=aggregate_dir,
        )

        self.assertEqual(result["status"], "RECORDED")
        manifest = self._load(os.path.join(aggregate_dir, "manifest.json"))
        ground_truth = self._load(os.path.join(aggregate_dir, "ground_truth.json"))
        self.assertEqual(len(manifest["samples"]), 1)
        sample = manifest["samples"][0]
        self.assertEqual(sample["sample_id"], stable_sample_id(session_id, "one_card", step.category))
        self.assertEqual(sample["session_id"], session_id)
        self.assertEqual(sample["expected_card_id"], step.expected_card_id)
        self.assertEqual(ground_truth["labels"][sample["sample_id"]]["label_status"], "manual_confirmed")

    def test_capture_wizard_refuses_to_record_incomplete_session(self):
        aggregate_dir = os.path.join(self.tmpdir, "wizard_aggregate")
        session_id = "stage6_real_incomplete"
        scenario_dir = os.path.join(self.sessions_dir, session_id, "one_card")
        os.makedirs(scenario_dir)
        step = build_capture_plan()[0]
        step = step.__class__(
            index=step.index,
            session_id=session_id,
            category=step.category,
            deck=step.deck,
            card_label=step.card_label,
            expected_card_id=step.expected_card_id,
            expected_orientation=step.expected_orientation,
            expected_behavior=step.expected_behavior,
            quality_expectation=step.quality_expectation,
            similarity_group=step.similarity_group,
            operator_instruction=step.operator_instruction,
        )

        with self.assertRaisesRegex(ValueError, "missing required capture files"):
            append_confirmed_sample(
                step,
                session_root=os.path.join(self.sessions_dir, session_id),
                aggregate_dir=aggregate_dir,
            )

        self.assertFalse(os.path.exists(os.path.join(aggregate_dir, "manifest.json")))

    def test_capture_wizard_explains_missing_session_folder(self):
        step = build_capture_plan()[0]
        session_root = os.path.join(self.sessions_dir, step.session_id)

        message = capture_status_message(step, session_root)

        self.assertIn("Folder sesji jeszcze nie istnieje", message)
        self.assertIn(step.session_id, message)
        self.assertIn("TAROTVISION_LIVE_FIXTURE_NAME", message)
        self.assertIn("backend", message)

    def test_capture_wizard_explains_missing_required_files(self):
        step = build_capture_plan()[0]
        session_root = os.path.join(self.sessions_dir, step.session_id)
        os.makedirs(os.path.join(session_root, "one_card"))

        message = capture_status_message(step, session_root)

        self.assertIn("Folder scenariusza istnieje", message)
        self.assertIn("Brakujące pliki", message)
        self.assertIn("analysis_frame_1.png", message)
        self.assertIn("raw_frame_1.png", message)

    def test_capture_wizard_requires_real_gilded_id_for_manual_categories(self):
        yellow = next(step for step in build_capture_plan() if step.category == "gilded_yellow")

        resolved = resolve_manual_card_identity(yellow, "Gilded_34", None)

        self.assertEqual(resolved.expected_card_id, "Gilded_34")
        self.assertEqual(resolved.card_label, "Gilded_34")

        with self.assertRaisesRegex(ValueError, "expected_card_id must match Gilded_<number>"):
            resolve_manual_card_identity(yellow, "Gilded_YELLOW_01", None)
        with self.assertRaisesRegex(ValueError, "expected_card_id must match Gilded_<number>"):
            resolve_manual_card_identity(yellow, "Magic_01", None)

    def test_capture_wizard_requires_similarity_group_for_visually_similar(self):
        similar = next(step for step in build_capture_plan() if step.category == "gilded_visually_similar")

        resolved = resolve_manual_card_identity(similar, "Gilded_54", "court-wands")

        self.assertEqual(resolved.expected_card_id, "Gilded_54")
        self.assertEqual(resolved.similarity_group, "court-wands")

        with self.assertRaisesRegex(ValueError, "similarity_group is required"):
            resolve_manual_card_identity(similar, "Gilded_54", "")

    def test_preflight_blocks_placeholder_expected_card_ids(self):
        manifest = self._load(self.manifest_path)
        sample_id = next(item["sample_id"] for item in self.samples if item["category"] == "gilded_yellow")
        sample = next(item for item in manifest["samples"] if item["sample_id"] == sample_id)
        sample["expected_card_id"] = "Gilded_YELLOW_01"
        self._dump(self.manifest_path, manifest)
        ground_truth = self._load(self.ground_truth_path)
        ground_truth["labels"][sample_id]["expected_card_id"] = "Gilded_YELLOW_01"
        self._dump(self.ground_truth_path, ground_truth)

        report = run_preflight(self.manifest_path, self.ground_truth_path)

        self.assertIn("INVALID_EXPECTED_CARD_ID_PLACEHOLDER", {item["code"] for item in report["errors"]})

    def _build_minimum_sessions(self):
        specifications = []
        for index in range(6):
            specifications.append(("gilded_upright", f"Gilded_{index:02d}", "upright", "identify", None))
            specifications.append(("gilded_reversed", f"Gilded_{index:02d}", "reversed", "identify", None))
        for index in range(4):
            specifications.append(("wrong_deck_magic", None, "not_applicable", "reject", None))
            specifications.append(("wrong_deck_marchetti", None, "not_applicable", "reject", None))
            specifications.append(("gilded_yellow", f"Gilded_{20 + index:02d}", "upright", "identify", None))
        for index in range(4):
            specifications.append((
                "gilded_visually_similar",
                f"Gilded_{40 + index:02d}",
                "upright",
                "identify",
                f"similar-{index // 2 + 1}",
            ))
        samples = []
        for index, (category, card_id, orientation, behavior, similarity_group) in enumerate(specifications):
            session_id = f"stage6_real_session_{index:02d}"
            self._write_session(session_id, index)
            sample_id = stable_sample_id(session_id, "one_card", category)
            samples.append({
                "sample_id": sample_id,
                "session_id": session_id,
                "session_path": os.path.relpath(os.path.join(self.sessions_dir, session_id), self.aggregate_dir),
                "scenario": "one_card",
                "category": category,
                "expected_deck": "gilded" if not category.startswith("wrong_deck") else category.split("_")[-1],
                "expected_card_id": card_id,
                "expected_orientation": orientation,
                "expected_behavior": behavior,
                "quality_expectation": "YELLOW" if category == "gilded_yellow" else "PASS_OR_YELLOW",
                "similarity_group": similarity_group,
                "notes": "",
            })
        return samples

    def _write_session(self, session_id, index):
        session_dir = os.path.join(self.sessions_dir, session_id)
        scenario_dir = os.path.join(session_dir, "one_card")
        os.makedirs(scenario_dir)
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04"
            b"\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        self._write_bytes(os.path.join(scenario_dir, "analysis_frame_1.png"), png_bytes)
        self._write_bytes(os.path.join(scenario_dir, "raw_frame_1.png"), png_bytes)
        self._dump(os.path.join(scenario_dir, "payload.json"), {"cards": []})
        self._dump(os.path.join(scenario_dir, "metrics.json"), {"crop_quality_status": "YELLOW"})
        self._dump(os.path.join(scenario_dir, "roi_diagnostics.json"), [])
        self._dump(os.path.join(session_dir, "manifest.json"), {"fixture_id": session_id, "scenarios": ["one_card"]})

    def _write_aggregate(self, samples):
        self._dump(self.manifest_path, {
            "fixture_id": "stage6_real_camera_validation",
            "manifest_version": 1,
            "capture_policy": "immutable_sessions",
            "samples": samples,
        })
        labels = {}
        for sample in samples:
            labels[sample["sample_id"]] = {
                "sample_id": sample["sample_id"],
                "expected_deck": sample["expected_deck"],
                "expected_card_id": sample["expected_card_id"],
                "expected_orientation": sample["expected_orientation"],
                "expected_behavior": sample["expected_behavior"],
                "label_status": "manual_confirmed",
                "notes": "",
            }
        self._dump(self.ground_truth_path, {"fixture_id": "stage6_real_camera_validation", "labels": labels})

    def _all_fingerprints(self):
        return {
            sample["session_id"]: session_fingerprint(os.path.join(self.sessions_dir, sample["session_id"]))
            for sample in self.samples
        }

    @staticmethod
    def _load(path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _dump(path, payload):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    @staticmethod
    def _write_bytes(path, payload):
        with open(path, "wb") as handle:
            handle.write(payload)


if __name__ == "__main__":
    unittest.main()
