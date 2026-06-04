# TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001

## Goal

Zaimplementować deterministyczny synthetic validation benchmark porównujący
`orb_bfmatcher_ratio_test` z `akaze_bfmatcher` przed jakąkolwiek integracją runtime.

## Scope

- 24 równomiernie wybrane karty Gilded.
- Upright, reversed i pięć trudniejszych kategorii transformacji.
- Po 12 wrong-deck samples z talii Magic i Marchetti.
- Manifest reprodukowalności.
- Metryki per method, category i orientation.
- Offline-only wrong-deck rejection threshold.
- Lokalny pomiar runtime jako proxy.
- Raporty i przykładowe debug sheety.

## Out of Scope

- `app_cv/tarotvision/*`
- `app_cv/main.py`
- `app_ar/*`
- integracja runtime,
- strojenie lub zapis runtime thresholdów,
- commitowanie pełnego syntetycznego datasetu,
- deklarowanie lokalnego wyniku jako pomiaru HP EliteBook 830 G6.

## Files Allowed to Change

- `tools/cv_detection_lab/stage6_synthetic_dataset.py`
- `tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001/*`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-04-stage-6-synthetic-validation-benchmark-implementation-plan.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

Existing Stage 6 identification method files may only be changed after explicit
owner approval if a verified blocking defect is found.

## Acceptance Criteria

- Fixed seed and stable sample IDs reproduce the same manifest.
- Manifest records source card, source deck, category, orientation and transform parameters.
- Dataset contains 168 known Gilded samples and 24 wrong-deck samples.
- ORB and AKAZE run against the same sample set and full Gilded reference deck.
- `matrix.csv` contains one row per method and sample, including category and orientation.
- Reports include aggregate and `method + category + orientation` metrics.
- Reports include wrong-deck false-accept rate using an offline-only threshold.
- Reports include mean, p50 and p95 local-proxy runtime.
- Debug sheets exist for upright, reversed, `yellow_combined` and wrong-deck.
- No runtime files change.

## Tests Required

- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v`
- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_preflight -v`
- `python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 app_cv.tests.test_cv_detection_lab_stage4 app_cv.tests.test_cv_detection_lab_stage5 -v`
- `python -B -m py_compile tools/cv_detection_lab/stage6_synthetic_dataset.py tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py`
- `python -m unittest discover -s app_cv/tests -v`

## Reports Required

- `logs/offline_replay/stage6_validation_benchmark/manifest.json`
- `logs/offline_replay/stage6_validation_benchmark/matrix.csv`
- `logs/offline_replay/stage6_validation_benchmark/report.json`
- `logs/offline_replay/stage6_validation_benchmark/report.md`
- representative debug sheets
- task `STATE.md`, `CHANGELOG.md` and `TEST_REPORT.md`

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`

## Commit Message

`feat: dodaj syntetyczny benchmark walidacyjny stage6`

## Plan Review Status

`PENDING_SUPERVISOR_REVIEW`
