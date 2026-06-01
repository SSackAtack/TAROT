# -*- coding: utf-8 -*-
import unittest
import threading
import time
from tarotvision.status.status_store import StatusStore

class TestStatusStore(unittest.TestCase):
    def setUp(self):
        self.store = StatusStore()

    def test_initial_state(self):
        status = self.store.get_status()
        self.assertEqual(status["schema_version"], 1)
        self.assertFalse(status["detected"])
        self.assertEqual(status["cards"], [])
        self.assertEqual(status["studio"]["recording_state"], "idle")
        self.assertEqual(status["studio"]["director_mode"], "manual")
        self.assertEqual(status["operator"]["calibration"]["state"], "idle")

    def test_deep_copy_safety(self):
        status = self.store.get_status()
        status["cards"].append("01_magician")
        status["studio"]["recording_state"] = "recording"
        
        # Pobieramy stan ponownie i upewniamy się, że modyfikacje zewnętrzne nie wpłynęły na store
        fresh_status = self.store.get_status()
        self.assertEqual(fresh_status["cards"], [])
        self.assertEqual(fresh_status["studio"]["recording_state"], "idle")

    def test_update_cv_state(self):
        cards = ["00_fool", "01_magician"]
        metrics = {"fps": 30.0}
        runtime = {"some_param": 1}
        operator = {"enabled": True, "active_profile": "test"}
        layout = {"foo": "bar"}
        warnings = ["warn1", "warn2"]
        
        self.store.update_cv_state(cards, metrics, runtime, operator, layout, warnings)
        
        status = self.store.get_status()
        self.assertTrue(status["detected"])
        self.assertEqual(status["cards"], cards)
        self.assertEqual(status["metrics"], metrics)
        self.assertEqual(status["runtime"], runtime)
        for key in operator:
            self.assertEqual(status["operator"][key], operator[key])
        self.assertIn("active_decks", status["operator"])
        self.assertEqual(status["layout"], layout)
        self.assertEqual(status["warnings"], warnings)

    def test_update_cv_state_defensive_copy(self):
        # Przekazujemy mutowalne obiekty
        cards = ["00_fool"]
        metrics = {"fps": 30.0}
        runtime = {"threshold": 120}
        operator = {"active_profile": "default"}
        layout = {"card": " Fool"}
        warnings = ["warning"]
        
        self.store.update_cv_state(cards, metrics, runtime, operator, layout, warnings)
        
        # Modyfikujemy obiekty po wywołaniu update_cv_state
        cards.append("01_magician")
        metrics["fps"] = 60.0
        runtime["threshold"] = 150
        operator["active_profile"] = "modified"
        layout["card"] = "Magician"
        warnings.append("another_warning")
        
        # Pobieramy stan i upewniamy się, że nie uległ zmianie
        status = self.store.get_status()
        self.assertEqual(status["cards"], ["00_fool"])
        self.assertEqual(status["metrics"], {"fps": 30.0})
        self.assertEqual(status["runtime"], {"threshold": 120})
        self.assertEqual(status["operator"]["active_profile"], "default")
        self.assertEqual(status["layout"], {"card": " Fool"})
        self.assertEqual(status["warnings"], ["warning"])

    def test_update_studio_state(self):
        dir_status = {"valid": True, "message": "Ready", "path": "/tmp/rec"}
        self.store.update_studio_state(
            recording_state="recording",
            recording_id="rec_123",
            elapsed_ms=1000,
            dropped_frames=2,
            audio_peak_db=-3.5,
            director_scene="wow",
            recording_dir_status=dir_status,
            director_mode="auto"
        )
        
        status = self.store.get_status()
        studio = status["studio"]
        self.assertEqual(studio["recording_state"], "recording")
        self.assertEqual(studio["recording_id"], "rec_123")
        self.assertEqual(studio["elapsed_ms"], 1000)
        self.assertEqual(studio["dropped_frames"], 2)
        self.assertEqual(studio["audio_peak_db"], -3.5)
        self.assertEqual(studio["director_scene"], "wow")
        self.assertEqual(studio["director_mode"], "auto")
        self.assertEqual(studio["recording_dir_status"], dir_status)

    def test_update_studio_state_audio(self):
        # Sprawdzamy stan domyślny
        status = self.store.get_status()
        self.assertEqual(status["studio"]["audio"]["channels"]["bgm"]["volume"], 0.5)
        self.assertFalse(status["studio"]["audio"]["channels"]["mic"]["muted"])
        self.assertIsNone(status["studio"]["audio"]["peak_db"])
        
        # Aktualizujemy parametry audio
        self.store.update_studio_state(
            audio_channels={"bgm": {"volume": 0.35}, "mic": {"muted": True}},
            audio_peak_db=-18.2
        )
        
        updated_status = self.store.get_status()
        studio = updated_status["studio"]
        self.assertEqual(studio["audio"]["channels"]["bgm"]["volume"], 0.35)
        self.assertTrue(studio["audio"]["channels"]["mic"]["muted"])
        self.assertEqual(studio["audio"]["peak_db"], -18.2)
        self.assertEqual(studio["audio_peak_db"], -18.2) # kompatybilność wsteczna

    def test_partial_studio_update(self):
        # Najpierw ustawiamy pełny stan
        self.store.update_studio_state(recording_state="recording", recording_id="rec_123")
        
        # Następnie aktualizujemy tylko jedno pole
        self.store.update_studio_state(elapsed_ms=5000)
        
        status = self.store.get_status()
        studio = status["studio"]
        self.assertEqual(studio["recording_state"], "recording")
        self.assertEqual(studio["recording_id"], "rec_123")
        self.assertEqual(studio["elapsed_ms"], 5000)

    def test_clear_recording_id_to_none(self):
        # Ustawiamy najpierw recording_id
        self.store.update_studio_state(recording_id="rec_123")
        self.assertEqual(self.store.get_status()["studio"]["recording_id"], "rec_123")
        
        # Czyścimy na None i upewniamy się, że zmiana została zastosowana
        self.store.update_studio_state(recording_id=None)
        self.assertIsNone(self.store.get_status()["studio"]["recording_id"])

    def test_setters(self):
        self.store.set_calibration_state("calibrating", 0.95)
        self.store.set_parameter_metadata({"param1": "meta"})
        self.store.set_active_profile("pro")
        self.store.set_supported_camera_controls({"brightness": [0, 100]})
        
        status = self.store.get_status()
        self.assertEqual(status["operator"]["calibration"]["state"], "calibrating")
        self.assertEqual(status["operator"]["calibration"]["last_score"], 0.95)
        self.assertEqual(status["operator"]["parameter_metadata"], {"param1": "meta"})
        self.assertEqual(status["operator"]["active_profile"], "pro")
        self.assertEqual(status["operator"]["supported_camera_controls"], {"brightness": [0, 100]})

    def test_thread_safety_stress(self):
        # Stress test zapisu i odczytu z wielu wątków jednocześnie
        num_threads = 10
        iterations = 100
        errors = []

        def worker(thread_idx):
            try:
                for i in range(iterations):
                    self.store.update_cv_state(
                        cards=[f"card_{thread_idx}_{i}"],
                        metrics={"iteration": i},
                        runtime={},
                        operator={}
                    )
                    status = self.store.get_status()
                    self.assertIsNotNone(status)
                    # Krótki sleep w celu przełączenia wątków
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = []
        for idx in range(num_threads):
            t = threading.Thread(target=worker, args=(idx,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread stress test errors: {errors}")

    def test_lock_property(self):
        # Upewniamy się, że property lock zwraca ten sam obiekt, co wewnętrzny Lock
        self.assertIsNotNone(self.store.lock)
        # Próba przejęcia locka
        acquired = self.store.lock.acquire(blocking=False)
        self.assertTrue(acquired)
        if acquired:
            self.store.lock.release()

    def test_get_status_returns_complete_v1_schema(self):
        # Weryfikacja kompletności wszystkich sekcji top-level schematu Payload v1
        status = self.store.get_status()
        required_keys = [
            "schema_version",
            "detected",
            "cards",
            "metrics",
            "warnings",
            "debug",
            "runtime",
            "operator",
            "table",
            "layout",
            "studio"
        ]
        for key in required_keys:
            self.assertIn(key, status, f"Brak klucza '{key}' w status payload")
        
        self.assertEqual(status["schema_version"], 1)

    def test_update_cv_state_preserves_active_decks(self):
        # 1. Ustawienie początkowych aktywnych talii
        initial_decks = ["magic", "zodiak"]
        self.store.update_active_decks(initial_decks)
        
        # Weryfikacja ustawienia
        status_before = self.store.get_status()
        self.assertEqual(status_before["operator"]["active_decks"], initial_decks)
        
        # 2. Wywołanie update_cv_state ze słownikiem operator, który NIE zawiera active_decks
        cards = []
        metrics = {"fps": 30.0}
        runtime = {}
        operator_without_decks = {"enabled": True, "active_profile": "default"}
        self.store.update_cv_state(cards, metrics, runtime, operator_without_decks)
        
        # 3. Weryfikacja, czy active_decks zostało zachowane
        status_after = self.store.get_status()
        self.assertEqual(status_after["operator"]["active_decks"], initial_decks)

    def test_update_cv_state_preserves_operator_explainability(self):
        explainability = {
            "severity": "warn",
            "next_action": "Zostaw mate nieruchomo przez kilka sekund.",
            "steps": [
                {
                    "id": "snapshot",
                    "label": "Snapshot",
                    "state": "wait",
                    "value": "settling",
                    "message": "Czeka na stabilny snapshot",
                }
            ],
        }
        operator = {
            "enabled": True,
            "active_profile": "default",
            "explainability": explainability,
        }

        self.store.update_cv_state([], {}, {}, operator)

        status = self.store.get_status()
        self.assertEqual(status["operator"]["explainability"], explainability)

if __name__ == '__main__':
    unittest.main()

