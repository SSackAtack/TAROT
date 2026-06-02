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
    mode: str | None = None
    markers: list | None = None
    active_decks: list | None = None
    scenario: str | None = None


ALLOWED_TYPES = {
    "tuning_update",
    "tuning_rollback",
    "profile_save",
    "profile_apply",
    "camera_probe",
    "camera_set",
    "calibration_start",
    "calibration_cancel",
    "autotune_start",
    "autotune_apply",
    "autotune_save",
    "autotune_cancel",
    "background_capture",
    "background_clear",
    "studio_set_recording_dir",
    "studio_start_recording",
    "studio_stop_recording",
    "studio_update_recording_status",
    "studio_set_director_scene",
    "studio_set_audio_volume",
    "studio_set_audio_mute",
    "studio_update_audio_peak",
    "studio_set_director_mode",
    "studio_save_timeline",
    "studio_set_active_decks",
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

    if message_type == "autotune_start":
        scenario = str(payload.get("scenario", "three_cards"))
        if scenario not in {"empty", "one_card", "three_cards"}:
            raise ControlMessageError(f"Invalid autotune scenario: {scenario}")
        return ControlMessage(type=message_type, scenario=scenario)

    if message_type in {"autotune_apply", "autotune_cancel"}:
        return ControlMessage(type=message_type)

    if message_type == "autotune_save":
        if "name" not in payload:
            raise ControlMessageError("autotune_save requires name")
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
        scene = str(payload["scene"])
        if scene not in {"table", "wow", "portrait_pip", "title_card"}:
            raise ControlMessageError(f"Invalid director scene: {scene}")
        return ControlMessage(type=message_type, scene=scene)

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

    if message_type == "studio_set_director_mode":
        if "mode" not in payload:
            raise ControlMessageError(f"{message_type} requires mode")
        mode = str(payload["mode"])
        if mode not in {"manual", "auto"}:
            raise ControlMessageError(f"Invalid director mode: {mode}")
        return ControlMessage(type=message_type, mode=mode)

    if message_type == "studio_save_timeline":
        if "recording_id" not in payload or "markers" not in payload:
            raise ControlMessageError(f"{message_type} requires recording_id and markers")
        rec_id = str(payload["recording_id"])
        markers = payload["markers"]
        if not isinstance(markers, list):
            raise ControlMessageError("markers must be a list")
            
        if len(markers) > 500:
            raise ControlMessageError(f"Too many timeline markers: {len(markers)} (max 500)")
            
        allowed_marker_types = {
            "recording_started",
            "scene_changed",
            "card_revealed",
            "operator_marker",
            "recording_stopped"
        }
        
        for idx, marker in enumerate(markers):
            if not isinstance(marker, dict):
                raise ControlMessageError(f"Marker at index {idx} must be a dict")
            if "timestamp_ms" not in marker:
                raise ControlMessageError(f"Marker at index {idx} is missing timestamp_ms")
            if "type" not in marker:
                raise ControlMessageError(f"Marker at index {idx} is missing type")
                
            t_ms = marker["timestamp_ms"]
            if not isinstance(t_ms, int) or isinstance(t_ms, bool):
                raise ControlMessageError(f"Marker at index {idx} timestamp_ms must be an integer, got: {type(t_ms)}")
            if t_ms < 0:
                raise ControlMessageError(f"Marker at index {idx} timestamp_ms must be non-negative, got: {t_ms}")
                
            m_type = marker["type"]
            if not isinstance(m_type, str):
                raise ControlMessageError(f"Marker at index {idx} type must be a string")
            if m_type not in allowed_marker_types:
                raise ControlMessageError(f"Marker at index {idx} has invalid type: {m_type}")
                
            for k, v in marker.items():
                if k in {"timestamp_ms", "type"}:
                    continue
                if v is not None and not isinstance(v, (str, int, float, bool)):
                    raise ControlMessageError(
                        f"Marker at index {idx} key '{k}' has invalid value type: {type(v)}. "
                        "Only string, int, float, bool, or null are allowed."
                    )
                    
        return ControlMessage(type=message_type, recording_id=rec_id, markers=markers)

    if message_type == "studio_set_active_decks":
        if "active_decks" not in payload:
            raise ControlMessageError(f"{message_type} requires active_decks")
        decks = payload["active_decks"]
        if not isinstance(decks, list):
            raise ControlMessageError("active_decks must be a list")
        if not (1 <= len(decks) <= 3):
            raise ControlMessageError(f"active_decks list length must be between 1 and 3, got {len(decks)}")
        for d in decks:
            if not isinstance(d, str):
                raise ControlMessageError("active_decks elements must be strings")
        return ControlMessage(type=message_type, active_decks=decks)

    return ControlMessage(type=message_type)

