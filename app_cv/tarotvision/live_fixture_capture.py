from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import platform
import subprocess

import cv2
import numpy as np


METRICS_FIELDS = (
    "change_region_count",
    "change_added_count",
    "change_removed_count",
    "change_mask_ratio",
    "snapshot_quads_found",
    "snapshot_recognition_attempts",
    "snapshot_recognition_rejections",
    "snapshot_candidate_validation_rejections",
    "snapshot_detection_quads_final",
    "roi_count",
    "roi_with_quads_count",
    "roi_with_accepted_card_count",
    "accepted_cards_before_dedup",
    "accepted_cards_after_dedup",
    "roi_diagnostics",
)


@dataclass(frozen=True)
class FixtureCaptureResult:
    ok: bool
    path: str | None = None
    reason: str | None = None
    error: str | None = None


class LiveFixtureCapture:
    def __init__(
        self,
        log_dir,
        enabled=False,
        fixture_name=None,
        commit=None,
        branch=None,
        deck=None,
        notes="event-first live smoke fixture",
    ):
        self.log_dir = log_dir
        self.enabled = bool(enabled)
        self.fixture_id = fixture_name or _default_fixture_name()
        self.commit = commit or _git_value(["rev-parse", "--short", "HEAD"])
        self.branch = branch or _git_value(["branch", "--show-current"])
        self.deck = deck or os.environ.get("TAROTVISION_DECK", "unknown")
        self.notes = notes

    @classmethod
    def from_env(cls, log_dir, deck=None):
        return cls(
            log_dir=log_dir,
            enabled=os.environ.get("TAROTVISION_CAPTURE_LIVE_FIXTURES") == "1",
            fixture_name=os.environ.get("TAROTVISION_LIVE_FIXTURE_NAME"),
            deck=deck,
        )

    def save_snapshot(
        self,
        scenario,
        raw_frame,
        analysis_frame,
        metrics,
        payload,
        empty_reference=None,
        expected_cards_count=None,
    ):
        if not self.enabled:
            return FixtureCaptureResult(ok=False, reason="disabled")

        try:
            scenario_name = _safe_name(scenario or os.environ.get("TAROTVISION_LIVE_FIXTURE_SCENARIO") or "unknown")
            fixture_dir = os.path.join(self.log_dir, "live_fixtures", self.fixture_id)
            scenario_dir = os.path.join(fixture_dir, scenario_name)
            os.makedirs(scenario_dir, exist_ok=True)

            self._write_manifest(fixture_dir, scenario_name)
            image_suffix = _scenario_image_suffix(scenario_name)
            _write_png(os.path.join(scenario_dir, f"raw_frame_{image_suffix}.png"), raw_frame)
            _write_png(os.path.join(scenario_dir, f"analysis_frame_{image_suffix}.png"), analysis_frame)
            if empty_reference is not None:
                _write_png(os.path.join(scenario_dir, f"empty_reference_{image_suffix}.png"), empty_reference)

            safe_metrics = _metrics_payload(metrics or {})
            safe_payload = _status_payload(
                scenario_name,
                payload or {},
                metrics or {},
                expected_cards_count,
            )
            _write_json(os.path.join(scenario_dir, "metrics.json"), safe_metrics)
            _write_json(os.path.join(scenario_dir, "payload.json"), safe_payload)
            _write_json(
                os.path.join(scenario_dir, "roi_diagnostics.json"),
                (metrics or {}).get("roi_diagnostics", []),
            )
            return FixtureCaptureResult(ok=True, path=scenario_dir)
        except Exception as exc:
            return FixtureCaptureResult(ok=False, reason="write_error", error=str(exc))

    def _write_manifest(self, fixture_dir, scenario_name):
        manifest_path = os.path.join(fixture_dir, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as handle:
                manifest = json.load(handle)
        else:
            manifest = {
                "fixture_id": self.fixture_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "commit": self.commit or "unknown",
                "branch": self.branch or "unknown",
                "camera": os.environ.get("TAROTVISION_CAMERA_NAME", "AnkerWork C310"),
                "machine": os.environ.get("TAROTVISION_MACHINE_NAME", platform.node() or "unknown"),
                "deck": self.deck,
                "scenarios": [],
                "notes": self.notes,
            }
        scenarios = manifest.setdefault("scenarios", [])
        if scenario_name not in scenarios:
            scenarios.append(scenario_name)
        _write_json(manifest_path, manifest)


def _write_png(path, image):
    if image is None:
        raise ValueError(f"missing image for {path}")
    ok = cv2.imwrite(path, np.asarray(image))
    if not ok:
        raise OSError(f"failed to write image: {path}")


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_to_jsonable(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)


def _metrics_payload(metrics):
    return {field: metrics.get(field) for field in METRICS_FIELDS if field in metrics}


def _status_payload(scenario, payload, metrics, expected_cards_count):
    runtime = payload.get("runtime") if isinstance(payload.get("runtime"), dict) else {}
    table = runtime.get("table") if isinstance(runtime.get("table"), dict) else {}
    operator = payload.get("operator") if isinstance(payload.get("operator"), dict) else {}
    calibration = operator.get("calibration") if isinstance(operator.get("calibration"), dict) else {}
    autotune = calibration.get("autotune") if isinstance(calibration.get("autotune"), dict) else {}
    cards = payload.get("cards") or []
    return {
        "scenario": scenario,
        "cards": cards,
        "cards_len": len(cards),
        "detected": bool(payload.get("detected", len(cards) > 0)),
        "table_calibrated": bool(table.get("calibrated", False)),
        "marker_ids": table.get("marker_ids", []),
        "background_reference_active": bool(runtime.get("background_reference_active", False)),
        "empty_reference_status": autotune.get("empty_reference_status"),
        "background_reference_validation_warning": metrics.get("background_reference_validation_warning"),
        "expected_cards_count": expected_cards_count,
        "actual_cards_count": len(cards),
        "metrics": _metrics_payload(metrics),
    }


def _to_jsonable(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def _safe_name(value):
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(value))
    return safe.strip("_") or "unknown"


def _scenario_image_suffix(scenario_name):
    return {
        "empty": "0",
        "one_card": "1",
        "three_cards": "3",
    }.get(scenario_name, _safe_name(scenario_name))


def _default_fixture_name():
    return datetime.now().strftime("%Y%m%d_%H%M%S_event_first_live_fixture")


def _git_value(args):
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        value = result.stdout.strip()
        return value or "unknown"
    except Exception:
        return "unknown"
