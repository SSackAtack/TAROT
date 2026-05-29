import unittest

from tarotvision.snapshot_gate import SnapshotGate, SnapshotGateConfig


class SnapshotGateTest(unittest.TestCase):
    def test_starts_holding_last_good(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        self.assertEqual(gate.state, "holding_last_good")
        self.assertEqual(gate.stable_for_ms, 0)

    def test_motion_enters_settling_without_requesting_analysis(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        decision = gate.update(now_ms=1000, motion_detected=True, changed_ratio=0.20)

        self.assertEqual(decision.state, "settling")
        self.assertFalse(decision.should_sample)
        self.assertFalse(decision.should_analyze)

    def test_requests_sampling_after_three_seconds_of_quiet(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        gate.update(now_ms=1000, motion_detected=True, changed_ratio=0.20)
        gate.update(now_ms=2000, motion_detected=False, changed_ratio=0.001)
        gate.update(now_ms=3500, motion_detected=False, changed_ratio=0.001)
        decision = gate.update(now_ms=5000, motion_detected=False, changed_ratio=0.001)

        self.assertEqual(decision.state, "sampling_snapshots")
        self.assertTrue(decision.should_sample)
        self.assertEqual(decision.stable_for_ms, 3000)

    def test_new_motion_resets_stable_timer(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        gate.update(now_ms=1000, motion_detected=True, changed_ratio=0.20)
        gate.update(now_ms=2500, motion_detected=False, changed_ratio=0.001)
        gate.update(now_ms=3000, motion_detected=True, changed_ratio=0.15)
        decision = gate.update(now_ms=5000, motion_detected=False, changed_ratio=0.001)

        self.assertEqual(decision.state, "settling")
        self.assertFalse(decision.should_sample)
        self.assertEqual(decision.stable_for_ms, 2000)

    def test_publish_returns_to_holding_last_good(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        gate.mark_published(layout_id=4, now_ms=6000)

        self.assertEqual(gate.state, "holding_last_good")
        self.assertEqual(gate.last_published_layout_id, 4)


if __name__ == "__main__":
    unittest.main()
