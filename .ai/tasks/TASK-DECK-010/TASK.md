# TASK-DECK-010: UI wyboru 1–3 talii w Studio / launcherze

## Goal
Zaimplementować premium interfejs użytkownika (UI) w konsoli reżysera Studio (`?studio=1`) umożliwiający interaktywny wybór od 1 do 3 aktywnych talii spośród 7 dostępnych talii systemowych, z pełnym zapisem w locie do konfiguracji sesji (`active_decks.json`), dynamicznym przeładowaniem wzorców w backendzie CV w locie (bez restartu) oraz natychmiastowym przeładowaniem zasobów we frontendowym Three.js (dynamic cache reload).

## Context
Po wprowadzeniu manifestu talii (TASK-DECK-006), lazy-loadingu we frontendzie (TASK-DECK-007) oraz dynamicznego ładowania wzorców w backendzie (TASK-DECK-008), zmiana aktywnych talii wciąż wymagała ręcznej edycji pliku `active_decks.json` i restartu systemu. To zadanie wdraża kompletny przepływ w locie (hot-reload) sterowany przez operatora z poziomu interfejsu Studio. Pozwala to na płynną zmianę talii w trakcie trwania audycji bez przerw technicznych.

## Scope
1. **Rozszerzenie statusu systemowego (Backend Python):**
   - W `app_cv/tarotvision/status/status_store.py` wczytywać aktywne talie z `active_decks.json` przy inicjalizacji i udostępnić je w sekcji `operator["active_decks"]` w status payloadzie.
   - Dodać metodę aktualizacji statusu aktywnych talii w locie.
2. **Rozszerzenie protokołu WebSocket (Tuning Protocol):**
   - W `app_cv/tarotvision/tuning_protocol.py` dodać obsługę nowego typu wiadomości kontrolnej: `studio_set_active_decks`.
   - Zaimplementować rygorystyczną walidację w `parse_control_message` (dopuszczenie listy od 1 do 3 poprawnych identyfikatorów talii).
3. **Dynamiczne ładowanie wzorców w locie (Backend CV Hot-Reload):**
   - W `app_cv/main.py` obsłużyć komendę `studio_set_active_decks`.
   - Wyodrębnić kod ładowania wzorców ORB w dedykowaną funkcję (np. `load_reference_cards()`), pozwalającą na bezpieczne, jednoczesne (pod lockiem) wyczyszczenie starego cache `reference_cards` i załadowanie wzorców dla nowych aktywnych talii bezpośrednio w wątku CV w locie.
4. **Rozszerzenie UI Konsoli Studio (Frontend JS & CSS):**
   - W `app_ar/src/studio/studioConsole.js` stworzyć nową premium sekcję/kartę wyboru aktywnych talii (Active Decks) z nowoczesnymi elementami checkbox/switch.
   - Pobrać manifest `/decks_manifest.json` asynchronicznie, aby dynamicznie zbudować listę 7 talii wraz z ich nazwami wyświetlanymi.
   - Dodać logikę interakcji: ograniczenie wyboru do 1-3 talii (dezaktywacja pozostałych checkboxów przy osiągnięciu limitu 3).
   - Przy zatwierdzeniu wyboru wysyłać wiadomość `studio_set_active_decks` przez WebSocket.
5. **Dynamiczny Preload we frontendzie (Vite / Three.js Hot-Reload):**
   - Gdy przez WebSocket przychodzi zaktualizowana lista `active_decks` w statusie, sprawdzić, czy różni się od obecnie załadowanych w frontendzie.
   - Jeśli tak, zainicjować dynamiczne asynchroniczne doładowanie brakujących tekstur do `textureCache.js` w locie, aby Three.js mógł natychmiast wyrenderować nowo wykryte karty.
6. **Aktualizacja statusu zadania w `.ai/TASKS_INDEX.md` oraz sporządzenie raportów w katalogu taska.**

## Out of Scope
- Modyfikacja algorytmów OpenCV/ORB dla samej detekcji konturów.
- Zmiana w fizycznym pozycjonowaniu i kalibracji kamery.
- Zmiana wyglądu HUD dla samego widoku Live (wow mode / table mode).

## Files Allowed to Change
- `app_cv/tarotvision/status/status_store.py`
- `app_cv/tarotvision/tuning_protocol.py`
- `app_cv/main.py`
- `app_ar/src/studio/studioConsole.js`
- `app_ar/src/renderer/textureCache.js`
- `app_ar/src/renderer/cardFactory.js` (jeśli wymagane)
- `app_ar/studio.css`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-DECK-010/*`

## Acceptance Criteria
1. Interfejs konsoli Studio (`?studio=1`) zawiera w pełni sprawną premium sekcję "Aktywne Talie" (Active Decks) z harmonijną kolorystyką zgaszonej miedzi `#d67d3e` i ciemnym motywem.
2. Operator może zaznaczać i odznaczać talie. System wymusza rygorystyczny limit: minimum 1 i maksimum 3 aktywne talie jednocześnie (pozostałe opcje stają się nieaktywne po wybraniu 3).
3. Kliknięcie przycisku "Zastosuj" (Apply) wysyła wiadomość `studio_set_active_decks` przez WebSocket do backendu CV.
4. Backend poprawnie zapisuje zaktualizowany plik `active_decks.json` na dysku.
5. Backend CV natychmiastowo czyści stare wzorce w pamięci i ładuje wzorce nowo wybranych aktywnych talii w locie (hot-reload) bez race conditions w wątkach (potwierdzone logiem `[INFO] Ladowanie cyfrowych wzorcow...`).
6. System we frontendzie w locie preloaduje tekstury nowo aktywowanej talii (brak błędów brakujących tekstur przy kładzeniu kart z nowo wybranej talii).
7. Testy jednostkowe backendu (`python -m unittest discover tests` w `app_cv`) oraz walidacja manifestów przechodzą pomyślnie na zielono.
8. Kompilacja produkcyjna `npm run build` w `app_ar` kończy się sukcesem.

## Tests Required
- `cd app_cv && python -m unittest discover tests`
- `python scripts/validate_decks_manifest.py`
- `cd app_ar && npm run build`
- Ręczna weryfikacja w przeglądarce: otworzyć konsolę Studio, wybrać aktywne talie, kliknąć "Zastosuj" i sprawdzić, czy w logach backendu CV pojawia się przeładowanie wzorców i czy plik `active_decks.json` został zmieniony.

## Reports Required
- `.ai/tasks/TASK-DECK-010/STATE.md`
- `.ai/tasks/TASK-DECK-010/CHANGELOG.md`
- `.ai/tasks/TASK-DECK-010/TEST_REPORT.md`
- `.ai/tasks/TASK-DECK-010/GEMINI_REPORT.md`

## Branch
`task/deck-010-studio-active-decks-ui`

## Commit Message
`feat: implement interactive active decks selection UI in Studio and CV hot-reload`
