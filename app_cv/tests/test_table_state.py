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


if __name__ == "__main__":
    unittest.main()
