# TASK-DECK-008: Backend CV registry tylko dla aktywnych talii

## Goal
Zastąpić sztywne ładowanie wzorców pojedynczej talii (ze zmiennej środowiskowej `TAROTVISION_DECK`) dynamicznym ładowaniem wzorców dla wszystkich aktywnych w bieżącej sesji talii (od 1 do 3), wczytywanych z `active_decks.json` oraz `decks_manifest.json` (zmniejszenie obciążenia CPU/RAM poprzez pomijanie pozostałych talii).

## Context
Obecnie backend CV wczytuje tylko jedną talię wskazaną przez zmienną środowiskową. Po zdefiniowaniu manifestów i dynamicznego ładowania na frontendzie w TASK-DECK-007, kolejnym krokiem jest dostosowanie backendu CV, aby wczytywał wzorce dla wszystkich wybranych 1–3 aktywnych talii naraz. Rejestr wzorców `reference_cards` powinien być zapełniany kartami z aktywnych talii, co umożliwi rozpoznawanie kart z dowolnej z nich w locie.

## Scope
1. Zmodyfikować `app_cv/main.py`:
   - Dodać wczytywanie plików konfiguracyjnych sesji `app_ar/public/active_decks.json` oraz `app_ar/public/decks_manifest.json` (ścieżki relatywne do projektu).
   - Jeśli pliki istnieją, zinterpretować aktywne talie, pobrać ich ścieżki `cv_path` i wczytać wzorce `.jpg` dla każdej z nich do centralnego słownika `reference_cards`.
   - Zaimplementować odporny mechanizm **fail-safe** (fallback) - w przypadku braku plików konfiguracyjnych (np. w środowisku CI) system ładuje wzorce z talii określonej przez zmienną środowiskową `TAROTVISION_DECK` (lub domyślnie `rider-waite-smith`), zachowując dotychczasową logikę.
2. Zaktualizować status zadania w `.ai/TASKS_INDEX.md` oraz sporządzić raporty w katalogu taska.

## Out of Scope
- Nie zmieniać algorytmu detekcji i dopasowania cech (ORB + FLANN/BFMatcher).
- Nie modyfikować struktury WebSocket payload (deck_id zostanie wdrożony w kolejnym zadaniu TASK-DECK-009).
- Nie zmieniać sposobu uruchamiania launcherów.
- Nie usuwać ani nie modyfikować wzorców w `biblioteka_talii/`.

## Files Allowed to Change
- `app_cv/main.py`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-DECK-008/*`

## Acceptance Criteria
1. Backend CV dynamicznie odczytuje konfigurację sesji i wczytuje do pamięci (`reference_cards`) wzorce dla 1-3 aktywnych talii.
2. Wzorce ze wszystkich aktywnych talii są prawidłowo wczytywane w pętli.
3. System uruchamia się poprawnie (OK) na zielono.
4. Brak regresji - w środowisku testowym CI bez plików JSON system pomyślnie ładuje domyślną talię RWS z fallbacku.
5. Wszystkie testy jednostkowe backendu (171/171 PASS) przechodzą bez błędów.

## Tests Required
- `cd app_cv && python -m unittest discover tests`
- `python scripts/validate_decks_manifest.py`

## Reports Required
- `.ai/tasks/TASK-DECK-008/STATE.md`
- `.ai/tasks/TASK-DECK-008/CHANGELOG.md`
- `.ai/tasks/TASK-DECK-008/TEST_REPORT.md`
- `.ai/tasks/TASK-DECK-008/GEMINI_REPORT.md`

## Branch
`task/deck-008-backend-cv-registry`

## Commit Message
`feat: implement dynamic pattern loading for active decks in CV backend`
