# TASK-STUDIO-007 — Changelog

## [2026-05-31] — Utwardzenie launchera Studio pod zajęty port 5173

### Zmiany produkcyjne

#### Launcher (`start_tarotvision_studio.bat`)

- **[MODIFY]** `start_tarotvision_studio.bat`
  - Zaimplementowano sprawdzanie zajętości portu `5173` przed startem Vite przy użyciu komendy PowerShell `Get-NetTCPConnection`.
  - Wdrożono interaktywne menu ostrzegawcze z wyborem dla operatora (ubicie procesu, kontynuacja na własne ryzyko, anulowanie startu).
  - Wzbogacono komunikację konsolową o estetyczne i wyraźne komunikaty ostrzegawcze (kolor jasnoczerwony dla zagrożeń, domyślny miedziano-żółty po pomyślnym starcie).

### Indeksowanie i dokumentacja

- **[MODIFY]** `.ai/TASKS_INDEX.md`
  - Zarejestrowano zadanie `TASK-STUDIO-007` jako `IN_PROGRESS`.
