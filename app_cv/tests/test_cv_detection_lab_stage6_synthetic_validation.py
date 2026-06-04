"""Tests for the isolated Stage 6 synthetic validation benchmark."""
import json
import os
import shutil
import tempfile
import unittest

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_identification_methods import ReferenceCard
from tools.cv_detection_lab.stage6_synthetic_dataset import (
    build_validation_samples,
    render_sample,
    samples_manifest,
    select_evenly_spaced,
)
from tools.cv_detection_lab.stage6_synthetic_validation_benchmark import (
    MATRIX_COLUMNS,
    run_validation,
)


def _card_image(index, deck_offset=0):
    image = np.full((330, 200, 3), (25 + deck_offset, 35, 30), dtype=np.uint8)
    color = ((index * 31 + deck_offset) % 220 + 25, (index * 47) % 220 + 25, (index * 59) % 220 + 25)
    cv2.rectangle(image, (5, 5), (194, 324), (235, 235, 235), 4)
    cv2.circle(image, (100, 120), 30 + index % 25, color, -1)
    cv2.putText(image, f"{index:02d}", (65, 270), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (250, 250, 250), 3)
    return image


def _references(deck, count, deck_offset=0):
    return [
        ReferenceCard(f"{deck}_{index:02d}", f"{deck} {index:02d}", f"{deck}_{index:02d}.jpg", _card_image(index, deck_offset))
        for index in range(count)
    ]


class TestSyntheticDataset(unittest.TestCase):
    def test_even_selection_is_stable_and_covers_endpoints(self):
        items = list(range(78))

        selected = select_evenly_spaced(items, 24)

        self.assertEqual(len(selected), 24)
        self.assertEqual(selected[0], 0)
        self.assertEqual(selected[-1], 77)
        self.assertEqual(selected, select_evenly_spaced(items, 24))

    def test_dataset_is_deterministic_and_has_required_counts(self):
        gilded = _references("Gilded", 78)
        wrong = {"Magic": _references("Magic", 30, 25), "Marchetti": _references("Marchetti", 30, 50)}

        first = build_validation_samples(gilded, wrong, seed=6042026)
        second = build_validation_samples(gilded, wrong, seed=6042026)

        self.assertEqual(len([sample for sample in first if sample.is_known]), 168)
        self.assertEqual(len([sample for sample in first if not sample.is_known]), 24)
        self.assertEqual(samples_manifest(first), samples_manifest(second))
        self.assertEqual(len({sample.sample_id for sample in first}), 192)

    def test_manifest_records_source_category_orientation_and_parameters(self):
        samples = build_validation_samples(
            _references("Gilded", 78),
            {"Magic": _references("Magic", 30, 25), "Marchetti": _references("Marchetti", 30, 50)},
            seed=6042026,
        )

        item = samples_manifest(samples)[0]

        for key in ["sample_id", "source_deck", "source_card_id", "category", "orientation", "transform_parameters"]:
            self.assertIn(key, item)

    def test_reversed_sample_is_rotated_180_degrees(self):
        samples = build_validation_samples(
            _references("Gilded", 78),
            {"Magic": _references("Magic", 30, 25), "Marchetti": _references("Marchetti", 30, 50)},
            seed=6042026,
        )
        reversed_sample = next(sample for sample in samples if sample.category == "reversed_clean")

        rendered = render_sample(reversed_sample)

        self.assertTrue(np.array_equal(rendered, cv2.rotate(reversed_sample.source_image, cv2.ROTATE_180)))


class TestSyntheticValidationBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="stage6_synthetic_validation_")
        self.references = _references("Gilded", 78)
        all_samples = build_validation_samples(
            self.references,
            {"Magic": _references("Magic", 30, 25), "Marchetti": _references("Marchetti", 30, 50)},
            seed=6042026,
        )
        known_by_category = {sample.category: sample for sample in all_samples if sample.is_known}
        wrong = [sample for sample in all_samples if not sample.is_known][:2]
        self.samples = [
            known_by_category["upright_clean"],
            known_by_category["reversed_clean"],
            known_by_category["yellow_combined"],
            *wrong,
        ]

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_runner_uses_same_samples_and_reports_granular_metrics(self):
        summary = run_validation(
            self.samples,
            self.references,
            self.tmpdir,
            methods=["orb_bfmatcher_ratio_test", "akaze_bfmatcher"],
            offline_accept_score_threshold=0.08,
            warmup_runs=0,
        )

        self.assertEqual(len(summary["rows"]), len(self.samples) * 2)
        self.assertEqual(
            {row["sample_id"] for row in summary["rows"] if row["method"] == "orb_bfmatcher_ratio_test"},
            {row["sample_id"] for row in summary["rows"] if row["method"] == "akaze_bfmatcher"},
        )
        self.assertEqual(summary["offline_accept_score_threshold"], 0.08)
        self.assertEqual(summary["runtime_measurement"], "local_proxy")
        self.assertTrue(summary["method_summaries"])
        self.assertTrue(summary["category_orientation_summaries"])
        for key in ["wrong_deck_false_accept_rate", "mean_runtime_ms", "p50_runtime_ms", "p95_runtime_ms"]:
            self.assertIn(key, summary["method_summaries"][0])

    def test_matrix_and_reports_include_required_audit_fields(self):
        run_validation(
            self.samples,
            self.references,
            self.tmpdir,
            methods=["orb_bfmatcher_ratio_test"],
            offline_accept_score_threshold=0.08,
            warmup_runs=0,
        )

        for column in [
            "method", "sample_id", "source_deck", "source_card_id", "is_known",
            "category", "orientation", "predicted_card_id", "top1_correct",
            "top3_contains_expected", "confidence_score", "confidence_gap",
            "offline_accepted", "false_accept", "runtime_ms",
        ]:
            self.assertIn(column, MATRIX_COLUMNS)
        for filename in ["manifest.json", "matrix.csv", "report.json", "report.md"]:
            self.assertTrue(os.path.isfile(os.path.join(self.tmpdir, filename)))
        for filename in ["upright_debug_sheet.png", "reversed_debug_sheet.png", "yellow_combined_debug_sheet.png", "wrong_deck_debug_sheet.png"]:
            self.assertTrue(os.path.isfile(os.path.join(self.tmpdir, "debug", filename)))
        with open(os.path.join(self.tmpdir, "report.md"), "r", encoding="utf-8") as handle:
            report = handle.read()
        self.assertIn("local proxy, not a direct HP EliteBook 830 G6 measurement", report)
        self.assertIn("validation-only and is not approved for runtime", report)
        self.assertFalse(os.path.isdir(os.path.join(self.tmpdir, "samples")))


if __name__ == "__main__":
    unittest.main()
