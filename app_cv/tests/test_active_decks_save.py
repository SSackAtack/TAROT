# -*- coding: utf-8 -*-
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Ustawiamy tryb testowy w środowisku przed importem main.py
os.environ["TAROTVISION_TEST_MODE"] = "1"
import main


class TestActiveDecksSave(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Przygotowujemy tymczasowe ścieżki
        self.active_decks_path = os.path.join(self.temp_dir, "active_decks.json")
        self.decks_manifest_path = os.path.join(self.temp_dir, "decks_manifest.json")
        
        # Nadpisujemy ścieżki w zaimportowanym module main
        self.old_active_path = main.active_decks_path
        self.old_manifest_path = main.decks_manifest_path
        
        main.active_decks_path = self.active_decks_path
        main.decks_manifest_path = self.decks_manifest_path
        
        # Przygotowujemy sztuczny decks_manifest.json
        self.manifest_data = {
            "version": 1,
            "decks": [
                {"id": "rider-waite-smith", "display_name": "RWS"},
                {"id": "zodiak", "display_name": "Zodiak"},
                {"id": "magic", "display_name": "Magic"}
            ]
        }
        with open(self.decks_manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest_data, f, indent=2)

    def tearDown(self):
        main.active_decks_path = self.old_active_path
        main.decks_manifest_path = self.old_manifest_path
        shutil.rmtree(self.temp_dir)

    @patch("main.load_reference_cards")
    @patch("main.status_store")
    @patch("main.add_operator_warning")
    def test_save_active_decks_correct_format(self, mock_warn, mock_store, mock_load):
        # Symulujemy poprawną wiadomość
        message = MagicMock()
        message.type = "studio_set_active_decks"
        message.active_decks = ["rider-waite-smith", "magic"]
        
        # Wywołujemy funkcję handlera z main.py
        camera_mock = MagicMock()
        main.handle_control_message(message, camera_mock)
        
        # 1. Sprawdzamy czy plik active_decks.json został utworzony i zapisany
        self.assertTrue(os.path.exists(self.active_decks_path))
        with open(self.active_decks_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            
        # 2. Weryfikacja kluczy oraz formatu: version ma być 1, a schema_version ma nie być obecne
        self.assertIn("version", saved_data)
        self.assertEqual(saved_data["version"], 1)
        self.assertNotIn("schema_version", saved_data)
        
        # 3. Weryfikacja zawartości listy aktywnych talii
        self.assertEqual(saved_data["active_decks"], ["rider-waite-smith", "magic"])
        
        # 4. Sprawdzamy czy wywołano przeładowanie wzorców i aktualizację statusu
        mock_load.assert_called_once_with(["rider-waite-smith", "magic"])
        mock_store.update_active_decks.assert_called_once_with(["rider-waite-smith", "magic"])
        
        # 5. Sprawdzamy czy dodano odpowiedni komunikat sukcesu
        mock_warn.assert_any_call("Studio: Pomyslnie wdrożono aktywne talie: ['rider-waite-smith', 'magic'] (Hot-Reload OK)")

    @patch("main.load_reference_cards")
    @patch("main.status_store")
    @patch("main.add_operator_warning")
    def test_save_active_decks_validation_failure(self, mock_warn, mock_store, mock_load):
        # Symulujemy niepoprawną wiadomość (nieistniejąca talia "fake-deck")
        message = MagicMock()
        message.type = "studio_set_active_decks"
        message.active_decks = ["rider-waite-smith", "fake-deck"]
        
        # Wywołujemy handlera
        camera_mock = MagicMock()
        main.handle_control_message(message, camera_mock)
        
        # 1. Sprawdzamy, czy plik active_decks.json NIE został utworzony ani zmodyfikowany
        self.assertFalse(os.path.exists(self.active_decks_path))
        
        # 2. Sprawdzamy, czy NIE wywołano procedury hot-reloadu i zapisu statusu
        mock_load.assert_not_called()
        mock_store.update_active_decks.assert_not_called()
        
        # 3. Sprawdzamy, czy operator otrzymał stosowne ostrzeżenie o błędzie walidacji
        mock_warn.assert_any_call("Studio: Blad zmiany talii. Talia fake-deck nie istnieje w manifeście!")


if __name__ == "__main__":
    unittest.main()
