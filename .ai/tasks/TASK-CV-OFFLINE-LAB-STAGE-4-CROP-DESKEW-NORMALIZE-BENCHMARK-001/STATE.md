# Stan Prac — TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001

## Summary

Implemented isolated Stage 4 Crop / Deskew / Normalize benchmark.

## Input

Stage 1 approved method: `gray_absdiff_gaussian`.

Stage 2 approved method: `contour_external`.

Stage 3 approved method: `hybrid_edge_plus_contour`.

Fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

## Pipelines tested

| # | crop_method | normalization_variant | padding_ratio |
|---|---|---|---|
| 1 | bbox_crop_resize | resize_only_normalization | 0.0 |
| 2 | rotated_rect_warp_affine | resize_only_normalization | 0.0 |
| 3 | quad_warp_perspective | resize_only_normalization | 0.0 |
| 4 | quad_warp_perspective_with_safe_padding | resize_only_normalization | 0.03 |
| 5 | quad_warp_perspective_fixed_aspect | resize_only_normalization | 0.0 |
| 6 | quad_warp_perspective_keep_border_margin | resize_only_normalization | 0.03 |
| 7 | quad_warp_perspective_with_safe_padding | grayscale_normalization | 0.03 |
| 8 | quad_warp_perspective_with_safe_padding | clahe_normalization | 0.03 |
| 9 | quad_warp_perspective_with_safe_padding | brightness_contrast_normalization | 0.03 |
| 10 | quad_warp_perspective_with_safe_padding | orientation_portrait_normalization | 0.03 |

## Benchmark result

* rows: 60
* recommended_pipeline: `quad_warp_perspective_fixed_aspect__resize_only_normalization`
* recommendation_status: `PROVISIONAL_RECOMMENDED`
* output path: `logs/offline_replay/stage4_crop_deskew_normalize/`

## Decision

`PROVISIONAL_RECOMMENDED` only.

Waiting for Supervisor manual review.

## Required next action

Upload / review crop debug sheets from:

```text
logs/offline_replay/stage4_crop_deskew_normalize/quad_warp_perspective_fixed_aspect__resize_only_normalization/*/crop_debug_sheet.png
```

Do not start Stage 5 before Supervisor review.

## TASK-CV-OFFLINE-LAB-STAGE-4-REVIEW-PATHS-FIX-001

### Summary

Fixed Stage 4 manual review output completeness.

### Problem

`manual_review_paths` included `empty_to_empty/crop_debug_sheet.png`, but no sheet was generated when crop_count was 0.

### Fix

Benchmark now writes placeholder `crop_debug_sheet.png` for no-crop pairs.

### Decision

Stage 4 remains `PROVISIONAL_RECOMMENDED`.

### Required next action

Prepare Stage 4 manual review pack after Supervisor confirms this fix.

## TASK-CV-OFFLINE-LAB-STAGE-4-MANUAL-REVIEW-PACK-001

### Summary

Prepared local manual review pack for Stage 4 `quad_warp_perspective_fixed_aspect__resize_only_normalization` crop debug sheets.

### Files prepared locally

- `logs/offline_replay/stage4_manual_review_pack/quad_warp_perspective_fixed_aspect__resize_only_normalization/01_empty_to_empty_crop_debug_sheet.png`
- `logs/offline_replay/stage4_manual_review_pack/quad_warp_perspective_fixed_aspect__resize_only_normalization/02_empty_to_one_card_crop_debug_sheet.png`
- `logs/offline_replay/stage4_manual_review_pack/quad_warp_perspective_fixed_aspect__resize_only_normalization/03_empty_to_three_cards_crop_debug_sheet.png`
- `logs/offline_replay/stage4_manual_review_pack/quad_warp_perspective_fixed_aspect__resize_only_normalization/04_one_card_to_three_cards_crop_debug_sheet.png`
- `logs/offline_replay/stage4_manual_review_pack/quad_warp_perspective_fixed_aspect__resize_only_normalization/05_one_card_to_empty_crop_debug_sheet.png`
- `logs/offline_replay/stage4_manual_review_pack/quad_warp_perspective_fixed_aspect__resize_only_normalization/06_three_cards_to_empty_crop_debug_sheet.png`
- `logs/offline_replay/stage4_manual_review_pack/README_FOR_SUPERVISOR.md`
- `logs/offline_replay/stage4_manual_review_pack_quad_warp_perspective_fixed_aspect.zip`

### Tests

No algorithmic tests required. Packaging only.

Verification:

- confirmed all 6 PNG files exist
- confirmed `empty_to_empty` placeholder exists
- confirmed README exists
- confirmed ZIP exists

### Decision

Stage 4 still `PROVISIONAL_RECOMMENDED`.

Waiting for Supervisor visual review.

### Required next action

Michał uploads the six PNG crop debug sheets to ChatGPT Supervisor for manual Stage 4 review.

## TASK-CV-OFFLINE-LAB-STAGE-4-DECISION-001

### Supervisor Manual Review

Manualnie przejrzano crop debug sheets dla pipeline:

`quad_warp_perspective_fixed_aspect__resize_only_normalization`

Pary testowe:

- `empty_to_empty`
- `empty_to_one_card`
- `empty_to_three_cards`
- `one_card_to_three_cards`
- `one_card_to_empty`
- `three_cards_to_empty`

### Decision

APPROVED_STAGE_4_PIPELINE: quad_warp_perspective_fixed_aspect__resize_only_normalization

### Scope of Approval

Zatwierdzenie dotyczy tylko Stage 4 Crop / Deskew / Normalize:

- generowanie cropów z geometrii Stage 3,
- fixed aspect perspective crop,
- resize-only normalization jako bezpieczny baseline,
- poprawna liczba cropów dla `added`, `removed` i `no_change`,
- poprawne użycie `previous_snapshot` dla `removed`,
- poprawne działanie w modelu kaskadowym `one_card -> three_cards`,
- przygotowanie cropów wejściowych dla przyszłego Stage 5.

### Known Limitation

Stage 4 nie zatwierdza jeszcze automatycznej walidacji jakości cropa ani identyfikacji kart.

Stage 5 musi dopiero ocenić jakość cropów, m.in.:

- `edge_cut_risk`
- `background_margin_score`
- `border_visible_score`
- `top_reflection_score`
- `blur_score`
- `contrast_score`
- `brightness_score`
- `card_fill_ratio`
- `crop_completeness_score`
- `identification_readiness_score`

### Required Next Action

Utworzyć:

TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001
