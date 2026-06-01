from copy import deepcopy
from dataclasses import dataclass


class ParameterValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TunableParameter:
    name: str
    default: float
    minimum: float
    maximum: float
    live_safe: bool


PARAMETERS = {
    "SNAPSHOT_SETTLE_SECONDS": TunableParameter("SNAPSHOT_SETTLE_SECONDS", 0.5, 0.1, 2.5, True),
    "MOTION_CHANGED_RATIO": TunableParameter("MOTION_CHANGED_RATIO", 0.02, 0.005, 0.10, True),
    "MIN_MATCH_COUNT": TunableParameter("MIN_MATCH_COUNT", 12.0, 8.0, 40.0, False),
    "RATIO_THRESH": TunableParameter("RATIO_THRESH", 0.79, 0.50, 0.95, False),
    "MIN_INLIER_RATIO": TunableParameter("MIN_INLIER_RATIO", 0.25, 0.10, 0.80, False),
    "WORKSPACE_INFLATE_PERCENT": TunableParameter("WORKSPACE_INFLATE_PERCENT", 0.0, -10.0, 30.0, True),
    "CARD_DETECT_MAX_CANDIDATES": TunableParameter("CARD_DETECT_MAX_CANDIDATES", 10.0, 1.0, 30.0, True),
    "CARD_DETECT_MIN_AREA_RATIO": TunableParameter("CARD_DETECT_MIN_AREA_RATIO", 0.001, 0.0001, 0.02, True),
}


class RuntimeConfig:
    def __init__(self):
        self.values = {name: param.default for name, param in PARAMETERS.items()}

    def update(self, name, value):
        if name not in PARAMETERS:
            raise ParameterValidationError(f"Unknown parameter: {name}")
        param = PARAMETERS[name]
        numeric_value = float(value)
        if numeric_value < param.minimum or numeric_value > param.maximum:
            raise ParameterValidationError(
                f"{name} must be between {param.minimum} and {param.maximum}"
            )
        self.values[name] = numeric_value

    def snapshot(self):
        return deepcopy(self.values)

    def rollback(self, snapshot):
        for name, value in snapshot.items():
            self.update(name, value)

    def metadata(self):
        return {
            name: {
                "default": param.default,
                "minimum": param.minimum,
                "maximum": param.maximum,
                "live_safe": param.live_safe,
            }
            for name, param in PARAMETERS.items()
        }


class RuntimeConfigSession:
    def __init__(self, config=None):
        self.config = config or RuntimeConfig()
        self.stable_snapshot = self.config.snapshot()
        self.pending_changes = {}

    def update(self, name, value):
        self.config.update(name, value)
        if PARAMETERS[name].live_safe:
            self.pending_changes.pop(name, None)
            return True
        self.pending_changes[name] = self.config.values[name]
        return False

    def rollback(self):
        self.config.rollback(self.stable_snapshot)
        self.pending_changes.clear()

    def commit_stable(self):
        self.stable_snapshot = self.config.snapshot()
        self.pending_changes.clear()
