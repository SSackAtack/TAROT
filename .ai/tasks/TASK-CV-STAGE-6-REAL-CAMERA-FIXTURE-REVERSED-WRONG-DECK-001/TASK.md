# TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001

## Goal

Przygotować offline tooling i procedurę operatorską do zebrania oraz
zwalidowania szerszego real-camera fixture Stage 6 w modelu:

```text
multiple immutable capture sessions
+
single offline aggregate validation manifest
```

## Scope

- agregujący `manifest.json`,
- `ground_truth.json`,
- stabilne `sample_id`,
- offline preflight manifestu, ground truth i sesji capture,
- generator manual review pack,
- dokumentacja operatorska tworzenia i agregowania sesji,
- minimum 28 real-camera samples:
  - 6 Gilded upright,
  - te same 6 Gilded reversed,
  - 4 Magic wrong-deck,
  - 4 Marchetti wrong-deck,
  - 4 trudne Gilded YELLOW,
  - 2 grupy visually similar po minimum 2 karty.

## Out of Scope

- zmiany `app_cv/main.py`,
- zmiany `app_cv/tarotvision/*`,
- zmiany `app_ar/*`,
- zmiany mechanizmu live fixture capture,
- runtime thresholdy,
- integracja ORB/AKAZE z runtime,
- automatyczne zbieranie obrazów bez operatora,
- deklarowanie zgody na runtime integration.

## Files Allowed to Change

- `tools/cv_detection_lab/stage6_real_camera_fixture.py`
- `tools/cv_detection_lab/stage6_real_camera_preflight.py`
- `tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py`
- `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py`
- `docs/operator/stage6_real_camera_fixture_capture.md`
- `docs/superpowers/plans/2026-06-04-stage-6-real-camera-fixture-implementation-plan.md`
- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001/*`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`
- local ignored fixture/output paths under `logs/live_fixtures/` and `logs/offline_replay/`

## Acceptance Criteria

- Preflight blocks duplicate `sample_id`.
- Preflight blocks any session referenced by more than one aggregate sample.
- Preflight verifies that each session and required capture file exists.
- Preflight verifies manifest/ground-truth one-to-one consistency.
- Preflight validates upright, reversed, wrong-deck, YELLOW and visually similar categories.
- Wrong-deck requires `expected_behavior: reject`.
- Reversed requires `expected_orientation: reversed`.
- Every ground-truth label requires `label_status: manual_confirmed`.
- Preflight verifies the minimum 28-sample matrix.
- Preflight proves session files were not modified during execution.
- Manual review pack is generated exclusively from the aggregate manifest.
- Manual review pack contains one debug sheet per sample and category/similarity indexes.
- No runtime files change.

## Tests Required

- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v`
- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v`
- `python -B -m py_compile tools/cv_detection_lab/stage6_real_camera_fixture.py tools/cv_detection_lab/stage6_real_camera_preflight.py tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py`
- `python -m unittest discover -s app_cv/tests -v`

## Reports Required

- `logs/offline_replay/stage6_real_camera_validation/preflight_report.json`
- `logs/offline_replay/stage6_real_camera_validation/preflight_report.md`
- `logs/offline_replay/stage6_real_camera_validation/manual_review_pack/`
- task `STATE.md`, `CHANGELOG.md`, `TEST_REPORT.md`

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`

## Commit Message

`feat: dodaj offline tooling real-camera fixture stage6`

## Plan Review Status

`APPROVED_BY_CHATGPT_SUPERVISOR`
