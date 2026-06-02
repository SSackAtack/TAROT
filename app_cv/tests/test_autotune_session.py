import unittest

from tarotvision.autotune_session import AutotuneSession


class AutotuneSessionTest(unittest.TestCase):
    def test_collects_required_scenarios_before_ready(self):
        session = AutotuneSession(
            required_scenarios=("empty", "one_card", "three_cards"),
            samples_per_scenario=1,
        )

        self.assertFalse(session.ready_to_score())
        session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})
        session.add_sample("one_card", {"candidate_count": 1, "accepted_count": 1})
        session.add_sample("three_cards", {"candidate_count": 3, "accepted_count": 2})

        self.assertTrue(session.ready_to_score())

    def test_rejects_unknown_scenario(self):
        session = AutotuneSession(required_scenarios=("empty",))

        with self.assertRaises(ValueError):
            session.add_sample("six_cards", {})

    def test_status_payload_is_operator_readable(self):
        session = AutotuneSession(
            required_scenarios=("empty", "one_card"),
            samples_per_scenario=2,
        )
        session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})

        status = session.status()

        self.assertEqual(status["state"], "collecting")
        self.assertEqual(status["progress"]["empty"], "1/2")
        self.assertEqual(status["progress"]["one_card"], "0/2")

    def test_empty_mat_passes_only_when_no_cards_are_seen(self):
        session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=2)

        session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})
        session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})

        status = session.status()
        self.assertEqual(status["stage_result"]["state"], "PASS")
        self.assertIn("pusta", status["stage_result"]["message"].lower())
        self.assertEqual(status["next_action"], "Przejdz do testu 1 karta.")

    def test_empty_mat_fails_when_false_positive_is_seen(self):
        session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=1)

        session.add_sample("empty", {"candidate_count": 1, "accepted_count": 0})

        status = session.status()
        self.assertEqual(status["stage_result"]["state"], "FAIL")
        self.assertIn("false positive", status["stage_result"]["message"].lower())
        self.assertEqual(status["next_action"], "Kliknij Skalibruj albo popraw swiatlo/mate.")

    def test_one_card_requires_one_accepted_card(self):
        session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=1)

        session.add_sample("one_card", {"candidate_count": 1, "accepted_count": 0})

        self.assertEqual(session.status()["stage_result"]["state"], "FAIL")

        session = AutotuneSession(required_scenarios=("one_card",), samples_per_scenario=1)
        session.add_sample("one_card", {"candidate_count": 1, "accepted_count": 1})

        self.assertEqual(session.status()["stage_result"]["state"], "PASS")

    def test_three_cards_requires_three_accepted_cards(self):
        session = AutotuneSession(required_scenarios=("three_cards",), samples_per_scenario=1)

        session.add_sample("three_cards", {"candidate_count": 3, "accepted_count": 2})

        status = session.status()
        self.assertEqual(status["stage_result"]["state"], "FAIL")
        self.assertIn("3 karty", status["stage_result"]["message"])


if __name__ == "__main__":
    unittest.main()
