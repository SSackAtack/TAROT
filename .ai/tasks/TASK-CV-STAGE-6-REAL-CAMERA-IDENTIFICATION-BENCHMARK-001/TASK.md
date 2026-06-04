# TASK-CV-STAGE-6-REAL-CAMERA-IDENTIFICATION-BENCHMARK-001

## Goal

Uruchomić offline-only benchmark ORB i AKAZE na zatwierdzonym real-camera fixture Stage 6.

## Scope

- Identyfikacja na 28 zatwierdzonych próbkach real-camera.
- Metryki upright, reversed, wrong-deck, YELLOW i visually similar.
- Wrong-deck FAR z progiem wyłącznie walidacyjnym.
- Lokalny runtime proxy.
- Brak zmian runtime.

## Files Allowed to Change

- `tools/cv_detection_lab/stage6_real_camera_identification_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage6_real_camera_identification.py`
- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-IDENTIFICATION-BENCHMARK-001/*`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

## Out of Scope

- `app_cv/main.py`
- `app_cv/tarotvision/*`
- `app_ar/*`
- runtime thresholds i integracja runtime

## Acceptance Criteria

- ORB i AKAZE przetwarzają ten sam zatwierdzony fixture.
- Raport zawiera Top-1, Top-3, wrong-deck FAR, kategorie, similarity groups i runtime proxy.
- Benchmark nie modyfikuje sesji capture.
- Wynik pozostaje offline-only.

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`
