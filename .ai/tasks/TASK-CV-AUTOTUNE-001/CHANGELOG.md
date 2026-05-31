# Wykaz Zmian (Changelog) — TASK-CV-AUTOTUNE-001

## 1. Modyfikowane i Nowe Pliki Produkcyjne

### `app_cv/tarotvision/auto_tuner.py` [NEW]
* Zaimplementowano funkcję `score_candidate_quad` oceniającą jakość wykrytego prostokąta na podstawie stosunku proporcji (closeness do 1.72), area ratio (preferowanie mniejszych zagnieżdżonych struktur zamiast całego A4) oraz centralności kandydata w kadrze.
* Zaimplementowano funkcję `tune_card_detection_params` przeprowadzającą optymalizację parametrów w ograniczonej przestrzeni coarse search (240 stanów) z weryfikacją budżetu `max_iterations` i obsługą poziomów wiarygodności (`LOW/MEDIUM/HIGH`).
* Dodano klasę `AutoTuner` stanowiącą obiektowy interfejs autotunera.

---

## 2. Pliki Testowe i Konfiguracyjne

### `app_cv/tests/test_auto_tuner.py` [NEW]
* `test_score_candidate_quad_bounds`: weryfikuje poprawność wyliczania wag matematycznych dla idealnych prostokątów.
* `test_autotuner_finds_params_for_synthetic_card`: potwierdza, że autotuner potrafi odnaleźć właściwą konfigurację Canny/mode dla syntetycznego obrazu karty na ciemnym tle z "HIGH" confidence.
* `test_autotuner_nested_a4_trap_resolution`: sprawdza, czy autotuner zwraca właściwe zagnieżdżone kontury w trybach `list`/`tree` i radzi sobie z pułapką A4.
* `test_autotuner_low_confidence_for_blank_image`: sprawdza zachowanie na pustych obrazach (oczekiwany score 0.0 i "LOW" confidence).
* `test_autotuner_respects_budget`: weryfikuje ścisłe przestrzeganie limitu iteracji.
