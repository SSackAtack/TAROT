from dataclasses import dataclass


@dataclass(frozen=True)
class CameraControlProbe:
    supported: bool
    readback_value: float


def read_camera_control(capture, prop_id):
    readback = float(capture.get(prop_id))
    return CameraControlProbe(
        # Read-only probe intentionally does not infer support by setting values.
        # Some webcams switch focus/exposure modes when CAP_PROP_* is set.
        supported=False,
        readback_value=readback,
    )
