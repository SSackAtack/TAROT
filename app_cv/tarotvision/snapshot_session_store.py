from dataclasses import dataclass
import time

import numpy as np


@dataclass
class SnapshotFrame:
    image: np.ndarray
    timestamp_ms: int
    role: str


class SnapshotSessionStore:
    def __init__(self, clock_ms=None):
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self.session_active = False
        self.empty_reference_locked = False
        self.empty_reference = None
        self.previous_snapshot = None
        self.current_snapshot = None

    def start_session(self):
        self.session_active = True
        self.current_snapshot = None

    def end_session(self):
        self.session_active = False
        self.empty_reference_locked = False
        self.current_snapshot = None

    def capture_empty_reference(self, frame):
        if not self.session_active:
            raise RuntimeError("session must be active before empty reference capture")
        snapshot = self._snapshot(frame, "empty_reference")
        self.empty_reference = snapshot
        self.previous_snapshot = self._snapshot(frame, "previous_snapshot")
        self.current_snapshot = None
        self.empty_reference_locked = True

    def clear_empty_reference(self):
        if self.session_active and self.empty_reference_locked:
            raise RuntimeError("empty reference is locked during active session")
        self.empty_reference = None
        self.previous_snapshot = None
        self.current_snapshot = None
        self.empty_reference_locked = False

    def set_current_snapshot(self, frame):
        if not self.session_active:
            raise RuntimeError("session is not active")
        if self.empty_reference is None:
            raise RuntimeError("empty reference is required before current snapshot")
        self.current_snapshot = self._snapshot(frame, "current_snapshot")

    def commit_current_snapshot(self):
        if self.current_snapshot is None:
            raise RuntimeError("current snapshot is missing")
        self.previous_snapshot = self._snapshot(self.current_snapshot.image, "previous_snapshot")
        self.current_snapshot = None

    def discard_current_snapshot(self):
        self.current_snapshot = None

    def ready_for_diff(self):
        return (
            self.session_active
            and self.empty_reference is not None
            and self.previous_snapshot is not None
            and self.current_snapshot is not None
        )

    def _snapshot(self, frame, role):
        if frame is None:
            raise ValueError("snapshot frame cannot be None")
        return SnapshotFrame(
            image=np.asarray(frame).copy(),
            timestamp_ms=self._clock_ms(),
            role=role,
        )
