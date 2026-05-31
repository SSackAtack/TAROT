# CHANGELOG — TASK-DECK-010

Wszystkie zmiany wprowadzone w ramach zadania **TASK-DECK-010: UI wyboru 1–3 talii w Studio / launcherze**.

## [1.0.0] - 2026-05-31

### Dodano (Added)
- Nowy typ wiadomości WebSocket `"studio_set_active_decks"` w `ALLOWED_TYPES` w `app_cv/tarotvision/tuning_protocol.py` do orkiestracji wyboru talii.
- Klasę `ControlMessage` rozbudowano o opcjonalne pole `active_decks: list | None = None` w celu bezpiecznego przesyłania wybranej konfiguracji.
- Rygorystyczną walidację i parser w `parse_control_message` w `tuning_protocol.py`, kontrolujący czy wejście jest poprawną listą stringów o długości 1-3.
- Metodę `update_active_decks(self, active_decks)` w `app_cv/tarotvision/status/status_store.py` w celu aktualizacji statusu aktywnych talii pod lockiem i rozesłania go przez WebSocket.
- Premium kartę/sekcję interfejsu wyboru talii **"Aktywne Talie (Active Decks)"** w Sidebarze w `app_ar/src/studio/studioConsole.js`.
- Logikę dynamicznego wczytywania manifestu `/decks_manifest.json` i renderowania checkboxów z harmonijnym ciemnym motywem.
- Rygorystyczną kontrolę wyboru w UI: limit 1-3 talii (dezaktywacja pozostałych opcji po wybraniu 3) oraz blokada odznaczenia ostatniego elementu (wymagane minimum 1 talia).
- Przycisk "Zastosuj Wybór" w UI wysyłający wiadomość `studio_set_active_decks` na backend.
- Reaktywną synchronizację stanu checkboxów w UI na podstawie przychodzącego WebSocket statusu z backendu w `updateStudioConsole(data)`.
- Funkcję `dynamicPreloadDecks(activeDecksList, onComplete)` w `app_ar/src/renderer/textureCache.js` asynchronicznie i reaktywnie pobierającą brakujące 78 tekstur w locie w przypadku wykrycia zmiany aktywnych talii, bez przerw technicznych.
- Style CSS i premium mikro-animacje hover, active oraz disabled w `app_ar/studio.css`.

### Zmodyfikowano i Ulepszono (Modified & Improved)
- Wyodrębniono wczytywanie wzorców ORB na backendzie w elastyczną funkcję `load_reference_cards(active_ids=None)` w `app_cv/main.py` umożliwiającą hot-reload w locie.
- W `handle_control_message` w `main.py` zaimplementowano obsługę `studio_set_active_decks` (zapis nowej listy do pliku `active_decks.json`, przeładowanie wzorców w locie za pomocą `load_reference_cards()`, synchronizacja kluczy i wyczyszczenie starego stanu w `table_state` oraz powiadomienie operatora).

### Poprawiono (Fixed)
- Naprawiono potencjalne Race Conditions w wątkach poprzez wywoływanie dynamicznego przeładowania wzorców ORB bezpośrednio w głównym wątku pętli CV (poprzez kolejkę orkiestrowaną przez `drain_control_messages`), eliminując zderzenia z wątkiem WebSocket.
