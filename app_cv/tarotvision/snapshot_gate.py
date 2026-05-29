from dataclasses import dataclass


@dataclass(frozen=True)
class SnapshotGateConfig:
    settle_seconds: float = 0.5
    sample_count: int = 3
    sample_interval_ms: int = 250

    @property
    def settle_ms(self):
        return int(self.settle_seconds * 1000)


@dataclass(frozen=True)
class SnapshotGateDecision:
    state: str
    should_sample: bool
    should_analyze: bool
    stable_for_ms: int
    changed_ratio: float


class SnapshotGate:
    def __init__(self, config=None):
        self.config = config or SnapshotGateConfig()
        self.state = "holding_last_good"
        self.motion_started_ms = None
        self.quiet_started_ms = None
        self.stable_for_ms = 0
        self.last_published_layout_id = None

    def update(self, now_ms, motion_detected, changed_ratio):
        if motion_detected:
            had_quiet_period = self.quiet_started_ms is not None
            self.state = "settling"
            self.motion_started_ms = now_ms
            self.quiet_started_ms = now_ms if had_quiet_period else None
            self.stable_for_ms = 0
            return self._decision(False, False, changed_ratio)

        if self.state == "settling":
            if self.quiet_started_ms is None:
                self.quiet_started_ms = now_ms
            self.stable_for_ms = now_ms - self.quiet_started_ms
            if self.stable_for_ms >= self.config.settle_ms:
                self.state = "sampling_snapshots"
                return self._decision(True, False, changed_ratio)

        return self._decision(False, False, changed_ratio)

    def mark_analyzing(self):
        self.state = "analyzing_snapshot"

    def mark_published(self, layout_id, now_ms):
        self.state = "holding_last_good"
        self.last_published_layout_id = layout_id
        self.motion_started_ms = None
        self.quiet_started_ms = None
        self.stable_for_ms = 0

    def mark_rejected(self):
        self.state = "holding_last_good"
        self.motion_started_ms = None
        self.quiet_started_ms = None
        self.stable_for_ms = 0

    def _decision(self, should_sample, should_analyze, changed_ratio):
        return SnapshotGateDecision(
            state=self.state,
            should_sample=should_sample,
            should_analyze=should_analyze,
            stable_for_ms=self.stable_for_ms,
            changed_ratio=changed_ratio,
        )
