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

## TASK-CV-OFFLINE-LAB-STAGE-5-MANUAL-REVIEW-PACK-001

### Summary

Prepared the Stage 5 manual review pack after Supervisor accepted the foreground/margin fix.

### Output

```text
logs/offline_replay/stage5_crop_quality_validation/manual_review_pack_quality_metric_suite_v1/
```

### Files

```text
empty_to_empty.crop_quality_debug_sheet.png
empty_to_one_card.crop_quality_debug_sheet.png
empty_to_three_cards.crop_quality_debug_sheet.png
one_card_to_three_cards.crop_quality_debug_sheet.png
one_card_to_empty.crop_quality_debug_sheet.png
three_cards_to_empty.crop_quality_debug_sheet.png
```

### Decision

Stage 5 is still not approved in repo. The manual review pack is ready for Michal.

### Required next action

Michal reviews all 6 debug sheets and decides whether to record:

```text
APPROVED_STAGE_5_METHOD: quality_metric_suite_v1
```

## TASK-CV-OFFLINE-LAB-STAGE-5-YELLOW-REASON-FIX-001

### Summary

Improved Stage 5 diagnostics so YELLOW / FAIL crop quality results include an explicit reason.

### Problem

Manual review showed real crop quality debug sheets with `status=YELLOW` and `flags=none`, which made Stage 5 diagnostically weak.

### Fix

Stage 5 now adds benchmark-only diagnostic flags for low score/readiness/sharpness/contrast/detail conditions.

### Verification

Stage 5 tests, Stage 1-4 regressions, py_compile, Stage 5 benchmark CLI and full backend suite passed. Regenerated real benchmark JSON output no longer has non-PASS crop results without `quality_flags`, `warning_reason` or `reject_reason`.

### Decision

Stage 5 remains `PROVISIONAL_RECOMMENDED`.

### Required next action

Supervisor reviews regenerated Stage 5 debug sheets before any Stage 5 approval decision.

## TASK-CV-OFFLINE-LAB-STAGE-5-DECISION-001

### Supervisor Manual Review

Manualnie przejrzano zaktualizowane crop quality debug sheets dla metody:

`quality_metric_suite_v1`

Pary testowe:

- `empty_to_empty`
- `empty_to_one_card`
- `empty_to_three_cards`
- `one_card_to_three_cards`
- `one_card_to_empty`
- `three_cards_to_empty`

### Decision

APPROVED_STAGE_5_METHOD: quality_metric_suite_v1

### Scope of Approval

Zatwierdzenie dotyczy tylko Stage 5 Crop Quality Validation:

- ocena jakości cropów z zatwierdzonego Stage 4,
- statusy `PASS`, `YELLOW`, `FAIL`, `PASS_NO_CROPS`,
- `quality_flags`,
- `warning_reason` / `reject_reason`,
- `crop_quality_score`,
- `identification_readiness_score`,
- `threshold_status=BENCHMARK_HEURISTIC_ONLY`,
- obsługa par state-first `added`, `removed`, `no_change`.

### Known Limitation

Stage 5 nie zatwierdza jeszcze identyfikacji kart ani runtime thresholds.

Wszystkie realne cropy w aktualnym fixture mają status `YELLOW`, więc Stage 6 musi być projektowany z założeniem, że wejściowe cropy są używalne, ale jakościowo średnie.

### Required Next Action

Utworzyć:

TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001
