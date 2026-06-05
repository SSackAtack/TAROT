# TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001

## Goal

Wykonac Research Gate dla Stage 6 Card Identification w izolowanym offline labie state-first.

Stage 6 ma przygotowac shortlistę metod do przyszlego benchmarku identyfikacji kart na cropach zaakceptowanych albo ostrzezonych przez Stage 5.

## Scope

Dozwolone:

- dokumentacja researchu Stage 6,
- analiza metod klasycznych CPU-only,
- opis wymagan reference deck i ground truth,
- aktualizacja `.ai/TASKS_INDEX.md`,
- utworzenie planu Stage 6 w `docs/superpowers/plans/`.

## Out of Scope

Niedozwolone:

- implementacja benchmarku Stage 6,
- implementacja card identification code,
- zmiany `tools/cv_detection_lab/`,
- zmiany `app_cv/`,
- zmiany `app_ar/`,
- zmiany runtime, WebSocket, Studio UI albo SnapshotFirstPipeline,
- dodawanie nowych bibliotek,
- ML classifier, embedding model, OCR albo runtime integration.

## Files Allowed to Change

- `.ai/tasks/TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001/TASK.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001/STATE.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001/RESEARCH_REPORT.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-5-plan.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

## Acceptance Criteria

- Research report zawiera Candidate Techniques Matrix.
- Kazda metoda ma status `TEST_NOW`, `TEST_LATER`, `REJECT_FOR_NOW` albo `REQUIRES_APPROVAL`.
- Raport uwzglednia HP EliteBook 830 G6, state-first model, reference deck, ground truth, top-k, confidence, reject/unknown/ambiguous behavior.
- Raport rozroznia docelowy zakres RWS Major Arcana i aktualne live fixture / mozliwa inna talie.
- Raport zawiera proponowany benchmark Stage 6.
- Nie zmieniono kodu runtime ani offline lab.

## Tests Required

Automated tests: `NOT_RUN` — documentation-only research gate.

Manual verification: `git diff` reviewed manually.

## Reports Required

- `RESEARCH_REPORT.md`
- `STATE.md`
- `CHANGELOG.md`
- `TEST_REPORT.md`

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`

## Commit Message

`docs: przygotuj research stage6 card identification`
