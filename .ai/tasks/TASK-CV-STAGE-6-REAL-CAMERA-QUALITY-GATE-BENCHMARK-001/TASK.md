# TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-BENCHMARK-001

## Goal

Zaimplementować offline benchmark zatwierdzonego quality gate Stage 6.

## Scope

- `local_specular_component_ratio`,
- `highlight_occlusion_ratio`,
- `usable_detail_ratio`,
- decyzje ACCEPT / RETRY / MANUAL_REVIEW,
- wymagane metryki i review pack z maską highlightu.

## Out of Scope

- runtime integration i runtime thresholds,
- zmiany `app_cv/main.py`, `app_cv/tarotvision/*`, `app_ar/*`.

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`
