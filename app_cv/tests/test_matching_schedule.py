import unittest

from tarotvision.matching_schedule import choose_cards_to_match, get_schedule_mode


class MatchingScheduleTest(unittest.TestCase):
    def test_checks_detecting_cards_and_refreshes_locked_on_interval(self):
        state = {
            "00_fool": {"stable_count": 8, "phase": "LOCKED"},
            "01_magician": {"stable_count": 2, "phase": "DETECTING"},
        }

        cards = choose_cards_to_match(
            all_card_names=["00_fool", "01_magician", "02_priestess"],
            debounce_state=state,
            inactive_index=0,
            frame_counter=9,
            locked_refresh_interval=10,
            inactive_per_frame=1,
        )

        self.assertEqual(cards.next_inactive_index, 0)
        self.assertEqual(cards.names, ["01_magician", "02_priestess"])

    def test_refreshes_locked_cards_on_schedule(self):
        state = {
            "00_fool": {"stable_count": 8, "phase": "LOCKED"},
            "01_magician": {"stable_count": 2, "phase": "DETECTING"},
        }

        cards = choose_cards_to_match(
            all_card_names=["00_fool", "01_magician", "02_priestess"],
            debounce_state=state,
            inactive_index=0,
            frame_counter=10,
            locked_refresh_interval=10,
            inactive_per_frame=1,
        )

        self.assertEqual(cards.names, ["00_fool", "01_magician", "02_priestess"])

    def test_schedule_mode_scans_more_when_empty(self):
        mode = get_schedule_mode(
            active_count=0,
            boost_frames_remaining=0,
            inactive_per_frame_empty=4,
            inactive_per_frame_active=1,
            inactive_per_frame_boost=6,
        )

        self.assertEqual(mode.name, "empty_scan")
        self.assertEqual(mode.inactive_per_frame, 4)

    def test_schedule_mode_boosts_when_layout_changed(self):
        mode = get_schedule_mode(
            active_count=5,
            boost_frames_remaining=12,
            inactive_per_frame_empty=4,
            inactive_per_frame_active=1,
            inactive_per_frame_boost=3,
        )

        self.assertEqual(mode.name, "boost_scan")
        self.assertEqual(mode.inactive_per_frame, 3)

    def test_schedule_mode_is_conservative_when_stable(self):
        mode = get_schedule_mode(
            active_count=5,
            boost_frames_remaining=0,
            inactive_per_frame_empty=4,
            inactive_per_frame_active=1,
            inactive_per_frame_boost=6,
        )

        self.assertEqual(mode.name, "steady_scan")
        self.assertEqual(mode.inactive_per_frame, 1)


if __name__ == "__main__":
    unittest.main()
