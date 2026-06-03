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
| **TASK-DECK-001** | `APPROVED` | `master` | Gemini | Wdrożenie nowej talii Zodiak i obsługa wielu talii w locie | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-002** | `APPROVED` | `master` | Gemini | Wdrożenie talii Magic i Gilded z integracją w launcherze i cache | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-003** | `APPROVED` | `master` | Gemini | Wdrożenie talii Marchetti z integracją w launcherze i cache | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-004** | `APPROVED` | `master` | Gemini | Wdrożenie talii Boski z integracją w launcherze i cache | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-SCAN-004** | `APPROVED` | `master` | Gemini | Usprawnienie auto-orientacji kart i segmentacji tła | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-COMM-001** | `APPROVED` | `master` | ChatGPT Supervisor | Standard komunikacji między modelami AI przez GitHub | 2026-05-31 | Self-documented, owner requested |
| **TASK-DECK-005** | `APPROVED` | `master` | Gemini | Wdrożenie talii Światło i Cień z integracją oraz uodpornieniem zapisu Unicode na Windowsie | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-006** | `APPROVED` | `master` | Gemini | Manifest talii i konfiguracja aktywnych talii sesji 1–3 talie | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-007** | `APPROVED` | `master` | Gemini | Frontend lazy loading tylko aktywnych talii | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-008** | `APPROVED` | `master` | Gemini | Backend CV registry tylko dla aktywnych talii | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-009** | `APPROVED` | `master` | Gemini | WebSocket payload z deck_id + card_id | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-010** | `APPROVED` | `master` | Gemini | UI wyboru 1–3 talii w Studio / launcherze | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR (PR #4) |
| **TASK-STUDIO-006** | `APPROVED` | `master` | Gemini | Diagnostyka CV Health Minimal i Dedykowany Launcher Studio | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR (PR #5) |
| **TASK-STUDIO-007** | `APPROVED` | `master` | Gemini | Uodpornienie launchera Studio pod zajęty port 5173 | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR (PR #6 + PR #9 fix) |
| **TASK-STUDIO-CV-EXPLAIN-001** | `APPROVED` | `master` | Codex | Panel CV Explain z przyczynami problemów i następnym krokiem operatora | 2026-06-02 | Local merge approved after full verification |
| **TASK-STUDIO-CV-EXPLAIN-002** | `TODO` | `task/studio-cv-explain-002-candidate-accepted-gap` | Codex/Gemini | Doprecyzowanie komunikatu różnicy między kandydatami kart a zaakceptowanymi rozpoznaniami | 2026-06-02 | Zaplanowane po live smoke |
| **TASK-CV-RECT-001** | `APPROVED` | `master` | Gemini | Parametryzacja detekcji prostokątów kart pod autotuning | 2026-06-02 | Approved as autotuning foundation |
| **TASK-CV-AUTOTUNE-001** | `APPROVED` | `master` | Gemini | Prototyp offline autotunera detekcji prostokąta karty | 2026-06-02 | Approved as offline foundation |
| **TASK-CV-AUTOTUNE-LIVE-001** | `IN_PROGRESS` | `codex/live-autotuning-foundation` | Codex/Gemini | Live autotuning jako rekomendacja profilu z apply/rollback i zapisem profilu | 2026-06-02 | Automated verification + recognition diagnostics + glare false-positive guard done; pending manual live smoke |
| **TASK-CV-EVENT-FIRST-PLAN-001** | `DONE` | `task/cv-event-first-plan-001-clarify-autotune-runtime` | Codex | Doprecyzowanie planu event-first background diff: Autotune vs Runtime | 2026-06-02 | Pending Supervisor Review |
| **TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001** | `DONE` | `task/cv-event-first-plan-001-clarify-autotune-runtime` | Codex | Research Gate Stage 1: metody detekcji różnic dla offline labu state-first | 2026-06-03 | Research complete; pending Supervisor stage decision |
| **TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001** | `APPROVED` | `task/cv-event-first-plan-001-clarify-autotune-runtime` | Codex | Offline benchmark Stage 1 Difference Detection na zatwierdzonych fixture | 2026-06-03 | Stage 1 method approved: gray_absdiff_gaussian; next: Research Stage 2 |
| **TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001** | `DONE` | `task/cv-event-first-plan-001-clarify-autotune-runtime` | Codex | Research Gate Stage 2: region segmentation/refinement dla offline labu state-first | 2026-06-03 | Research complete; pending Supervisor shortlist approval |
| **TASK-CV-SNAPSHOT-001** | `APPROVED` | `master` | Codex | Usunięcie legacy state-first i utrwalenie snapshot-first jako jedynego pipeline CV | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-002** | `APPROVED` | `master` | Codex | Unicode-safe image I/O i reference loader poza main.py | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-003** | `APPROVED` | `master` | Codex | Analiza snapshotu na klatce sprostowanej przez ArUco | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-004** | `APPROVED` | `master` | Codex | Diagnostyka porażek detekcji i rozpoznania snapshot-first | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-005** | `APPROVED` | `master` | Codex | Wieloprofilowa detekcja kart dla ciemnych talii i mat | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-006** | `APPROVED` | `master` | Codex | Opcjonalny model pustej maty dla background-diff | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-007** | `APPROVED` | `master` | Codex | Recognition-aware snapshot autotuning offline | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-008** | `APPROVED` | `master` | Codex | Lokalny benchmark snapshot recognition dla talii i mat | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-LIVE-001** | `APPROVED` | `master` | Gemini + Michał | Live smoke test snapshot-first z kamerą i Studio | 2026-06-01 | Test na żywo zakończony pełnym sukcesem (GREEN), potwierdzony po merge |
| **TASK-CV-GEOMETRY-FALLBACK-001** | `APPROVED` | `master` | Codex | MinAreaRect fallback, diagnostyka detekcji i filtr ArUco dla snapshot-first live | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |



---

## Statusy Zadań:
* `TODO` — Zadanie zaplanowane, oczekuje na realizację.
* `IN_PROGRESS` — Zadanie jest w trakcie aktywnej realizacji przez przypisanego agenta AI.
* `DONE` — Prace kodowe zostały zakończone i zweryfikowane lokalnie.
* `APPROVED` — Zadanie pomyślnie przeszło review i zostało scalone z gałęzią główną (`master`).
