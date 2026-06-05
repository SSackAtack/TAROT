# TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001

## Goal

Wykonac Research Gate dla Stage 4 nowego izolowanego offline labu state-first:

```text
Crop / Deskew / Normalize
```

Stage 4 ma zbadac, jak z geometrii Stage 3 uzyskac stabilny, nieuciety i znormalizowany obraz karty jako wejscie do przyszlego Stage 5 Crop Quality Validation oraz Stage 6 Card Identification.

## Scope

Dozwolone:

- utworzenie dokumentacji taska w `.ai/tasks/TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001/`
- aktualizacja `.ai/TASKS_INDEX.md`
- aktualizacja planu Stage 3
- opcjonalne utworzenie planu Stage 4

## Out of Scope

Zakazane:

- implementacja benchmarku Stage 4
- cropowanie kart
- deskew / perspective transform w kodzie
- normalizacja obrazu w kodzie
- walidacja jakosci cropa
- identyfikacja kart
- integracja runtime
- zmiany `tools/cv_detection_lab/`
- zmiany `app_cv/`
- zmiany `app_ar/`
- nowe zaleznosci

## Files Allowed to Change

- `.ai/tasks/TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001/TASK.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001/STATE.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001/RESEARCH_REPORT.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-3-plan.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-4-plan.md`

## Acceptance Criteria

- Istnieje `RESEARCH_REPORT.md` z Candidate Techniques Matrix.
- Kazda metoda ma status `TEST_NOW`, `TEST_LATER`, `REJECT_FOR_NOW` albo `REQUIRES_APPROVAL`.
- Raport uwzglednia ograniczenia HP EliteBook 830 G6 i CPU-only.
- Raport uwzglednia model state-first oraz regule `removed -> previous_snapshot`.
- Raport jasno oddziela Stage 4 od Stage 5, Stage 6 i runtime.
- Raport zawiera proponowany benchmark Stage 4.
- Nie zmieniono kodu runtime ani offline labu.

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
docs: przygotuj research stage4 crop deskew normalize
```
