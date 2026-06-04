# TASK-CV-STAGE-6-REAL-CAMERA-ERROR-ANALYSIS-001

## Goal

Przeanalizować błędne próbki ORB z zatwierdzonego real-camera benchmarku Stage 6.

## Scope

- błędy Top-1 i Top-3,
- analiza per category, YELLOW i visually similar,
- porównanie extracted crop z oczekiwaną i przewidywaną referencją,
- paczka review zawierająca `matrix.csv`, `report.json`, extracted crops i debug sheets,
- offline-only.

## Files Allowed to Change

- `tools/cv_detection_lab/stage6_real_camera_error_analysis.py`
- `app_cv/tests/test_cv_detection_lab_stage6_real_camera_error_analysis.py`
- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-ERROR-ANALYSIS-001/*`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

## Out of Scope

- runtime threshold i runtime integration,
- `app_cv/main.py`,
- `app_cv/tarotvision/*`,
- `app_ar/*`.

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`
