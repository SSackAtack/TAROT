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
    "LOCK_DEAD_ZONE_POS": TunableParameter("LOCK_DEAD_ZONE_POS", 3.0, 1.5, 6.0, True),
    "LOCK_DEAD_ZONE_ANGLE": TunableParameter("LOCK_DEAD_ZONE_ANGLE", 0.5, 0.1, 1.2, True),
    "TRACKING_IOU_THRESHOLD": TunableParameter("TRACKING_IOU_THRESHOLD", 0.35, 0.1, 0.8, True),
    "REVERIFY_INTERVAL_FRAMES": TunableParameter("REVERIFY_INTERVAL_FRAMES", 180.0, 30.0, 600.0, True),
    "BOOST_AFTER_LAYOUT_CHANGE_FRAMES": TunableParameter("BOOST_AFTER_LAYOUT_CHANGE_FRAMES", 12.0, 0.0, 60.0, True),
    "EMA_ALPHA": TunableParameter("EMA_ALPHA", 0.4, 0.05, 1.0, False),
    "MIN_MATCH_COUNT": TunableParameter("MIN_MATCH_COUNT", 14.0, 8.0, 60.0, False),
    "RATIO_THRESH": TunableParameter("RATIO_THRESH", 0.75, 0.6, 0.95, False),
    "MIN_INLIER_RATIO": TunableParameter("MIN_INLIER_RATIO", 0.18, 0.1, 0.8, False),
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
