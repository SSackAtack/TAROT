# State-First Offline Lab Stage 5 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
Stage 3 approved: hybrid_edge_plus_contour.
Stage 4 approved: quad_warp_perspective_fixed_aspect__resize_only_normalization.
```

Next gate: Stage 5 Crop Quality Validation research.

Stage 5 benchmark must not begin until Supervisor accepts TEST_NOW shortlist.

## Session Status (2026-06-04 Codex)

Stan aktualny: przygotowano research summary dla Stage 5 Crop Quality Validation.

Co zostało zrobione: utworzono `TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001`, zapisano macierz kandydatów i wskazano shortlistę metryk `TEST_NOW`.

Kolejne kroki: Supervisor powinien zaakceptować albo skorygować shortlistę `TEST_NOW`. Po akceptacji należy utworzyć `TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001`.

## Co zostało zrobione

- [x] Potwierdzono wejście ze Stage 1: `gray_absdiff_gaussian`.
- [x] Potwierdzono wejście ze Stage 2: `contour_external`.
- [x] Potwierdzono wejście ze Stage 3: `hybrid_edge_plus_contour`.
- [x] Potwierdzono wejście ze Stage 4: `quad_warp_perspective_fixed_aspect__resize_only_normalization`.
- [x] Zidentyfikowano ograniczenie Stage 4: crop jest generowany, ale nie ma jeszcze automatycznej oceny jakości.
- [x] Przeanalizowano metryki ucięcia karty, marginesów, refleksów, ostrości, kontrastu, kompletności i gotowości do identyfikacji.
- [x] Wskazano shortlistę `TEST_NOW`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001`: Research Gate Stage 5 Crop Quality Validation.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001`: implementacja benchmarku po akceptacji shortlisty.

## Shortlista TEST_NOW

- `edge_cut_risk_score`
- `border_visible_score`
- `border_continuity_score`
- `corner_visibility_score`
- `missing_border_score`
- `card_edge_proximity_to_crop_edge`
- `card_fill_ratio_score`
- `background_margin_score`
- `top_margin_ratio_score`
- `side_margin_ratios`
- `overexposed_pixel_ratio`
- `underexposed_pixel_ratio`
- `top_reflection_score`
- `brightness_mean_score`
- `contrast_stddev_score`
- `histogram_spread_score`
- `dynamic_range_score`
- `variance_of_laplacian_blur_score`
- `tenengrad_sharpness_score`
- `edge_density_score`
- `texture_density_score`
- `internal_detail_score`
- `aspect_ratio_error_score`
- `crop_size_score`
- `crop_completeness_score`
- `identification_readiness_score`
- `composite_crop_quality_score`

## Kolejne kroki

Natychmiastowy następny krok dla kolejnego modelu: przekazać shortlistę `TEST_NOW` Supervisorowi.

Po akceptacji dopiero wtedy utworzyć i zaimplementować offline benchmark Stage 5 w izolowanym `tools/cv_detection_lab/`, bez zmian runtime, bez Studio i bez identyfikacji kart.
