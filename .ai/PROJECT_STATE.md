# Stan Projektu — TarotVision (TAROT)

Ten plik przedstawia aktualny status techniczny oraz architekturę projektu TarotVision w pigułce. Służy jako punkt startowy dla każdego agenta AI wchodzącego do projektu.

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

## 4. Aktualne Ryzyka i Stan Zablokowania

* **Brak CI/CD (W TRAKCIE ROZWIĄZYWANIA):** Do tej pory weryfikacja poprawności kodu (testy jednostkowe i kompilacja frontendu) opierała się wyłącznie na manualnych raportach agentów, co groziło regresją w przypadku braku uruchomienia testów lokalnie.
* **Brak sztywnych ram workflow (W TRAKCIE ROZWIĄZYWANIA):** Brak sformalizowanych zasad failover dla agentów AI i szablonów PR.
* **Requirements.txt (W TRAKCIE ROZWIĄZYWANIA):** Konieczność weryfikacji i stabilizacji pliku dependencies dla CI.

---

## 5. Następne Priorytety (Po zakończeniu wdrożenia procesu)

1. **TASK-WF-001 / TASK-CI-001 / TASK-PR-001 / TASK-DOC-001** (Zamknięcie bootstrapu workflow i automatyzacji testów w GitHub Actions).
2. Dalszy rozwój Konsoli Studio (np. **Task Studio Console 6: CV health minimal** lub integracja z zaawansowanym systemem montażu w tle).
