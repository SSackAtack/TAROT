from dataclasses import dataclass
import json


class ControlMessageError(ValueError):
    pass


@dataclass(frozen=True)
class ControlMessage:
    type: str
    param: str | None = None
    value: float | str | None = None
    name: str | None = None
    path: str | None = None


ALLOWED_TYPES = {
    "tuning_update",
    "tuning_rollback",
    "profile_save",
    "profile_apply",
    "camera_probe",
    "camera_set",
    "calibration_start",
    "calibration_cancel",
    "studio_set_recording_dir",
}


def parse_control_message(raw_message):
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError as exc:
        raise ControlMessageError("Invalid JSON") from exc

    message_type = payload.get("type")
    if message_type not in ALLOWED_TYPES:
        raise ControlMessageError(f"Unsupported message type: {message_type}")

    if message_type in {"tuning_update", "camera_set"}:
        if "param" not in payload or "value" not in payload:
            raise ControlMessageError(f"{message_type} requires param and value")
        return ControlMessage(
            type=message_type,
            param=str(payload["param"]),
            value=payload["value"],
        )

    if message_type in {"profile_save", "profile_apply"}:
        if "name" not in payload:
            raise ControlMessageError(f"{message_type} requires name")
        return ControlMessage(type=message_type, name=str(payload["name"]))

    if message_type == "studio_set_recording_dir":
        if "path" not in payload:
            raise ControlMessageError(f"{message_type} requires path")
        return ControlMessage(type=message_type, path=str(payload["path"]))

    return ControlMessage(type=message_type)
