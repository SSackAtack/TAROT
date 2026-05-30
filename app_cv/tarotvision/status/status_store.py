# -*- coding: utf-8 -*-
"""
Moduł zarządzania współdzielonym stanem (StatusStore) aplikacji TarotVision.
"""
import copy
import threading

class StatusStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = {
            "schema_version": 1,
            "detected": False,
            "cards": [],
            "metrics": {},
            "runtime": {},
            "operator": {
                "enabled": True,
                "active_profile": "default",
                "parameters": {},
                "parameter_metadata": {},
                "pending_changes": {},
                "supported_camera_controls": {},
                "calibration": {"state": "idle", "last_score": None},
                "warnings": [],
            },
            "studio": {
                "recording_state": "idle",
                "recording_id": None,
                "elapsed_ms": 0,
                "dropped_frames": 0,
                "audio_peak_db": None,
                "director_scene": "table"
            }
        }

    def get_status(self):
        """Zwraca głęboką kopię obecnego statusu w bezpieczny dla wątków sposób."""
        with self._lock:
            return copy.deepcopy(self._status)

    def update_cv_state(self, cards, metrics, runtime, operator, layout=None, warnings=None):
        """Aktualizuje stan analizy CV."""
        with self._lock:
            self._status["detected"] = len(cards) > 0
            self._status["cards"] = copy.deepcopy(cards)
            self._status["metrics"] = copy.deepcopy(metrics)
            self._status["runtime"] = copy.deepcopy(runtime)
            self._status["operator"] = copy.deepcopy(operator)
            if layout is not None:
                self._status["layout"] = copy.deepcopy(layout)
            if warnings is not None:
                self._status["warnings"] = copy.deepcopy(warnings)

    def update_studio_state(self, recording_state=None, recording_id=None, elapsed_ms=None, dropped_frames=None, audio_peak_db=None, director_scene=None):
        """Aktualizuje stan nagrywania w studio nagrań."""
        with self._lock:
            if recording_state is not None:
                self._status["studio"]["recording_state"] = recording_state
            if recording_id is not None:
                self._status["studio"]["recording_id"] = recording_id
            if elapsed_ms is not None:
                self._status["studio"]["elapsed_ms"] = elapsed_ms
            if dropped_frames is not None:
                self._status["studio"]["dropped_frames"] = dropped_frames
            if audio_peak_db is not None:
                self._status["studio"]["audio_peak_db"] = audio_peak_db
            if director_scene is not None:
                self._status["studio"]["director_scene"] = director_scene

    def set_calibration_state(self, state, last_score):
        """Aktualizuje stan kalibracji operatora."""
        with self._lock:
            self._status["operator"]["calibration"]["state"] = state
            self._status["operator"]["calibration"]["last_score"] = last_score

    def set_parameter_metadata(self, metadata):
        """Ustawia metadane parametrów operatora."""
        with self._lock:
            self._status["operator"]["parameter_metadata"] = metadata

    def set_active_profile(self, profile):
        """Ustawia aktywny profil operatora."""
        with self._lock:
            self._status["operator"]["active_profile"] = profile

    def set_supported_camera_controls(self, controls):
        """Ustawia obsługiwane kontrolki kamery operatora."""
        with self._lock:
            self._status["operator"]["supported_camera_controls"] = controls

    @property
    def lock(self):
        """Zwraca wewnętrzny lock w celach kompatybilności wstecznej dla wątków orkiestratora."""
        return self._lock
