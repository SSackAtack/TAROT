import unittest

from tarotvision.table_state import TableState


class TableStateTest(unittest.TestCase):
    def test_available_cards_excludes_locked_cards(self):
        state = TableState(["00_fool", "01_magician", "02_priestess"])

        state.upsert_locked(
            card_id="00_fool",
            x=1.0,
            y=2.0,
            angle=0.1,
            confidence=0.92,
            frame_index=10,
        )

        self.assertEqual(state.available_card_ids, ["01_magician", "02_priestess"])

    def test_removed_card_returns_to_available_pool(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)

        state.remove_card("00_fool")

        self.assertEqual(state.available_card_ids, ["00_fool", "01_magician"])

    def test_clear_removes_all_locked_cards(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)
        state.upsert_locked("01_magician", 3.0, 4.0, 0.2, 0.88, 11)

        state.clear()

        self.assertEqual(state.cards, {})
        self.assertEqual(state.available_card_ids, ["00_fool", "01_magician"])

    def test_needs_reverify_does_not_return_card_to_pool(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)

        state.mark_needs_reverify("00_fool", "contour_drift")

        self.assertEqual(state.cards["00_fool"].phase, "needs_reverify")
        self.assertEqual(state.available_card_ids, ["01_magician"])

    def test_operator_correction_swaps_card_identity(self):
        state = TableState(["00_fool", "01_magician", "02_priestess"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)

        state.correct_card_id("00_fool", "02_priestess")

        self.assertNotIn("00_fool", state.cards)
        self.assertIn("02_priestess", state.cards)
        self.assertEqual(state.available_card_ids, ["00_fool", "01_magician"])

    def test_removed_roi_removes_intersecting_card_by_bbox(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked(
            "00_fool",
            1.0,
            2.0,
            0.1,
            0.92,
            10,
            bbox=(100, 100, 80, 120),
        )
        state.upsert_locked(
            "01_magician",
            -1.0,
            -2.0,
            0.0,
            0.88,
            11,
            bbox=(260, 100, 80, 120),
        )

        removed = state.remove_cards_intersecting_bbox((110, 110, 60, 90))

        self.assertEqual(removed, ["00_fool"])
        self.assertNotIn("00_fool", state.cards)
        self.assertIn("01_magician", state.cards)
        self.assertEqual(state.available_card_ids, ["00_fool"])

    def test_moved_roi_marks_intersecting_card_for_reverify(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked(
            "00_fool",
            1.0,
            2.0,
            0.1,
            0.92,
            10,
            bbox=(100, 100, 80, 120),
        )

        marked = state.mark_cards_intersecting_bbox_needs_reverify(
            (110, 110, 60, 90),
            reason="moved_or_replaced",
        )

        self.assertEqual(marked, ["00_fool"])
        self.assertEqual(state.cards["00_fool"].phase, "needs_reverify")
        self.assertEqual(state.cards["00_fool"].reverify_reason, "moved_or_replaced")
        self.assertEqual(state.available_card_ids, ["01_magician"])

    def test_non_intersecting_roi_does_not_remove_card(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked(
            "00_fool",
            1.0,
            2.0,
            0.1,
            0.92,
            10,
            bbox=(100, 100, 80, 120),
        )

        removed = state.remove_cards_intersecting_bbox((260, 100, 80, 120))

        self.assertEqual(removed, [])
        self.assertIn("00_fool", state.cards)

    def test_to_layout_cards_returns_payload_shape(self):
        state = TableState(["00_fool"])
        state.upsert_locked(
            "00_fool",
            1.0,
            2.0,
            0.1,
            0.92,
            10,
            bbox=(100, 100, 80, 120),
        )

        self.assertEqual(state.to_layout_cards(), [{
            "name": "00_fool",
            "x": 1.0,
            "y": 2.0,
            "angle": 0.1,
            "confidence": 0.92,
            "phase": "locked_tracking",
            "bbox": [100, 100, 80, 120],
        }])


if __name__ == "__main__":
    unittest.main()
