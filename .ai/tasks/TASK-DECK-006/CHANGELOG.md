# CHANGELOG — TASK-DECK-006

## 2026-05-31 — Gemini Implementation

### Added
- `app_ar/public/decks_manifest.json` — centralny manifest 7 dostępnych w projekcie talii wraz z ich metadanymi i ścieżkami technicznymi.
- `app_ar/public/active_decks.json` — plik konfiguracyjny bieżącej sesji czytania, określający aktywne talie (domyślnie: Rider-Waite-Smith, Zodiak, Magic).
- `scripts/validate_decks_manifest.py` — rygorystyczny skrypt walidacji spójności danych, poprawności limitów i fizycznej obecności plików na dysku.
- `.ai/tasks/TASK-DECK-006/GEMINI_REPORT.md` — oficjalny raport z wdrożenia dla ChatGPT Supervisor.

### Changed
- `.ai/TASKS_INDEX.md` — zaktualizowano status zadania `TASK-DECK-006` z `TODO` na `IN_PROGRESS` (a po weryfikacji na `DONE`).
- `.ai/tasks/TASK-DECK-006/STATE.md` — zaktualizowano status na `DONE` oraz dodano szczegółowy opis prac.
- `.ai/tasks/TASK-DECK-006/TEST_REPORT.md` — rozbudowano raport testów o wyniki walidacji manifestu oraz testy jednostkowe.

### Not Changed
- Nie modyfikowano algorytmu CV ani kodu produkcyjnego backendu w `app_cv/`.
- Nie modyfikowano logiki WebSocket payload.
- Nie modyfikowano kodu produkcyjnego frontendu w `app_ar/src/` (z wyjątkiem udanej kompilacji weryfikacyjnej Vite).
- Nie modyfikowano ani nie usuwano żadnych fizycznych assetów graficznych talii w `app_ar/public/karty/` ani `biblioteka_talii/`.
