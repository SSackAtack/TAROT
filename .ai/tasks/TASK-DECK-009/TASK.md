# TASK-DECK-009: WebSocket payload z deck_id + card_id

## Goal
Rozszerzyć strukturę payloadu danych o wykrytych kartach wysyłanych przez serwer WebSocket (backend Python) do frontendu (JavaScript), dodając pola `deck_id` oraz `card_id` do każdego słownika karty, przy jednoczesnym zachowaniu pełnej spójności i kompatybilności wstecznej (zero regresji).

## Context
Po optymalizacji wczytywania zasobów aktywnych talii we frontendzie i backendzie CV, kolejnym krokiem architektonicznym jest rozszerzenie protokołu WebSocket. Zamiast dotychczasowej pojedynczej nazwy `name` (np. `"Zodiak_00"`), każda karta w tablicy `cards` payloadu WebSocket będzie jednoznacznie zidentyfikowana za pomocą technicznego `card_id` oraz identyfikatora talii `deck_id` (np. `"zodiak"`). Umożliwi to w kolejnym kroku (TASK-DECK-010) łatwe grupowanie, dynamiczne zarządzanie scenami i rozróżnianie talii w interfejsie Studio.

## Scope
1. Zmodyfikować `app_cv/tarotvision/status/status_store.py`:
   - Dodać mechanizm odczytywania manifestu talii `decks_manifest.json` przy inicjalizacji.
   - Opracować odporną metodę `_get_deck_id(self, card_name)` dopasowującą prefiks karty (np. `"Zodiak"`) do technicznego ID talii (np. `"zodiak"`), z wdrożeniem fail-safe fallbacku ASCII.
   - Wzbogacić każdą kartę przekazywaną do `update_cv_state` o pola `"deck_id"` oraz `"card_id"` (ustawionym na dotychczasowy techniczny identyfikator `name`).
2. Zmodyfikować `app_ar/src/renderer/cardFactory.js` w celu uodpornienia frontendu na dynamiczne pobieranie kart za pomocą `card_id` (jako ulepszona wersja `name`).
3. Zaktualizować status zadania w `.ai/TASKS_INDEX.md` oraz sporządzić raporty w katalogu taska.

## Out of Scope
- Nie modyfikować algorytmów CV w Pythonie ani logiki śledzenia konturów.
- Nie zmieniać parametrów kalibracji i sterowania kamerą.
- Nie zmieniać widoku konsoli Studio (UI wyboru 1-3 talii to osobne zadanie TASK-DECK-010).

## Files Allowed to Change
- `app_cv/tarotvision/status/status_store.py`
- `app_ar/src/renderer/cardFactory.js`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-DECK-009/*`

## Acceptance Criteria
1. Każdy wpis w tablicy `cards` w payloadzie wysyłanym przez WebSocket zawiera pola `"deck_id"` (ASCII) oraz `"card_id"`.
2. Pole `"name"` jest nadal przesyłane w celu zachowania 100% kompatybilności wstecznej.
3. System Three.js na frontendzie bezbłędnie ładuje, pozycjonuje i animuje karty przy użyciu nowych danych.
4. Testy jednostkowe backendu (171/171 PASS) przechodzą bez błędów.
5. Zbudowanie produkcyjne frontendu (`npm run build`) kończy się sukcesem.

## Tests Required
- `cd app_cv && python -m unittest discover tests`
- `python scripts/validate_decks_manifest.py`
- `cd app_ar && npm run build`

## Reports Required
- `.ai/tasks/TASK-DECK-009/STATE.md`
- `.ai/tasks/TASK-DECK-009/CHANGELOG.md`
- `.ai/tasks/TASK-DECK-009/TEST_REPORT.md`
- `.ai/tasks/TASK-DECK-009/GEMINI_REPORT.md`

## Branch
`task/deck-009-websocket-payload`

## Commit Message
`feat: expand WebSocket payload with deck_id and card_id`
