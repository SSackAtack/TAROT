# -*- coding: utf-8 -*-
"""
Moduł zarządzania współdzielonym stanem (StatusStore) aplikacji TarotVision.
"""
import copy
import threading
import os
import json
from tarotvision.messages import build_status_payload

_UNSET = object()


class StatusStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = build_status_payload(
            cards=[],
            metrics={},
            warnings=[],
            debug={},
            runtime={},
            operator={
                "enabled": True,
                "active_profile": "default",
                "parameters": {},
                "parameter_metadata": {},
                "pending_changes": {},
                "supported_camera_controls": {},
                "calibration": {"state": "idle", "last_score": None},
                "warnings": [],
            },
            table={},
            layout={},
            studio={
                "recording_state": "idle",
                "recording_id": None,
                "elapsed_ms": 0,
                "dropped_frames": 0,
                "audio_peak_db": None,
                "director_scene": "table",
                "director_mode": "manual"
            }
        )
        
        self._status["operator"]["active_decks"] = ["rider-waite-smith"]
        self._decks_cache = {}
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            manifest_path = os.path.join(base_dir, "app_ar", "public", "decks_manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                for deck in manifest_data.get("decks", []):
                    prefix = deck.get("prefix")
                    deck_id = deck.get("id")
                    if prefix and deck_id:
                        self._decks_cache[prefix] = deck_id
                        
            active_decks_path = os.path.join(base_dir, "app_ar", "public", "active_decks.json")
            if os.path.exists(active_decks_path):
                with open(active_decks_path, "r", encoding="utf-8") as f:
                    active_data = json.load(f)
                active_ids = active_data.get("active_decks", [])
                if isinstance(active_ids, list) and len(active_ids) > 0:
                    self._status["operator"]["active_decks"] = active_ids
        except Exception:
            pass


    def get_status(self):
        """Zwraca głęboką kopię obecnego statusu w bezpieczny dla wątków sposób."""
        with self._lock:
            return copy.deepcopy(self._status)

    def update_active_decks(self, active_decks):
        """Aktualizuje listę aktywnych talii w statusie w bezpieczny dla wątków sposób."""
        with self._lock:
            self._status["operator"]["active_decks"] = copy.deepcopy(active_decks)

    def _get_deck_id(self, card_name):
        """Dopasowuje prefiks karty do technicznego ID talii z manifestu z fallbackami ASCII."""
        for prefix, d_id in self._decks_cache.items():
            if card_name.startswith(prefix):
                return d_id
                
        # Rezerwowy fallback ASCII w przypadku braku manifestu
        if card_name.startswith("RWS"):
            return "rider-waite-smith"
        elif card_name.startswith("Zodiak"):
            return "zodiak"
        elif card_name.startswith("Magic"):
            return "magic"
        elif card_name.startswith("Gilded"):
            return "gilded"
        elif card_name.startswith("Marchetti"):
            return "marchetti"
        elif card_name.startswith("Boski"):
            return "boski"
        elif card_name.startswith("Światło") or card_name.startswith("Swiatlo"):
            return "swiatlo_i_cien"
            
        if "_" in card_name:
            return card_name.split("_")[0].lower()
        return "rider-waite-smith"

    def update_cv_state(self, cards, metrics, runtime, operator, layout=None, warnings=None):
        """Aktualizuje stan analizy CV, wzbogacając payload kart o deck_id i card_id."""
        enriched_cards = []
        for card in cards:
            if isinstance(card, dict):
                c_copy = copy.deepcopy(card)
                name = c_copy.get("name", "")
                c_copy["deck_id"] = self._get_deck_id(name)
                c_copy["card_id"] = name  # unikalny identyfikator techniczny
                enriched_cards.append(c_copy)
            else:
                enriched_cards.append(card)

        with self._lock:
            # Zachowaj active_decks z obecnego stanu przed nadpisaniem słownika operator
            old_active_decks = self._status["operator"].get("active_decks")

            self._status["detected"] = len(enriched_cards) > 0
            self._status["cards"] = enriched_cards
            self._status["metrics"] = copy.deepcopy(metrics)
            self._status["runtime"] = copy.deepcopy(runtime)
            
            new_operator = copy.deepcopy(operator)
            if ("active_decks" not in new_operator or not new_operator["active_decks"]) and old_active_decks is not None:
                new_operator["active_decks"] = old_active_decks
            self._status["operator"] = new_operator

            if layout is not None:
                self._status["layout"] = copy.deepcopy(layout)
            if warnings is not None:
                self._status["warnings"] = copy.deepcopy(warnings)

    def update_studio_state(self, recording_state=_UNSET, recording_id=_UNSET, elapsed_ms=_UNSET, dropped_frames=_UNSET, audio_peak_db=_UNSET, director_scene=_UNSET, recording_dir_status=_UNSET, audio_channels=_UNSET, director_mode=_UNSET):
        """Aktualizuje stan nagrywania w studio nagrań."""
        with self._lock:
            if recording_state is not _UNSET:
                self._status["studio"]["recording_state"] = recording_state
            if recording_id is not _UNSET:
                self._status["studio"]["recording_id"] = recording_id
            if elapsed_ms is not _UNSET:
                self._status["studio"]["elapsed_ms"] = elapsed_ms
            if dropped_frames is not _UNSET:
                self._status["studio"]["dropped_frames"] = dropped_frames
            if audio_peak_db is not _UNSET:
                self._status["studio"]["audio_peak_db"] = audio_peak_db
                self._status["studio"]["audio"]["peak_db"] = audio_peak_db
            if director_scene is not _UNSET:
                self._status["studio"]["director_scene"] = director_scene
            if director_mode is not _UNSET:
                self._status["studio"]["director_mode"] = director_mode
            if recording_dir_status is not _UNSET:
                self._status["studio"]["recording_dir_status"] = copy.deepcopy(recording_dir_status)
            if audio_channels is not _UNSET and audio_channels is not None:
                for ch, settings in audio_channels.items():
                    if ch in self._status["studio"]["audio"]["channels"]:
                        self._status["studio"]["audio"]["channels"][ch].update(settings)


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
