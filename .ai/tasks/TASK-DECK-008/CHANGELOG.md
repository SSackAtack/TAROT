# CHANGELOG — TASK-DECK-008

## 2026-05-31 — Gemini Implementation

### Added
- `.ai/tasks/TASK-DECK-008/TASK.md` — cele, zakres i kryteria akceptacji zadania.
- `.ai/tasks/TASK-DECK-008/STATE.md` — status i aktualny stan zadania.
- `.ai/tasks/TASK-DECK-008/TEST_REPORT.md` — szczegółowy raport z testów i weryfikacji.
- `.ai/tasks/TASK-DECK-008/GEMINI_REPORT.md` — oficjalny raport z wdrożenia dla ChatGPT Supervisor.

### Changed
- `app_cv/main.py` — przebudowano ładowanie cyfrowych wzorców CV, zastępując sztywne wczytywanie pojedynczej talii dynamicznym wczytywaniem wzorców dla wszystkich zdefiniowanych w sesji aktywnych talii (1–3), z wdrożeniem fail-safe.
- `.ai/TASKS_INDEX.md` — dodano wpis `TASK-DECK-008` i zaktualizowano status.

### Not Changed
- Nie zmieniono algorytmu detekcji ani dopasowania cech w silniku CV.
- Nie modyfikowano WebSocket payload ani protokołu kontroli.
- Nie zmieniono fizycznych assetów wzorców graficznych w `biblioteka_talii/`.
- Nie zmieniono kodu produkcyjnego frontendu w `app_ar/`.
