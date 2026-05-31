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

* **TASK-COMM-001 (Standard komunikacji modeli AI):** Dodano `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md` jako wspólny standard przekazywania pracy między ChatGPT Supervisor, Gemini, Codex i Opus. Michał nie musi decydować, czy instrukcja ma trafić do issue, PR review, komentarza czy pliku `.md`; model zapisujący informację wybiera właściwy kanał GitHuba.
* **TASK-SCAN-001 (Obróbka Skanów - Hardening):** Kompleksowe utwardzenie i parametryzacja skryptu `scripts/process_scans.py` (CLI, autodetekcja tła, robust corner ordering, PNG/JPG/WebP, podgląd debug i dry-run). Skrypt pomyślnie przeszedł weryfikację na danych syntetycznych (reprodukowalne testy dodane do repozytorium) i jest w pełni gotowy do pierwszych prób kalibracyjnych na fizycznych skanach z urządzenia.
* **Diagnostyka i Uodpornienie Skanowania WIA (2026-05-31):** Wykryto i rozwiązano problem ze zlewaniem się białych ramek kart tarota z jasnym tłem zamkniętej pokrywy skanera. Wdrożono autodetekcję tła jako domyślny tryb (`--background auto`), zwiększono limit wierzchołków aproksymacji konturu z 6 do 8 w celu obsługi zaokrąglonych rogów fizycznych kart, oraz dodano system rejestrowania logów (`logs/process_scans.log`) i stałego zapisu kopii diagnostycznej (`scans_input/last_wia_scan.jpg`). Stworzono szczegółowy raport: `analizy/diagnostyka_skanowania_2026-05-31.md`.
* **TASK-SCAN-003 (Wdrożenie nowej talii Zodiak + Dynamiczne wczytywanie w locie):** Pomyślnie zaimportowano 79/79 plików z fizycznego skanu talii Zodiak za pomocą asystenta `prepare_zodiak.py`. Wygenerowano kompletne derywaty AR (WebP 1200px z przezroczystością), miniatury (WebP 150px) oraz wzorce CV (JPG 500px na czarnym tle) wraz z plikiem metadanych `info.json`. Ponadto uelastyczniono backend CV (`main.py`) umożliwiając dynamiczny start z dowolną talią za pomocą zmiennej środowiskowej `TAROTVISION_DECK` oraz zaimplementowano interaktywne menu wyboru talii w skrypcie uruchomieniowym `start_tarotvision.bat`. Frontend (`textureCache.js`) został rozbudowany o automatyczny preload i wsparcie dla obu talii w locie. Testy jednostkowe (171 zielonych) potwierdziły pełną kompatybilność i brak regresji.
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

1. **Powrót do prac funkcjonalnych (Bezpieczny):** Dzięki pełnemu zielonemu statusowi CI w chmurze i wdrożonym ramom workflow, możemy bezpiecznie wrócić do rozwoju aplikacji.
2. **Task Studio Console 6: CV health minimal:** Wdrożenie ograniczonego, bardzo czystego widoku parametrów diagnostycznych oraz optymalizacja HUD.
3. Dalsza integracja audio/reżysera w Konsoli Studio.
