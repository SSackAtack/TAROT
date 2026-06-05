# TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001

## Goal

Wykonać Research Gate dla Stage 3 nowego izolowanego offline labu state-first:

```text
Card Localization / Geometry Extraction
```

Stage 3 ma przygotować metody do przyszłego benchmarku, który z regionu kandydata Stage 2 wyznaczy właściwą geometrię fizycznej karty.

## Scope

Dozwolone:

- przygotowanie raportu badawczego Stage 3,
- wskazanie shortlisty `TEST_NOW`,
- aktualizacja `.ai/TASKS_INDEX.md`,
- aktualizacja planu Stage 2,
- utworzenie planu Stage 3.

## Out of Scope

Zakazane:

- zmiany `tools/cv_detection_lab/*`,
- zmiany `app_cv/*`,
- zmiany `app_ar/*`,
- implementacja benchmarku Stage 3,
- cropowanie, deskew, identyfikacja kart,
- state manager,
- integracja runtime.

## Files Allowed to Change

- `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/TASK.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/STATE.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/RESEARCH_REPORT.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-2-plan.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-3-plan.md`

## Acceptance Criteria

- Istnieje katalog taska Stage 3.
- `RESEARCH_REPORT.md` zawiera Candidate Techniques Matrix.
- Każda metoda ma status `TEST_NOW`, `TEST_LATER`, `REJECT_FOR_NOW` albo `REQUIRES_APPROVAL`.
- Raport uwzględnia HP EliteBook 830 G6 i model state-first.
- Raport jasno mówi, że Stage 3 nie robi cropowania, deskew ani identyfikacji.
- Raport zawiera proponowany benchmark Stage 3.
- Nie zmieniono kodu runtime ani offline lab.

## Tests Required

```text
Automated tests: NOT_RUN — documentation-only research gate.
Manual verification: git diff reviewed manually.
```

## Reports Required

- `RESEARCH_REPORT.md`
- `STATE.md`
- `CHANGELOG.md`
- `TEST_REPORT.md`

## Branch

```text
task/cv-event-first-plan-001-clarify-autotune-runtime
```

## Commit Message

```text
docs: przygotuj research stage3 card localization
```
