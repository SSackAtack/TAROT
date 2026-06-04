# TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001

## Goal

Wykonac Research Gate dla Stage 5 nowego izolowanego offline labu state-first:

```text
Crop Quality Validation
```

Stage 5 ma przygotowac metryki i zasady oceny, czy crop wygenerowany przez zatwierdzony Stage 4 jest jakosciowo gotowy jako wejscie do przyszlego Stage 6 Card Identification.

## Scope

Dozwolone:

- utworzenie dokumentacji taska w `.ai/tasks/TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001/`
- aktualizacja `.ai/TASKS_INDEX.md`
- aktualizacja `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-4-plan.md`
- utworzenie `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-5-plan.md`

## Out of Scope

Zakazane:

- implementacja benchmarku Stage 5
- implementacja kodu quality validation
- identyfikacja kart
- ORB / FLANN / template matching / OCR
- zmiany runtime, `SnapshotFirstPipeline`, `ChangeDetector`, ArUco, WebSocket i Studio UI
- zmiany w `app_cv/`, `app_ar/` oraz `tools/cv_detection_lab/`
- nowe zaleznosci

## Files Allowed to Change

- `.ai/tasks/TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001/TASK.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001/STATE.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001/RESEARCH_REPORT.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-4-plan.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-5-plan.md`

## Acceptance Criteria

- Istnieje `RESEARCH_REPORT.md` z Candidate Techniques Matrix.
- Kazda metoda/metryka ma status `TEST_NOW`, `TEST_LATER`, `REJECT_FOR_NOW` albo `REQUIRES_APPROVAL`.
- Raport uwzglednia ograniczenia HP EliteBook 830 G6 i CPU-only.
- Raport uwzglednia model state-first oraz regule `removed -> previous_snapshot`.
- Raport jasno zaznacza, ze Stage 5 nie identyfikuje kart.
- Raport oddziela Crop Quality Validation od Card Identification.
- Raport zawiera proponowany benchmark Stage 5.
- Nie zmieniono kodu runtime ani offline labu.
- `TEST_REPORT.md` jasno mowi `NOT_RUN` dla automated tests.
- `.ai/TASKS_INDEX.md` jest zaktualizowany.

## Tests Required

Automated tests:

```text
NOT_RUN
```

Uzasadnienie:

```text
documentation-only research gate
```

Manual verification:

```text
git diff reviewed manually
```

## Reports Required

- `STATE.md`
- `CHANGELOG.md`
- `TEST_REPORT.md`
- `RESEARCH_REPORT.md`

## Branch

```text
task/cv-event-first-plan-001-clarify-autotune-runtime
```

## Commit Message

```text
docs: przygotuj research stage5 crop quality
```
