# Indeks Zadań AI — TarotVision (TAROT)

Ten plik stanowi centralny rejestr wszystkich zadań (Tasks) realizowanych w projekcie TarotVision przez zespół AI. Każde zadanie musi posiadać swój wpis w tabeli oraz dedykowany katalog szczegółów w `.ai/tasks/TASK-XXX/`.

---

## Rejestr Zadań

| Task ID | Status | Gałąź (Branch) | Realizator (Owner) | Zakres (Scope) | Ostatnia aktualizacja | Status Review |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TASK-WF-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Scaffold struktury `.ai/` i standardy workflow | 2026-05-30 | ChatGPT Approved |
| **TASK-CI-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Konfiguracja GitHub Actions CI & requirements.txt | 2026-05-30 | Included in TASK-WF-001 |
| **TASK-PR-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Szablon Pull Request (.github/pull_request_template.md) | 2026-05-30 | Included in TASK-WF-001 |
| **TASK-DOC-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Aktualizacja README + AGENTS.md (startup sequence) | 2026-05-30 | Included in TASK-WF-001 |
| **TASK-CI-SMOKE-001** | `APPROVED` | `master` | Gemini | Weryfikacja dymna GitHub Actions na gałęzi master | 2026-05-30 | CI Confirmed Green (PASS) |
| **TASK-SCAN-001** | `APPROVED` | `master` | Gemini | Dostosowanie skryptu obróbki skanów pod skaner i jakość Premium | 2026-05-30 | ChatGPT Approved (PR #2) |
| **TASK-SCAN-002** | `APPROVED` | `master` | Gemini | Diagnostyka i uodpornienie skanowania WIA na flary i tła | 2026-05-31 | Confirmed 5/5 Green |
| **TASK-SCAN-003** | `APPROVED` | `master` | Gemini | Wdrożenie nowej talii Zodiak i obsługa wielu talii w locie | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-COMM-001** | `APPROVED` | `master` | ChatGPT Supervisor | Standard komunikacji między modelami AI przez GitHub | 2026-05-31 | Self-documented, owner requested |

---

## Statusy Zadań:
* `TODO` — Zadanie zaplanowane, oczekuje na realizację.
* `IN_PROGRESS` — Zadanie jest w trakcie aktywnej realizacji przez przypisanego agenta AI.
* `DONE` — Prace kodowe zostały zakończone i zweryfikowane lokalnie.
* `APPROVED` — Zadanie pomyślnie przeszło review i zostało scalone z gałęzią główną (`master`).
