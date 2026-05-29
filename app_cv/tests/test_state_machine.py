import unittest

from tarotvision.state_machine import CardStateMachine


class CardStateMachineTest(unittest.TestCase):
    def test_confirms_after_repeated_high_confidence_frames(self):
        fsm = CardStateMachine(confirm_frames=3, min_confidence=0.8)

        for _ in range(2):
            state = fsm.update("17_star", 0.91)
            self.assertEqual(state.phase, "candidate")

        state = fsm.update("17_star", 0.91)
        self.assertEqual(state.phase, "confirmed")

    def test_resets_when_card_identity_changes(self):
        fsm = CardStateMachine(confirm_frames=3, min_confidence=0.8)

        fsm.update("17_star", 0.91)
        state = fsm.update("18_moon", 0.91)

        self.assertEqual(state.phase, "candidate")
        self.assertEqual(state.card_id, "18_moon")

    def test_returns_empty_for_low_confidence(self):
        fsm = CardStateMachine(confirm_frames=3, min_confidence=0.8)

        state = fsm.update("17_star", 0.5)

        self.assertEqual(state.phase, "empty")
        self.assertIsNone(state.card_id)

    def test_resets_after_low_confidence_interruption(self):
        fsm = CardStateMachine(confirm_frames=3, min_confidence=0.8)

        fsm.update("17_star", 0.91)
        fsm.update("17_star", 0.91)
        # Przerwanie niskim confidence — reset
        fsm.update("17_star", 0.5)
        state = fsm.update("17_star", 0.91)

        self.assertEqual(state.phase, "candidate")
        self.assertEqual(state.frames, 1)

    def test_stays_confirmed_after_threshold(self):
        fsm = CardStateMachine(confirm_frames=2, min_confidence=0.8)

        fsm.update("00_fool", 0.95)
        fsm.update("00_fool", 0.95)
        state = fsm.update("00_fool", 0.90)

        self.assertEqual(state.phase, "confirmed")
        self.assertEqual(state.frames, 3)

    def test_initial_state_is_empty(self):
        fsm = CardStateMachine()

        self.assertEqual(fsm.state.phase, "empty")
        self.assertIsNone(fsm.state.card_id)
        self.assertEqual(fsm.state.frames, 0)


if __name__ == "__main__":
    unittest.main()
