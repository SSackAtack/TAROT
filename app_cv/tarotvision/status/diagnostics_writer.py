# -*- coding: utf-8 -*-
"""
Moduł zapisu diagnostyki (DiagnosticsWriter) aplikacji TarotVision.
"""
import os
import json
import time

class DiagnosticsWriter:
    def __init__(self, log_dir, filename="cv_metrics.jsonl", reset_on_start=False):
        """
        Inicjalizuje DiagnosticsWriter.
        
        Args:
            log_dir (str): Katalog zapisu logów.
            filename (str): Nazwa pliku logu.
            reset_on_start (bool): Czy usunąć istniejący plik logu przy starcie.
        """
        self.log_dir = log_dir
        self.filename = filename
        self.filepath = os.path.join(log_dir, filename)
        
        # Tworzenie katalogu logów, jeśli nie istnieje
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Resetowanie logów na starcie, jeśli wymagane
        if reset_on_start and os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except OSError:
                pass  # Ignorujemy błędy usuwania, np. gdy plik jest zablokowany

    def append(self, metrics_snapshot, runtime_snapshot, active_cards):
        """
        Zapisuje kolejną klatkę diagnostyki w formacie JSON Lines.
        
        Args:
            metrics_snapshot (dict): Słownik z metrykami wydajnościowymi i CV.
            runtime_snapshot (dict): Słownik z ustawieniami czasu uruchomienia.
            active_cards (list): Lista aktualnie wykrytych kart.
        """
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "detected": len(active_cards) > 0,
            "card_count": len(active_cards),
            "cards": active_cards,
            "metrics": metrics_snapshot,
            "runtime": runtime_snapshot
        }
        
        try:
            with open(self.filepath, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            # W środowisku produkcyjnym nie crashujemy głównego rurociągu CV z powodu błędu I/O
            pass
