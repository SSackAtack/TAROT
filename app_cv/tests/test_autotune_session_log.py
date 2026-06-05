import json
import os
import tempfile
import unittest

from tarotvision.autotune_session import AutotuneSession
from tarotvision.autotune_session_log import AutotuneSessionLog


class AutotuneSessionLogTest(unittest.TestCase):
    def test_writes_session_snapshot_to_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = AutotuneSession(required_scenarios=("empty",), samples_per_scenario=1)
            session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})
            logger = AutotuneSessionLog(tmpdir)

            path = logger.write_event(
                event="stage_completed",
                session=session,
                active_decks=["gilded"],
                runtime_parameters={"CARD_DETECT_MIN_AREA_RATIO": 0.001},
            )

            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as log_file:
                payload = json.load(log_file)

            self.assertEqual(payload["event"], "stage_completed")
            self.assertEqual(payload["active_decks"], ["gilded"])
            self.assertEqual(payload["status"]["stage_result"]["state"], "PASS")
            self.assertEqual(payload["samples"]["empty"][0]["candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
