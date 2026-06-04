# State-First Offline Lab Stage 5 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
Stage 3 approved: hybrid_edge_plus_contour.
Stage 4 approved: quad_warp_perspective_fixed_aspect__resize_only_normalization.
```

Stage 5 benchmark has been implemented and run. Result is `PROVISIONAL_RECOMMENDED`.

Stage 6 must not begin until Supervisor reviews Stage 5 crop quality debug sheets.

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
- [x] `TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001`: implementacja benchmarku — DONE, 6 rows, recommended: `quality_metric_suite_v1`.

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

Natychmiastowy następny krok dla kolejnego modelu: wykonać manual review crop quality debug sheets:

```text
logs/offline_replay/stage5_crop_quality_validation/quality_metric_suite_v1/*/crop_quality_debug_sheet.png
```

Nie rozpoczynać Stage 6 przed tą decyzją.

## Session Status (2026-06-04 Codex Stage 5 Benchmark)

Stan aktualny: zaimplementowano i uruchomiono izolowany offline benchmark Stage 5 Crop Quality Validation.

Co zostało zrobione: dodano `crop_quality_methods.py`, `stage5_crop_quality_validation_benchmark.py` oraz testy `test_cv_detection_lab_stage5.py`. Benchmark korzysta z `gray_absdiff_gaussian`, `contour_external`, `hybrid_edge_plus_contour` i `quad_warp_perspective_fixed_aspect__resize_only_normalization`, generuje `matrix.csv`, `report.json`, `report.md`, `crop_quality_debug_sheet.png`, `crop_XX_quality_overlay.png` i `crop_XX_metrics.json`.

Wynik: `quality_metric_suite_v1` jest `PROVISIONAL_RECOMMENDED`, `threshold_status=BENCHMARK_HEURISTIC_ONLY`, `rows=6`. `empty_to_empty` ma `PASS`, a pary z kartami maja `YELLOW`, przy poprawnych liczbach cropow i poprawnym `previous` dla `removed`.

Weryfikacja: 11 testow Stage 5 PASS, 34 testy regresji Stage 1-4 PASS, py_compile PASS, benchmark CLI PASS, full backend suite 361 testow PASS.

Kolejne kroki: Supervisor powinien recznie sprawdzic crop quality debug sheets. Nie rozpoczynac Stage 6 przed review.

## Stage 5 Final Decision

Decision:

APPROVED_STAGE_5_METHOD: quality_metric_suite_v1

Reason:

Metoda poprawnie przeszła benchmark, foreground/margin fix, YELLOW/FAIL reason fix oraz manualny crop quality debug review na parach:

- `empty -> empty`
- `empty -> one_card`
- `empty -> three_cards`
- `one_card -> three_cards`
- `one_card -> empty`
- `three_cards -> empty`

Scope:

Stage 5 approval covers Crop Quality Validation only.

Approved method:

- `quality_metric_suite_v1`

Approved output:

- `crop_quality_status`
- `crop_quality_score`
- `identification_readiness_score`
- `quality_flags`
- `warning_reason`
- `reject_reason`
- `quality_metrics`
- `crop_quality_debug_sheet`

Important limitation:

Stage 5 does not approve card identification, ORB / FLANN, OCR, template matching, runtime thresholds or runtime integration.

Observation:

All real crop samples in the current fixture are `YELLOW`, not `PASS`. Stage 6 must assume medium-quality crop input.

Next stage:

TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001
