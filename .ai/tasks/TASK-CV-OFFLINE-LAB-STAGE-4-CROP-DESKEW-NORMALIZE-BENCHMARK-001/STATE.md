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
