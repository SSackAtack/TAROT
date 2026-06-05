# TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-DESIGN-001

## Goal

Zaprojektować offline-only quality gate dla Stage 6, który wykrywa cropy
wymagające ponownego capture przed identyfikacją.

## Scope

- glare / specular highlight,
- kontrast i detal,
- sanity checks obszaru i krawędzi karty,
- sygnał `RETRY_CAPTURE`,
- projekt benchmarku offline-only.

## Out of Scope

- implementacja runtime,
- finalne progi,
- zmiany `app_cv/main.py`, `app_cv/tarotvision/*`, `app_ar/*`,
- automatyczne ponowienie capture.

## Files Allowed to Change

- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-DESIGN-001/*`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-04-stage-6-real-camera-quality-gate-design.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`
