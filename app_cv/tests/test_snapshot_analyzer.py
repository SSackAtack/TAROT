import unittest
import math

import numpy as np

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


if __name__ == "__main__":
    unittest.main()
