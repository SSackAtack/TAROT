import unittest
import math

import cv2
import numpy as np

from tarotvision.card_detection_profiles import MultiProfileDetectionResult
from tarotvision.recognition_debug import RecognitionDebug
from tarotvision.snapshot_analyzer import SnapshotAnalyzer


class SnapshotAnalyzerTest(unittest.TestCase):
    def test_returns_empty_layout_when_no_quads(self):
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [],
            crop_card=lambda frame, quad: None,
            recognize_crop=lambda crop: None,
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.cards, [])
        self.assertEqual(result.card_count, 0)
        self.assertEqual(result.diagnostics["quads_found"], 0)
        self.assertEqual(result.diagnostics["recognition_attempts"], 0)

    def test_converts_recognized_quads_to_layout_cards(self):
        quad = np.array([[[10, 10]], [[10, 30]], [[20, 30]], [[20, 10]]],
                        dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {
                "name": "17_star",
                "confidence": 0.91,
                "orientation": "upright",
            },
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.card_count, 1)
        self.assertEqual(result.diagnostics["quads_found"], 1)
        self.assertEqual(result.diagnostics["recognition_attempts"], 1)
        self.assertEqual(result.diagnostics["recognition_rejections"], 0)
        self.assertEqual(result.cards[0]["name"], "17_star")
        self.assertAlmostEqual(result.cards[0]["x"], -3.25)
        self.assertAlmostEqual(result.cards[0]["y"], 0.0)
        self.assertEqual(result.cards[0]["confidence"], 0.91)

    def test_maps_frame_center_to_scene_origin(self):
        quad = np.array([[[18, 18]], [[18, 22]], [[22, 22]], [[22, 18]]],
                        dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {"name": "17_star"},
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertAlmostEqual(result.cards[0]["x"], 0.0)
        self.assertAlmostEqual(result.cards[0]["y"], 0.0)

    def test_upright_portrait_card_reports_zero_angle(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {"name": "16_tower"},
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertAlmostEqual(result.cards[0]["angle"], 0.0)

    def test_reversed_recognition_rotates_layout_card_by_half_turn(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {
                "name": "15_devil",
                "orientation": "reversed",
            },
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertAlmostEqual(result.cards[0]["angle"], math.pi)
        self.assertEqual(result.cards[0]["orientation"], "reversed")

    def test_counts_recognition_rejections(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: None,
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.cards, [])
        self.assertEqual(result.card_count, 0)
        self.assertEqual(result.diagnostics["quads_found"], 1)
        self.assertEqual(result.diagnostics["recognition_attempts"], 1)
        self.assertEqual(result.diagnostics["recognition_rejections"], 1)

    def test_rejects_glare_like_candidate_before_recognition(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        crop = np.full((516, 300), 216, dtype=np.uint8)
        calls = []
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: crop,
            recognize_crop=lambda crop: calls.append(crop) or {
                "name": "forced_false_match",
                "confidence": 0.8,
            },
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.cards, [])
        self.assertEqual(calls, [])
        self.assertEqual(result.diagnostics["quads_found"], 1)
        self.assertEqual(result.diagnostics["recognition_attempts"], 0)
        self.assertEqual(result.diagnostics["recognition_rejections"], 0)
        self.assertEqual(result.diagnostics["candidate_validation_rejections"], 1)
        candidates = result.diagnostics["recognition_candidates"]
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0]["accepted"])
        self.assertIn(
            candidates[0]["reject_reason"],
            {"smooth_low_texture", "no_card_border_evidence"},
        )

    def test_records_per_candidate_recognition_debug(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        debug = RecognitionDebug(
            crop_keypoints=81,
            top_matches=[
                {"name": "Gilded_10", "score": 11.0, "match_count": 22, "inlier_ratio": 0.5},
                {"name": "Gilded_09", "score": 10.0, "match_count": 20, "inlier_ratio": 0.5},
            ],
            reject_reason="ambiguous_top_matches",
        )
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop_with_debug=lambda crop: (None, debug),
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.card_count, 0)
        self.assertEqual(result.diagnostics["recognition_rejections"], 1)
        candidates = result.diagnostics["recognition_candidates"]
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0]["accepted"])
        self.assertEqual(candidates[0]["reject_reason"], "ambiguous_top_matches")
        self.assertEqual(candidates[0]["crop_keypoints"], 81)
        self.assertEqual(candidates[0]["top_matches"][0]["name"], "Gilded_10")
        self.assertAlmostEqual(candidates[0]["score_margin"], 1.0)

    def test_aggregates_recognition_score_from_accepted_candidates(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        debug = RecognitionDebug(
            crop_keypoints=120,
            top_matches=[{"name": "Gilded_17", "score": 15.0, "match_count": 30, "inlier_ratio": 0.5}],
            reject_reason=None,
        )
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop_with_debug=lambda crop: ({
                "name": "Gilded_17",
                "confidence": 0.5,
                "orientation": "upright",
            }, debug),
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.card_count, 1)
        self.assertAlmostEqual(result.diagnostics["recognition_score"], 0.5)
        self.assertEqual(result.diagnostics["recognition_candidates"][0]["name"], "Gilded_17")

    def test_uses_injected_find_quads_without_debug_detector(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        calls = []
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: calls.append(frame.shape) or [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {"name": "17_star"},
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(calls, [(40, 40, 3)])
        self.assertEqual(result.card_count, 1)
        self.assertNotIn("detection", result.diagnostics)

    def test_uses_debug_detector_when_provided(self):
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        debug = {"profiles": [{"name": "test", "quads": 1}], "quads_final": 1}
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [],
            find_quads_with_debug=lambda frame: MultiProfileDetectionResult(
                quads=[quad],
                best_profile="test",
                debug=debug,
            ),
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {"name": "17_star"},
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.card_count, 1)
        self.assertIs(result.diagnostics["detection"], debug)

    def test_analyze_limits_detection_to_roi_hints(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.rectangle(frame, (20, 40), (80, 140), (255, 255, 255), -1)
        cv2.rectangle(frame, (190, 40), (250, 140), (255, 255, 255), -1)

        def find_quads(crop):
            return [np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32)]

        analyzer = SnapshotAnalyzer(
            find_quads=find_quads,
            recognize_crop=lambda crop: {"name": "Gilded_01", "confidence": 0.9},
            validate_candidate_crop=None,
        )

        result = analyzer.analyze(frame, roi_hints=[(180, 30, 90, 130)])

        self.assertEqual(result.card_count, 1)
        self.assertGreater(result.cards[0]["x"], 0)
        self.assertTrue(result.diagnostics["roi_limited"])
        self.assertEqual(result.diagnostics["roi_count"], 1)

    def test_analyze_reports_per_roi_recognition_diagnostics(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        quads_by_width = {
            80: [np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32)],
            90: [
                np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32),
                np.array([[15, 15], [45, 15], [45, 80], [15, 80]], dtype=np.float32),
            ],
        }
        recognitions = iter([
            {"name": "Gilded_01", "confidence": 0.9},
            None,
            {"name": "Gilded_02", "confidence": 0.8},
        ])

        analyzer = SnapshotAnalyzer(
            find_quads=lambda crop: quads_by_width[crop.shape[1]],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: next(recognitions),
            validate_candidate_crop=None,
        )

        result = analyzer.analyze(
            frame,
            roi_hints=[(0, 0, 80, 120), (100, 0, 90, 120)],
        )

        self.assertEqual(result.card_count, 2)
        self.assertEqual(result.diagnostics["roi_count"], 2)
        self.assertEqual(result.diagnostics["roi_with_quads_count"], 2)
        self.assertEqual(result.diagnostics["roi_with_accepted_card_count"], 2)
        self.assertEqual(result.diagnostics["accepted_cards_before_dedup"], 2)
        self.assertEqual(result.diagnostics["accepted_cards_after_dedup"], 2)
        roi_diagnostics = result.diagnostics["roi_diagnostics"]
        self.assertEqual(roi_diagnostics[0]["roi_index"], 0)
        self.assertEqual(roi_diagnostics[0]["roi_bbox"], [0, 0, 80, 120])
        self.assertEqual(roi_diagnostics[0]["roi_quads_found"], 1)
        self.assertEqual(roi_diagnostics[0]["roi_recognition_attempts"], 1)
        self.assertEqual(roi_diagnostics[0]["roi_accepted_cards"], 1)
        self.assertEqual(roi_diagnostics[1]["roi_index"], 1)
        self.assertEqual(roi_diagnostics[1]["roi_quads_found"], 2)
        self.assertEqual(roi_diagnostics[1]["roi_recognition_attempts"], 2)
        self.assertEqual(roi_diagnostics[1]["roi_recognition_rejections"], 1)
        self.assertEqual(roi_diagnostics[1]["roi_accepted_cards"], 1)
        self.assertEqual(roi_diagnostics[1]["roi_reject_reasons"], {"recognition_rejected": 1})

    def test_roi_crop_diagnostics_include_descriptor_rejection_context(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        debug = RecognitionDebug(
            crop_keypoints=3,
            top_matches=[],
            reject_reason="not_enough_crop_descriptors",
        )

        analyzer = SnapshotAnalyzer(
            find_quads=lambda crop: [np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32)],
            crop_card=lambda frame, quad: np.zeros((72, 48, 3), dtype=np.uint8),
            recognize_crop_with_debug=lambda crop: (None, debug),
            validate_candidate_crop=lambda crop: None,
        )

        result = analyzer.analyze(frame, roi_hints=[(30, 40, 80, 120)])

        crop_diagnostics = result.diagnostics["crop_diagnostics"]
        self.assertEqual(len(crop_diagnostics), 1)
        self.assertEqual(crop_diagnostics[0]["roi_index"], 0)
        self.assertEqual(crop_diagnostics[0]["candidate_index"], 1)
        self.assertEqual(crop_diagnostics[0]["crop_width"], 48)
        self.assertEqual(crop_diagnostics[0]["crop_height"], 72)
        self.assertEqual(crop_diagnostics[0]["crop_keypoints"], 3)
        self.assertEqual(crop_diagnostics[0]["descriptor_count"], 3)
        self.assertEqual(crop_diagnostics[0]["reject_reason"], "not_enough_crop_descriptors")
        self.assertEqual(crop_diagnostics[0]["recognition_attempt_result"], "rejected")
        roi_diagnostics = result.diagnostics["roi_diagnostics"]
        self.assertEqual(roi_diagnostics[0]["roi_candidate_diagnostics"][0]["candidate_index"], 1)

    def test_roi_crop_diagnostics_include_smooth_validation_context(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        smooth_crop = np.full((60, 40, 3), 216, dtype=np.uint8)
        calls = []

        analyzer = SnapshotAnalyzer(
            find_quads=lambda crop: [np.array([[8, 8], [44, 8], [44, 70], [8, 70]], dtype=np.float32)],
            crop_card=lambda frame, quad: smooth_crop,
            recognize_crop=lambda crop: calls.append(crop),
        )

        result = analyzer.analyze(frame, roi_hints=[(20, 30, 70, 100)])

        self.assertEqual(calls, [])
        crop_diagnostics = result.diagnostics["crop_diagnostics"]
        self.assertEqual(crop_diagnostics[0]["roi_index"], 0)
        self.assertEqual(crop_diagnostics[0]["crop_width"], 40)
        self.assertEqual(crop_diagnostics[0]["crop_height"], 60)
        self.assertEqual(crop_diagnostics[0]["reject_reason"], "smooth_low_texture")
        self.assertEqual(crop_diagnostics[0]["recognition_attempt_result"], "skipped_candidate_validation")
        self.assertFalse(crop_diagnostics[0]["candidate_validation"]["accepted"])
        self.assertEqual(crop_diagnostics[0]["candidate_validation"]["reject_reason"], "smooth_low_texture")

    def test_roi_crop_diagnostics_map_rejections_to_specific_roi(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        debug = RecognitionDebug(
            crop_keypoints=42,
            top_matches=[
                {"name": "Gilded_01", "score": 4.0, "match_count": 4, "inlier_ratio": 0.0},
            ],
            reject_reason="not_enough_good_matches",
        )

        def find_quads(crop):
            if crop.shape[1] == 50:
                return []
            return [np.array([[8, 8], [42, 8], [42, 68], [8, 68]], dtype=np.float32)]

        analyzer = SnapshotAnalyzer(
            find_quads=find_quads,
            crop_card=lambda frame, quad: np.zeros((80, 52, 3), dtype=np.uint8),
            recognize_crop_with_debug=lambda crop: (None, debug),
            validate_candidate_crop=lambda crop: None,
        )

        result = analyzer.analyze(
            frame,
            roi_hints=[(0, 0, 50, 100), (100, 0, 90, 120)],
        )

        crop_diagnostics = result.diagnostics["crop_diagnostics"]
        self.assertEqual(len(crop_diagnostics), 1)
        self.assertEqual(crop_diagnostics[0]["roi_index"], 1)
        self.assertEqual(crop_diagnostics[0]["reject_reason"], "not_enough_good_matches")
        self.assertEqual(crop_diagnostics[0]["top_matches"][0]["match_count"], 4)
        roi_diagnostics = result.diagnostics["roi_diagnostics"]
        self.assertEqual(roi_diagnostics[0]["roi_candidate_diagnostics"], [])
        self.assertEqual(roi_diagnostics[1]["roi_candidate_diagnostics"][0]["roi_index"], 1)

    def test_analyze_with_empty_roi_hints_does_not_fallback_to_global_detection(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        calls = []

        def find_quads(_frame):
            calls.append(_frame.shape)
            return [np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32)]

        analyzer = SnapshotAnalyzer(
            find_quads=find_quads,
            recognize_crop=lambda crop: {"name": "Gilded_01", "confidence": 0.9},
            validate_candidate_crop=None,
        )

        result = analyzer.analyze(frame, roi_hints=[])

        self.assertEqual(calls, [])
        self.assertEqual(result.card_count, 0)
        self.assertTrue(result.diagnostics["roi_limited"])
        self.assertEqual(result.diagnostics["roi_count"], 0)


if __name__ == "__main__":
    unittest.main()
