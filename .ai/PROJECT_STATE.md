# Stan Projektu — TarotVision (TAROT)

Ten plik przedstawia aktualny status techniczny oraz architekturę projektu TarotVision w pigułce. Służy jako punkt startowy dla każdego agenta AI wchodzącego do projektu.

* **Ostatnia weryfikacja procesu:** 2026-05-30 (Wdrożenie AI Workflow i CI w PR #1)

---

## 1. Informacje Ogólne

* **Projekt:** TarotVision / TAROT
* **Branch stabilny (produkcyjny):** `master`
* **Aktualna gałąź robocza:** `workflow/ci-bootstrap` (poprzednio `codex/snapshot-first-cv`)
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

* **Task Studio Console 5 & 5b-fix:** Pełne wdrożenie trybu Automatycznego Reżysera z 1.5s histerezą chroniącą przed migotaniem scen, wdrożenie paska osi czasu (Timeline Tracker) z automatycznym generowaniem i eksportem pliku JSON na frontendzie i backendzie oraz rygorystyczna walidacja struktur markerów i dozwolonych scen (allowlista).
* **Task Studio Console 6:** Zmiana szaty graficznej (akcent z jaskrawej żółci na zgaszoną miedź `#d67d3e`), podbicie czytelności czcionek diagnostyki CV Health oraz znaczne usprawnienie kontrastu i widoczności nieaktywnych (disabled) przycisków w bottombarze.

---

## 4. Status Integracji i Jakości (Workflow / CI)

* **Automatyzacja CI (WDROŻONA):** Skonfigurowano automatyczną weryfikację jakości w `.github/workflows/ci.yml`. Uruchamia ona testy Pythona, kompilację backendu oraz produkcyjny build frontendu. Oczekujemy na pierwszy zielony status z GitHub Actions po otwarciu PR.
* **Standardy Workflow (WDROŻONE):** Wdrożono katalog `.ai/` wraz z instrukcją `AI_WORKFLOW_FAILOVER.md`, rejestrem zadań `TASKS_INDEX.md` oraz szablonami szczegółów zadań pod `.ai/tasks/_TEMPLATE/`. Obowiązuje startup sequence zdefiniowany w `AGENTS.md`.
* **Szablon PR (WDROŻONY):** Każdy Pull Request korzysta teraz ze zintegrowanego szablonu `.github/pull_request_template.md` dla lepszej weryfikacji kryteriów i raportów testowych.
* **Zależności Python (WDROŻONE):** Utworzono plik `app_cv/requirements.txt` ze zwalidowanym zestawem paczek (OpenCV, NumPy, websockets, Pillow) stabilizujący proces instalacji w kontenerach CI.

---

## 5. Następne Priorytety

1. **Otwarcie Pull Requesta i Weryfikacja CI:** Uruchomienie pierwszego workflow runa na GitHubie dla gałęzi `workflow/ci-bootstrap` i scalenie zmian do `master` (wymaga zielonego statusu Actions oraz akceptacji Michała).
2. **Task Studio Console 6: CV health minimal:** Wdrożenie ograniczonego, bardzo czystego widoku parametrów diagnostycznych oraz optymalizacja HUD.
3. Dalsza integracja audio/reżysera w Konsoli Studio.
