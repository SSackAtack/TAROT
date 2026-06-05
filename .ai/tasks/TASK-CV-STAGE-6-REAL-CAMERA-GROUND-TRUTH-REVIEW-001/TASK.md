# TASK-CV-STAGE-6-REAL-CAMERA-GROUND-TRUTH-REVIEW-001

## Goal

Ręcznie rozstrzygnąć podejrzaną etykietę próbki `f8d6d84b5ddb5729fa07`
i ponownie przeliczyć offline benchmark Stage 6.

## Scope

- wizualne porównanie cropu z `Gilded_45` i `Gilded_67`,
- korekta lokalnego manifestu i ground truth fixture,
- preflight,
- ponowny benchmark i error analysis,
- nowe metryki offline-only.

## Decision

Crop jednoznacznie przedstawia `Gilded_67` (Cesarz), nie `Gilded_45`
(Sprawiedliwość).

## Out of Scope

- runtime thresholds i runtime integration,
- `app_cv/main.py`,
- `app_cv/tarotvision/*`,
- `app_ar/*`.

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`
