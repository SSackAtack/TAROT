import unittest

import numpy as np

from tarotvision.snapshot_session_store import SnapshotSessionStore


class SnapshotSessionStoreTest(unittest.TestCase):
    def frame(self, value):
        return np.full((20, 30, 3), value, dtype=np.uint8)

    def test_requires_empty_reference_before_current_snapshot(self):
        store = SnapshotSessionStore()

        with self.assertRaises(RuntimeError):
            store.set_current_snapshot(self.frame(10))

    def test_capture_empty_reference_locks_active_session(self):
        store = SnapshotSessionStore()
        empty = self.frame(5)

        store.start_session()
        store.capture_empty_reference(empty)

        self.assertTrue(store.session_active)
        self.assertTrue(store.empty_reference_locked)
        self.assertIsNotNone(store.empty_reference)
        self.assertIsNotNone(store.previous_snapshot)

    def test_cannot_clear_empty_reference_during_active_session(self):
        store = SnapshotSessionStore()
        store.start_session()
        store.capture_empty_reference(self.frame(5))

        with self.assertRaises(RuntimeError):
            store.clear_empty_reference()

    def test_commit_rotates_current_into_previous_and_drops_current(self):
        store = SnapshotSessionStore()
        store.start_session()
        store.capture_empty_reference(self.frame(5))
        current = self.frame(40)

        store.set_current_snapshot(current)
        store.commit_current_snapshot()

        self.assertIsNone(store.current_snapshot)
        self.assertTrue(np.array_equal(store.previous_snapshot.image, current))

    def test_discard_keeps_previous_snapshot(self):
        store = SnapshotSessionStore()
        store.start_session()
        empty = self.frame(5)
        store.capture_empty_reference(empty)
        previous_before = store.previous_snapshot.image.copy()

        store.set_current_snapshot(self.frame(80))
        store.discard_current_snapshot()

        self.assertIsNone(store.current_snapshot)
        self.assertTrue(np.array_equal(store.previous_snapshot.image, previous_before))

    def test_end_session_allows_reference_clear(self):
        store = SnapshotSessionStore()
        store.start_session()
        store.capture_empty_reference(self.frame(5))

        store.end_session()
        store.clear_empty_reference()

        self.assertFalse(store.session_active)
        self.assertFalse(store.empty_reference_locked)
        self.assertIsNone(store.empty_reference)


if __name__ == "__main__":
    unittest.main()
