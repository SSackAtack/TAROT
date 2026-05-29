from dataclasses import dataclass


@dataclass(frozen=True)
class CameraControlProbe:
    supported: bool
    requested_value: float
    readback_value: float


def probe_camera_control(capture, prop_id, test_value):
    before = float(capture.get(prop_id))
    set_ok = bool(capture.set(prop_id, float(test_value)))
    readback = float(capture.get(prop_id))
    if set_ok:
        capture.set(prop_id, before)
    supported = set_ok and readback != before
    return CameraControlProbe(
        supported=supported,
        requested_value=float(test_value),
        readback_value=readback,
    )
