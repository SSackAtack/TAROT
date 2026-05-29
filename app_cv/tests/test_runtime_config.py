import unittest

from tarotvision.runtime_config import RuntimeConfig, RuntimeConfigSession, ParameterValidationError


class RuntimeConfigTest(unittest.TestCase):
    def test_updates_safe_parameter_in_range(self):
        config = RuntimeConfig()

        config.update("LOCK_DEAD_ZONE_POS", 3.5)

        self.assertEqual(config.values["LOCK_DEAD_ZONE_POS"], 3.5)

    def test_rejects_value_outside_range(self):
        config = RuntimeConfig()

        with self.assertRaises(ParameterValidationError):
            config.update("TRACKING_IOU_THRESHOLD", 1.5)

    def test_snapshot_and_rollback(self):
        config = RuntimeConfig()
        snapshot = config.snapshot()
        config.update("LOCK_DEAD_ZONE_POS", 5.0)

        config.rollback(snapshot)

        self.assertEqual(config.values["LOCK_DEAD_ZONE_POS"], 3.0)

    def test_exports_public_parameter_metadata(self):
        config = RuntimeConfig()

        metadata = config.metadata()

        self.assertTrue(metadata["LOCK_DEAD_ZONE_POS"]["live_safe"])
        self.assertEqual(metadata["TRACKING_IOU_THRESHOLD"]["minimum"], 0.1)

    def test_live_update_does_not_move_rollback_target(self):
        session = RuntimeConfigSession()

        session.update("LOCK_DEAD_ZONE_POS", 5.19)
        session.rollback()

        self.assertEqual(session.config.values["LOCK_DEAD_ZONE_POS"], 3.0)

    def test_commit_stable_moves_rollback_target(self):
        session = RuntimeConfigSession()
        session.update("LOCK_DEAD_ZONE_POS", 4.0)
        session.commit_stable()
        session.update("LOCK_DEAD_ZONE_POS", 5.0)

        session.rollback()

        self.assertEqual(session.config.values["LOCK_DEAD_ZONE_POS"], 4.0)


if __name__ == "__main__":
    unittest.main()
