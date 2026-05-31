# CHANGELOG — TASK-DECK-007

## 2026-05-31 — Gemini Implementation

### Added
- `.ai/tasks/TASK-DECK-007/TASK.md` — cele, zakres i kryteria akceptacji zadania.
- `.ai/tasks/TASK-DECK-007/STATE.md` — stan zadania z oznaczeniem `DONE`.
- `.ai/tasks/TASK-DECK-007/TEST_REPORT.md` — szczegółowe sprawozdanie z weryfikacji.
- `.ai/tasks/TASK-DECK-007/GEMINI_REPORT.md` — oficjalny raport dla ChatGPT Supervisor.

### Changed
- `app_ar/src/renderer/textureCache.js` — przebudowano ładowanie tekstur, zamieniając sztywne tablice statyczne na dynamiczne wczytywanie metadanych sesji i manifestu talii wraz z wdrożeniem fail-safe.
- `.ai/TASKS_INDEX.md` — dodano wpis `TASK-DECK-007` i zaktualizowano status.

### Not Changed
- Nie zmieniono innych plików produkcyjnych frontendu.
- Nie zmieniono kodu produkcyjnego backendu CV w `app_cv/`.
- Nie modyfikowano WebSocket payload.
- Nie zmieniono fizycznych assetów graficznych w `app_ar/public/karty/` ani `biblioteka_talii/`.
