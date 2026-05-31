# Stan Projektu — TarotVision (TAROT)

Ten plik przedstawia aktualny status techniczny oraz architekturę projektu TarotVision w pigułce. Służy jako punkt startowy dla każdego agenta AI wchodzącego do projektu.

* **Ostatnia weryfikacja procesu:** 2026-05-31 (Ustandaryzowanie komunikacji między modelami AI przez GitHub)

---

## 1. Informacje Ogólne

* **Projekt:** TarotVision / TAROT
* **Branch stabilny (produkcyjny):** `master`
* **Aktualna gałąź robocza:** `master` / task branches według bieżącego zadania
* **Aktualny etap:** Zaawansowany Proof of Concept (PoC) / Wczesne MVP Techniczne
* **Architektura przetwarzania (Pipeline):**
  `Kamera USB (fizyczna / mock)` ➔ `Python/OpenCV (Detekcja kart)` ➔ `WebSocket (Protokół Payload v1)` ➔ `Aplikacja Frontend AR / Studio (Vite + Three.js)` ➔ `OBS Studio (Nakładka graficzna)`

---

## 2. Główne Moduły Systemu

### Backend (`app_cv/`)
* `tarotvision/status/status_store.py` — wątkobezpieczny magazyn stanu systemu (diagnostyka, tryb reżyserski, audio, status nagrywania).
* `tarotvision/tuning_protocol.py` — orkiestracja i rygorystyczna walidacja poleceń WebSocket napływających z konsoli Studio.
* `tarotvision/camera/camera_session.py` — abstrakcja i obsługa sesji fizycznej kamery USB.
* `tarotvision/pipelines/` — system przetwarzania klatek wideo (Snapshot-First i Legacy State-First).
* `main.py` — główny entrypoint backendu orkiestrujący pętlę CV i serwer WebSocket.

### Frontend (`app_ar/`)
* `src/studio/studioConsole.js` — dynamiczny moduł interfejsu konsoli Studio (`?studio=1`).
* `src/studio/studioState.js` — współdzielone zarządzanie lokalnym stanem konsoli (timer, recorder, timeline, audio).
* `src/studio/director.js` — silnik automatycznego reżysera (Auto Mode) z histerezą czasową (1.5s).
* `src/studio/timeline.js` — dynamiczna oś czasu i system wstrzykiwania/zapisu markerów zdarzeń.
* `src/studio/audioMixer.js` — lokalny mikser audio oparty na Web Audio API (efekty SFX offline, wskaźniki peak, połączenie mikrofonu ze strumieniem nagrywania).
* `src/studio/mediaRecorderController.js` — orkiestracja zapisu canvasu WebGL i master audio do pliku WebM.
* `studio.css` — premium style wizualne konsoli oparte na zgaszonym kolorze miedzi (`#d67d3e`).

---

## 3. Ostatnie Ukończone Duże Prace

* **TASK-CV-DIAG-001 (Diagnostyka błędu rozpoznawania kart):** Przeprowadzono kompleksową, read-only analizę pętli CV oraz rurociągu Snapshot-First. Zidentyfikowano podwójną główną przyczynę (Double Root Cause) zgłaszanego braku detekcji: niedopasowanie bazy talii (fizyczna karta na stole to talia Boski/Marchetti, natomiast w Studio zaznaczono talie "Gilded") oraz brak pełnej kalibracji stołu (kamera obejmuje tylko 2 z 4 wymaganych markerów ArUco, co blokuje stabilizację obrazu). Opracowano dokładną 12-punktową procedurę naprawczą dla operatora bez modyfikacji kodu. **[STATUS: UKOŃCZONE / DIAGNOSTYKA OK]**
* **TASK-STUDIO-007-FIX / FIX2 (Hotfixy i ostateczna przebudowa launchera na GOTO):** Zaimplementowano w pełni odporny na błędy składni parser Windows CMD w deweloperskim skrypcie `start_tarotvision_studio.bat`. Całkowicie wyeliminowano zagnieżdżone, wielowierszowe bloki nawiasów instrukcji warunkowych `if (...)` i przeprowadzono kompletną refaktoryzację mechanizmu sprawdzania portów na płaski model etykiet `goto` (:PORT_BUSY, :KILL_PORT_PROCESS itp.). Trwale i bezbłędnie rozwiązało to krytyczny błąd natychmiastowego zamykania się okna konsoli zaraz po uruchomieniu, wywołany przez surowe nawiasy okrągłe w komendach echo (np. w tekście "(Vite / Node)"). **[APPROVED BY CHATGPT SUPERVISOR (PR #7 + PR #9 fix)]**
* **TASK-STUDIO-007 (Port-aware Studio Launcher Hardening):** Utwardzono dedykowany launcher Konsoli Studio (`start_tarotvision_studio.bat`) poprzez wdrożenie automatycznej weryfikacji zajętości portu `5173` przed podniesieniem serwerów deweloperskich. Launcher korzysta ze zintegrowanego skryptu PowerShell do sprawdzania aktywnych połączeń TCP i w przypadku detekcji kolizji (np. starej wiszącej instancji Node w tle) prezentuje operatorowi jasnoczerwony baner ostrzegawczy z 3 opcjami: automatycznym wymuszeniem zatrzymania procesu na porcie 5173, kontynuacją na własne ryzyko, bądź bezpiecznym i czystym przerwaniem startu (domyślnie). Zaimplementowano poprawkę delayed expansion (`setlocal EnableDelayedExpansion` i składnia `!PORT_CHOICE!`) gwarantującą bezbłędną dynamiczną ewaluację wyboru operatora na maszynach Windows. **[APPROVED BY CHATGPT SUPERVISOR (PR #6 + PR #7 hotfix + PR #9 fix)]**
* **TASK-STUDIO-006 (Diagnostyka CV Health Minimal i Dedykowany Launcher Studio):** Wdrożono minimalistyczny podgląd parametrów diagnostycznych CV Health w Studio Console (`?studio=1`) oraz elegancki interfejs ostrzeżeń operatorskich (CV warning HUD). Panel ostrzeżeń reaguje dynamicznie w czasie rzeczywistym na tablicę `warnings` w payloadzie WebSocket i prezentuje ostatnie ostrzeżenie w ciemnoczerwonym boksie z luksusowo pulsującym obramowaniem miedziano-czerwonym (zgodnie z brandingiem zgaszonej miedzi `#d67d3e`). Dodatkowo utworzono dedykowany launcher startowy Windows `start_tarotvision_studio.bat`, który umożliwia wybór talii startowej i automatycznie uruchamia system otwierając Studio Console bezpośrednio pod adresem `http://localhost:5173/?studio=1`. Zmiana została zweryfikowana pomyślnym przebiegiem wszystkich 176 testów backendowych oraz poprawnym budowaniem frontendu w Vite. **[APPROVED BY CHATGPT SUPERVISOR (PR #5)]**
* **TASK-DECK-010 (UI wyboru 1–3 aktywnych talii w Studio i launcherze):** Umożliwiono operatorowi dynamiczne wybieranie i zatwierdzanie od 1 do 3 jednocześnie aktywnych talii bezpośrednio z poziomu interfejsu konsoli reżyserskiej Studio (nowy WebSocket command `studio_set_active_decks`). Wdrożono mechanizm dynamicznego preloadowania tekstur kart w locie w silniku Three.js frontendu bez konieczności przeładowywania strony oraz hot-reload wzorców w backendzie CV. Stan jest zapisywany w pliku konfiguracji `app_ar/public/active_decks.json` (przy użyciu formatu `"version": 1`). Zmiana została zabezpieczona nowymi testami jednostkowymi `StatusStore.update_cv_state` w celu zagwarantowania spójności stanu operatora. **[APPROVED BY CHATGPT SUPERVISOR (PR #4)]**
* **TASK-COMM-001 (Standard komunikacji modeli AI):** Dodano `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md` jako wspólny standard przekazywania pracy między ChatGPT Supervisor, Gemini, Codex i Opus. Michał nie musi decydować, czy instrukcja ma trafić do issue, PR review, komentarza czy pliku `.md`; model zapisujący informację wybiera właściwy kanał GitHuba.
* **TASK-SCAN-001 (Obróbka Skanów - Hardening):** Kompleksowe utwardzenie i parametryzacja skryptu `scripts/process_scans.py` (CLI, autodetekcja tła, robust corner ordering, PNG/JPG/WebP, podgląd debug i dry-run). Skrypt pomyślnie przeszedł weryfikację na danych syntetycznych (reprodukowalne testy dodane do repozytorium) i jest w pełni gotowy do pierwszych prób kalibracyjnych na fizycznych skanach z urządzenia.
* **Diagnostyka i Uodpornienie Skanowania WIA (2026-05-31):** Wykryto i rozwiązano problem ze zlewaniem się białych ramek kart tarota z jasnym tłem zamkniętej pokrywy skanera. Wdrożono autodetekcję tła jako domyślny tryb (`--background auto`), zwiększono limit wierzchołków aproksymacji konturu z 6 do 8 w celu obsługi zaokrąglonych rogów fizycznych kart, oraz dodano system rejestrowania logów (`logs/process_scans.log`) i stałego zapisu kopii diagnostycznej (`scans_input/last_wia_scan.jpg`). Stworzono szczegółowy raport: `analizy/diagnostyka_skanowania_2026-05-31.md`. Ponadto wdrożono usprawnienie asystenta operatorskiego: po obróbce każdego pojedynczego arkusza, skrypt wypisuje teraz duży, widoczny baner informujący, ile kart dokładnie wycięto z tego konkretnego skanu, obok ogólnego licznika postępu. Umożliwia to operatorowi bieżącą kontrolę nad pracą skanera. **[DODATKOWO]** Zaimplementowano odporną na błędy systemowe Windows metodę zapisu obrazów OpenCV (`save_image_unicode`) wykorzystującą enkoding bajtowy przez standardowe wejście/wyjście Pythona, co pozwala na pomyślne skanowanie talii z polskimi znakami diakrytycznymi (np. "Światło i Cień") bezpośrednio do dedykowanych folderów bez błędów "cichego braku zapisu".
* **TASK-DECK-001 (Wdrożenie nowej talii Zodiak + Dynamiczne wczytywanie w locie):** Pomyślnie zaimportowano 79/79 plików z fizycznego skanu talii Zodiak za pomocą asystenta `prepare_zodiak.py`. Wygenerowano kompletne derywaty AR (WebP 1200px z przezroczystością), miniatury (WebP 150px) oraz wzorce CV (JPG 500px na czarnym tle) wraz z plikiem metadanych `info.json`. Ponadto uelastyczniono backend CV (`main.py`) umożliwiając dynamiczny start z dowolną talią za pomocą zmiennej środowiskowej `TAROTVISION_DECK` oraz zaimplementowano interaktywne menu wyboru talii w skrypcie uruchomieniowym `start_tarotvision.bat`. Frontend (`textureCache.js`) został rozbudowany o automatyczny preload i wsparcie dla obu talii w locie. Testy jednostkowe (171 zielonych) potwierdziły pełną kompatybilność i brak regresji.
* **Uniwersalna automatyzacja importu talii (2026-05-31):** Stworzono i spushowano w pełni uniwersalny skrypt asystenta `scripts/prepare_deck.py`, który przyjmuje nazwę talii jako parametr. Automatycznie zakłada foldery w `biblioteka_talii/<deck_name>/`, generuje kopie `mastery`, zoptymalizowane pod AR pliki WebP 1200px (kopiowane też do Vite `app_ar/public/karty`), miniatury WebP 150px oraz wzorce CV JPG 500px na czarnym tle wraz z automatycznym plikiem metadanych `info.json`. Zaimportowano nim w locie kompletną, 79-plikową talię **Magic** (Tarot of Mystical Moments), w 100% kompletną 78-kartową talię **Gilded** (The Gilded Tarot Ciro Marchettiego), w 100% kompletną 78-kartową talię **Marchetti** (Tarot Marchetti) oraz w 100% kompletną 78-kartową talię **Boski** (Boski Tarot / Legacy of the Divine Tarot). Wszystkie te talie zostały w pełni zintegrowane z frontendem (wstępne ładowanie w `textureCache.js`) oraz dodane do interaktywnego menu wyboru talii w skrypcie uruchomieniowym `start_tarotvision.bat`.
* **Wdrożenie Pełnej Ustandardyzowanej Talii RWS (78 skanów + rewers):** Zastąpiono stare, internetowe assety kart pełną, fizycznie zeskanowaną talią Rider-Waite-Smith (78 awersów oraz 1 rewers), wprowadzając w 100% ustandardyzowane nazewnictwo w formacie `RWS_00` do `RWS_77` oraz `RWS_back` (całkowita rezygnacja z nazw postaci). Zmiany zostały zintegrowane w kodzie frontendu (dynamiczny preload 78 tekstur w locie w `textureCache.js`), w pełni zwalidowane jednostkowo (171 testów zielonych) oraz pomyślnie skompilowane w Vite. Zmiany zostały zacommitowane i spushowane do gałęzi `master` na serwerze, co rozwiązało zgłaszane przez użytkownika ograniczenie do 22 kart.
* **Task Studio Console 5 & 5b-fix:** Pełne wdrożenie trybu Automatycznego Reżysera z 1.5s histerezą chroniącą przed migotaniem scen, wdrożenie paska osi czasu (Timeline Tracker) z automatycznym generowaniem i eksportem pliku JSON na frontendzie i backendzie oraz rygorystyczna walidacja struktur markerów i dozwolonych scen (allowlista).
* **Task Studio Console 6:** Zmiana szaty graficznej (akcent z jaskrawej żółci na zgaszoną miedź `#d67d3e`), podbicie czytelności czcionek diagnostyki CV Health oraz znaczne usprawnienie kontrastu i widoczności nieaktywnych (disabled) przycisków w bottombarze.

---

## 4. Status Integracji i Jakości (Workflow / CI)

* **Komunikacja między modelami AI (WDROŻONA):** Standard zapisany w `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`. Komenda Michała „Zapisz to w GitHubie” oznacza zgodę na zapis komunikacji projektowej (issue, komentarz, PR review, plik `.md` w `.ai/`), ale nie oznacza zgody na zmianę kodu produkcyjnego, merge, kasowanie plików ani refaktor.
* **Automatyzacja CI (WDROŻONA & ZWERYFIKOWANA):** Skonfigurowano automatyczną weryfikację jakości w `.github/workflows/ci.yml`. Pierwszy oficjalny run GitHub Actions na gałęzi `master` (run **`26684570640`**) zakończył się **pełnym sukcesem na zielono (PASS)**. Zarówno testy Pythona (171 testów), jak i kompilacja frontendu przechodzą bezbłędnie w chmurze.
* **Standardy Workflow (WDROŻONE):** Wdrożono katalog `.ai/` wraz z instrukcją `AI_WORKFLOW_FAILOVER.md`, rejestrem zadań `TASKS_INDEX.md`, protokołem komunikacji `AI_AGENT_COMMUNICATION_PROTOCOL.md` oraz szablonami szczegółów zadań pod `.ai/tasks/_TEMPLATE/`.
* **Szablon PR (WDROŻONY):** Każdy Pull Request korzysta teraz ze zintegrowanego szablonu `.github/pull_request_template.md` dla lepszej weryfikacji kryteriów i raportów testowych.
* **Zależności Python (WDROŻONE):** Utworzono plik `app_cv/requirements.txt` ze zwalidowanym zestawem paczek (OpenCV, NumPy, websockets, Pillow) stabilizujący proces instalacji w kontenerach CI.

---

## 5. Następne Priorytety

1. **Lokalny smoke test deweloperski master (Priorytet krytyczny):** Uruchomienie zaktualizowanego systemu launcherem `start_tarotvision_studio.bat` na maszynie Windows operatora w celu weryfikacji całego stosu (Vite deweloperski, serwer CV, dynamiczny wybór talii, statusy WebSocket oraz warning HUD w Studio Console) po złączeniu ostatnich ważnych prac i poprawek (PR #4, #5, #6, #7, #9) na stabilnym `master`.
2. **Dalsze małe zadania stabilizacyjne:** Realizacja drobnych, bezpiecznych poprawek w systemie deweloperskim bez wprowadzania ryzykownych zmian w kodzie mastera.
3. Dalsza integracja audio/reżysera w Konsoli Studio.

> [!IMPORTANT]
> **Status gałęzi roboczych (Zakończone / Historyczne):**
> Stare branche robocze dewelopera `task/studio-007-port-hardening`, `task/studio-007-cmd-parentheses-fix`, `task/studio-007-fix2-goto-port-check` oraz niedokończony branch `task/doc-003-update-project-state-after-studio-007` zostały pomyślnie scalone/zastąpione i **nie są już gałęziami roboczymi (są nieaktywne)**. Wszelkie kolejne prace i ewentualne poprawki są realizowane na czystych, nowych gałęziach.
