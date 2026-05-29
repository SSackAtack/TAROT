import unittest

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
        self.assertAlmostEqual(result.cards[0]["x"], 15.0)
        self.assertAlmostEqual(result.cards[0]["y"], 20.0)
        self.assertEqual(result.cards[0]["confidence"], 0.91)


if __name__ == "__main__":
    unittest.main()
