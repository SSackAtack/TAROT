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


if __name__ == "__main__":
    unittest.main()
