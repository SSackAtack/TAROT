# TASK-STUDIO-006 — Changelog

## [2026-05-31] — Implementacja HUD ostrzeżeń CV i dedykowanego launchera Studio

### Zmiany produkcyjne

#### Frontend (`app_ar`)

- **[MODIFY]** `app_ar/src/studio/studioConsole.js`
  - Wdrożono dynamiczne pobieranie i renderowanie ostatniego elementu z tablicy `warnings` WebSocket payloadu.
  - Dodano przełączanie widoczności kontenera ostrzeżeń w czasie rzeczywistym.
- **[MODIFY]** `app_ar/studio.css`
  - Dodano definicje klas `.studio-cv-warning-box`, `.studio-cv-warning-title` oraz `.studio-cv-warning-text`.
  - Zaprojektowano płynną animację pulsowania granic (czerwień ostrzegawcza <-> zgaszona miedź `#d67d3e`) pod nazwą `warning-pulse`.

#### Narzędzia i Uruchamianie

- **[NEW]** `start_tarotvision_studio.bat`
  - Dodano dedykowany launcher Windows, który automatycznie kieruje operatora bezpośrednio na konsolę reżyserską Studio (`http://localhost:5173/?studio=1`).
  - Zaimplementowano interaktywny wybór talii startowej (1-7) zgodny z bazowym launcherem.

#### Indeksowanie

- **[MODIFY]** `.ai/TASKS_INDEX.md`
  - Zaktualizowano status zadania `TASK-STUDIO-006` na `DONE`.
