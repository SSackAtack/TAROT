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
    recording_id: str | None = None
    recording_state: str | None = None
    elapsed_ms: int | None = None
    dropped_frames: int | None = None
    scene: str | None = None
    channel: str | None = None
    volume: float | None = None
    muted: bool | None = None
    peak_db: float | None = None


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
    "studio_start_recording",
    "studio_stop_recording",
    "studio_update_recording_status",
    "studio_set_director_scene",
    "studio_set_audio_volume",
    "studio_set_audio_mute",
    "studio_update_audio_peak",
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

    if message_type == "studio_start_recording":
        if "recording_id" not in payload:
            raise ControlMessageError(f"{message_type} requires recording_id")
        return ControlMessage(type=message_type, recording_id=str(payload["recording_id"]))

    if message_type == "studio_update_recording_status":
        for field in ["recording_id", "recording_state", "elapsed_ms", "dropped_frames"]:
            if field not in payload:
                raise ControlMessageError(f"{message_type} requires {field}")
        return ControlMessage(
            type=message_type,
            recording_id=str(payload["recording_id"]),
            recording_state=str(payload["recording_state"]),
            elapsed_ms=int(payload["elapsed_ms"]),
            dropped_frames=int(payload["dropped_frames"])
        )

    if message_type == "studio_set_director_scene":
        if "scene" not in payload:
            raise ControlMessageError(f"{message_type} requires scene")
        return ControlMessage(type=message_type, scene=str(payload["scene"]))

    if message_type == "studio_set_audio_volume":
        if "channel" not in payload or "volume" not in payload:
            raise ControlMessageError(f"{message_type} requires channel and volume")
        ch = str(payload["channel"])
        if ch not in {"mic", "bgm", "sfx", "master"}:
            raise ControlMessageError(f"Invalid audio channel: {ch}")
        try:
            vol = float(payload["volume"])
        except (TypeError, ValueError) as exc:
            raise ControlMessageError(f"Invalid volume format: {payload['volume']}") from exc
        if not (0.0 <= vol <= 1.0):
            raise ControlMessageError(f"Volume out of range [0.0, 1.0]: {vol}")
        return ControlMessage(type=message_type, channel=ch, volume=vol)

    if message_type == "studio_set_audio_mute":
        if "channel" not in payload or "muted" not in payload:
            raise ControlMessageError(f"{message_type} requires channel and muted")
        ch = str(payload["channel"])
        if ch not in {"mic", "bgm", "sfx", "master"}:
            raise ControlMessageError(f"Invalid audio channel: {ch}")
        muted = payload["muted"]
        if not isinstance(muted, bool):
            raise ControlMessageError(f"Muted must be boolean: {muted}")
        return ControlMessage(type=message_type, channel=ch, muted=muted)

    if message_type == "studio_update_audio_peak":
        if "peak_db" not in payload:
            raise ControlMessageError(f"{message_type} requires peak_db")
        peak = payload["peak_db"]
        if peak is not None:
            try:
                peak = float(peak)
            except (TypeError, ValueError) as exc:
                raise ControlMessageError(f"Invalid peak_db format: {peak}") from exc
        return ControlMessage(type=message_type, peak_db=peak)

    return ControlMessage(type=message_type)
