import unittest

from tarotvision.runtime_config import RuntimeConfig, RuntimeConfigSession, ParameterValidationError


class RuntimeConfigTest(unittest.TestCase):
    def test_updates_safe_parameter_in_range(self):
        config = RuntimeConfig()

        config.update("SNAPSHOT_SETTLE_SECONDS", 1.5)

        self.assertEqual(config.values["SNAPSHOT_SETTLE_SECONDS"], 1.5)

    def test_rejects_value_outside_range(self):
        config = RuntimeConfig()

        with self.assertRaises(ParameterValidationError):
            config.update("MOTION_CHANGED_RATIO", 1.5)

    def test_snapshot_and_rollback(self):
        config = RuntimeConfig()
        snapshot = config.snapshot()
        config.update("SNAPSHOT_SETTLE_SECONDS", 2.0)

        config.rollback(snapshot)

        self.assertEqual(config.values["SNAPSHOT_SETTLE_SECONDS"], 0.5)

    def test_exports_public_parameter_metadata(self):
        config = RuntimeConfig()

        metadata = config.metadata()

        self.assertTrue(metadata["SNAPSHOT_SETTLE_SECONDS"]["live_safe"])
        self.assertEqual(metadata["MOTION_CHANGED_RATIO"]["minimum"], 0.005)

    def test_live_update_does_not_move_rollback_target(self):
        session = RuntimeConfigSession()

        session.update("SNAPSHOT_SETTLE_SECONDS", 1.2)
        session.rollback()

        self.assertEqual(session.config.values["SNAPSHOT_SETTLE_SECONDS"], 0.5)

    def test_commit_stable_moves_rollback_target(self):
        session = RuntimeConfigSession()
        session.update("SNAPSHOT_SETTLE_SECONDS", 1.0)
        session.commit_stable()
        session.update("SNAPSHOT_SETTLE_SECONDS", 2.0)

        session.rollback()

        self.assertEqual(session.config.values["SNAPSHOT_SETTLE_SECONDS"], 1.0)


if __name__ == "__main__":
    unittest.main()
