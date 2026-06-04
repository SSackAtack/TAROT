# Stan Prac — TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001

## Summary

Implemented isolated Stage 5 Crop Quality Validation benchmark.

## Input

Stage 1 approved method: `gray_absdiff_gaussian`.

Stage 2 approved method: `contour_external`.

Stage 3 approved method: `hybrid_edge_plus_contour`.

Stage 4 approved pipeline: `quad_warp_perspective_fixed_aspect__resize_only_normalization`.

Fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

## Method tested

`quality_metric_suite_v1`

## Benchmark result

* rows: `6`
* recommended_method: `quality_metric_suite_v1`
* recommendation_status: `PROVISIONAL_RECOMMENDED`
* threshold_status: `BENCHMARK_HEURISTIC_ONLY`
* output path: `logs/offline_replay/stage5_crop_quality_validation/`

## Result summary

* `empty_to_empty`: `PASS`
* non-empty pairs: `YELLOW`
* crop counts matched expected counts for all 6 pairs
* `removed` pairs used `previous` as `crop_source_frame`

## Decision

`PROVISIONAL_RECOMMENDED` only.

Waiting for Supervisor manual review.

## Required next action

Upload / review crop quality debug sheets from:

```text
logs/offline_replay/stage5_crop_quality_validation/quality_metric_suite_v1/*/crop_quality_debug_sheet.png
```

Do not start Stage 6 before Supervisor review.

## TASK-CV-OFFLINE-LAB-STAGE-5-FOREGROUND-MARGIN-FIX-001

### Summary

Improved Stage 5 foreground/card-area estimation for crop margin metrics.

### Problem

The previous `_foreground_bbox()` could treat nearly the entire crop as foreground because it used a broad brightness condition. This weakened `top_margin_ratio`, `background_margin_score` and `card_fill_ratio`.

### Fix

Stage 5 now estimates foreground/card-like bbox using edge/gradient-supported mask and avoids treating all bright pixels as card foreground.

### Verification

Added regression tests for synthetic top margin and background margin behavior. Stage 5 tests, Stage 1-4 regressions, py_compile, Stage 5 benchmark CLI and full backend suite passed.

### Decision

Stage 5 remains `PROVISIONAL_RECOMMENDED`.

### Required next action

Supervisor review of this fix. Do not prepare Stage 5 manual review pack until the fix is approved.
