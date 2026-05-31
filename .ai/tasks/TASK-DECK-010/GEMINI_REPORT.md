# GEMINI REPORT — TASK-DECK-010

## Task
TASK-DECK-010: UI wyboru 1–3 talii w Studio / launcherze

## Branch
`task/deck-010-studio-active-decks-ui`

## Base Commit
`5c04091`

## Head Commit
`b534f31`

## Files Changed
- `app_cv/tarotvision/status/status_store.py`
- `app_cv/tests/test_status_store.py`
- `app_ar/public/active_decks.json`
- `app_cv/tarotvision/tuning_protocol.py`
- `app_cv/tests/test_tuning_protocol.py`
- `app_cv/main.py`
- `app_ar/src/studio/studioConsole.js`
- `app_ar/src/renderer/textureCache.js`
- `app_ar/studio.css`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-DECK-010/TASK.md`
- `.ai/tasks/TASK-DECK-010/STATE.md`
- `.ai/tasks/TASK-DECK-010/CHANGELOG.md`
- `.ai/tasks/TASK-DECK-010/TEST_REPORT.md`
- `.ai/tasks/TASK-DECK-010/GEMINI_REPORT.md`

## Summary
- **POPRAWKA BŁĘDU (BUGFIX):** Naprawiono krytyczny błąd w backendzie (`status_store.py`), gdzie metoda `update_cv_state()` nadpisywała pole `operator` słownikiem z pętli CV bez pola `active_decks`. Zaimplementowano odporne zachowywanie i przywracanie listy `active_decks` pod lockiem przy każdej aktualizacji stanu CV.
- **TESTY JEDNOSTKOWE:** Dodano dedykowany test jednostkowy `test_update_cv_state_preserves_active_decks` w `test_status_store.py`, który w 100% potwierdza poprawne zachowanie.
- **USTALENIE DOMYŚLNYCH TALII:** Przywrócono i zwalidowano oficjalny zestaw domyślny aktywnych talii w `active_decks.json` na: `rider-waite-smith`, `zodiak`, `magic`.
- Zaimplementowano nowoczesne premium UI w konsoli Studio umożliwiające interaktywne zaznaczanie i odznaczanie talii z rygorystycznym limitem 1-3 aktywnych talii jednocześnie (switche/checkboxy stają się disabled przy osiągnięciu limitów, zapobiegając błędom operatora).
- Wdrożono nowy typ wiadomości WebSocket `"studio_set_active_decks"` z pełną walidacją wejściową na backendzie.
- Opracowano i zintegrowano logikę hot-reloadu wzorców CV w locie pod lockiem `status_lock` bezpośrednio w głównym wątku CV, wyodrębniając ładowanie do `load_reference_cards()`. CV backend w locie wyczyszcza i wczytuje ORB nowo wybranej konfiguracji i synchronizuje stół w `table_state`.
- Wdrożono funkcję reaktywnego preloading'u brakujących 78 tekstur w locie we frontendowym cache `dynamicPreloadDecks()` za pomocą dynamicznego importu, eliminując błędy brakujących tekstur w Three.js.
- Ostylowano nową sekcję w Sidebarze Studio z mikro-animacjami hover, active i disabled, pasującymi do premium zgaszonej miedzi `#d67d3e`.
- Wszystkie 174 testy jednostkowe CV przechodzą na zielono, a budowanie Vite przebiega poprawnie.

## Tests Run
- `cd app_cv && python -m unittest discover tests` => **PASS** (174/174 OK)
- `python scripts/validate_decks_manifest.py` => **PASS**
- `cd app_ar && npm run build` => **PASS**

## Known Risks
- **Opóźnienia I/O przy ładowaniu wzorców:** Wątek serwera WebSocket i wątek przetwarzania obrazu CV współdzielą `StatusStore` i `reference_cards`. Ponowne ładowanie plików z dysku przy częstym przełączaniu talii może powodować chwilowy spadek FPS (kilkadziesiąt ms) w pętli CV. Zabezpieczeniem jest zintegrowany lock, ale operator powinien unikać zbędnego klikania "Zastosuj" sekunda po sekundzie w trakcie audycji na żywo.
- **Wycieki pamięci w GPU:** Dynamiczne doładowywanie tekstur we frontendzie (do 78 kart na talię) zwiększa narzut pamięci VRAM. Częste rotowanie 7 talii bez odświeżania okna przeglądarki może doprowadzić do akumulacji nieużywanych tekstur w pamięci, dopóki Three.js lub silnik przeglądarki ich nie zwolni.
- **Fałszywe detekcje (False matches):** W przypadku, gdy operator zmieni talie, a na stole fizycznie leżą jeszcze karty z poprzedniej talii, pętla CV może chwilowo przypisać je do nowo wczytanych wzorców o podobnym wyglądzie konturów, dopóki stół nie zostanie oczyszczony.

## Request for Supervisor
APPROVAL
