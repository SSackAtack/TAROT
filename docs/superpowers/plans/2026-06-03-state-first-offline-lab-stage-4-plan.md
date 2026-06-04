# State-First Offline Lab Stage 4 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
Stage 3 approved: hybrid_edge_plus_contour.
```

Stage 4 final decision:

```text
APPROVED_STAGE_4_PIPELINE: quad_warp_perspective_fixed_aspect__resize_only_normalization
```

Next gate: `TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001`.

## Session Status (2026-06-03 Codex)

Stan aktualny: przygotowano research summary dla Stage 4 Crop / Deskew / Normalize.

Co zostało zrobione: utworzono `TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001`, zapisano macierz kandydatów i wskazano shortlistę `TEST_NOW`.

Kolejne kroki: Supervisor powinien zaakceptować albo skorygować shortlistę `TEST_NOW`. Po akceptacji należy utworzyć `TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001`.

## Co zostało zrobione

- [x] Potwierdzono wejście ze Stage 1: `gray_absdiff_gaussian`.
- [x] Potwierdzono wejście ze Stage 2: `contour_external`.
- [x] Potwierdzono wejście ze Stage 3: `hybrid_edge_plus_contour`.
- [x] Zidentyfikowano ograniczenie Stage 3: geometria nie gwarantuje jeszcze poprawnego cropa.
- [x] Przeanalizowano bbox crop, rotated rect warp affine, quad perspective warp, safe padding, target aspect ratio i normalizację obrazu.
- [x] Wskazano shortlistę `TEST_NOW`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001`: Research Gate Stage 4 Crop / Deskew / Normalize.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001`: implementacja benchmarku — DONE, 60 rows, recommended: `quad_warp_perspective_fixed_aspect`.

## Shortlista TEST_NOW

- `bbox_crop_resize`
- `rotated_rect_warp_affine`
- `quad_warp_perspective`
- `quad_warp_perspective_with_safe_padding`
- `quad_warp_perspective_fixed_aspect`
- `quad_warp_perspective_keep_border_margin`
- `resize_only_normalization`
- `grayscale_normalization`
- `clahe_normalization`
- `brightness_contrast_normalization`
- `orientation_portrait_normalization`

## Session Status (2026-06-04 Gemini Stage 4 Benchmark)

Stan aktualny: zaimplementowano i uruchomiono izolowany offline benchmark Stage 4 Crop / Deskew / Normalize.

Co zostało zrobione: dodano `crop_deskew_methods.py`, `stage4_crop_deskew_normalize_benchmark.py` oraz testy `test_cv_detection_lab_stage4.py`. Benchmark korzysta z `gray_absdiff_gaussian`, `contour_external` i `hybrid_edge_plus_contour`, generuje `matrix.csv`, `report.json`, `report.md` oraz crop debug sheets per pipeline variant i para fixture.

Wynik: `quad_warp_perspective_fixed_aspect__resize_only_normalization` jest `PROVISIONAL_RECOMMENDED` z kompletem 60 wierszy macierzy. Wszystkie 9 testów Stage 4 PASS, 23 testy Stage 1-3 PASS, 348 testów full backend PASS.

Kolejne kroki: Supervisor powinien ręcznie sprawdzić crop debug sheets:

```text
logs/offline_replay/stage4_crop_deskew_normalize/quad_warp_perspective_fixed_aspect__resize_only_normalization/*/crop_debug_sheet.png
```

Nie rozpoczynać Stage 5 przed tą decyzją.

## Stage 4 Final Decision

Decision:

APPROVED_STAGE_4_PIPELINE: quad_warp_perspective_fixed_aspect__resize_only_normalization

Reason:

Pipeline poprawnie przeszedł benchmark i manualny crop debug review na parach:

- `empty -> empty`
- `empty -> one_card`
- `empty -> three_cards`
- `one_card -> three_cards`
- `one_card -> empty`
- `three_cards -> empty`

Scope:

Stage 4 approval covers Crop / Deskew / Normalize only.

Approved pipeline:

- crop method: `quad_warp_perspective_fixed_aspect`
- normalization: `resize_only_normalization`

Approved output:

- `raw_crop`
- `deskewed_crop`
- `normalized_crop`
- `crop_metadata`
- `crop_transform_matrix`
- `crop_debug_sheet`

Important limitation:

Stage 4 does not approve automatic crop quality validation, card identification or runtime integration.

Next stage:

TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001

## Session Status (2026-06-04 Codex Stage 5 Research Gate)

Stan aktualny: Stage 1 approved: `gray_absdiff_gaussian`. Stage 2 approved: `contour_external`. Stage 3 approved: `hybrid_edge_plus_contour`. Stage 4 approved: `quad_warp_perspective_fixed_aspect__resize_only_normalization`. Next gate: Stage 5 Crop Quality Validation research.

Co zostało zrobione: utworzono `TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001` i zapisano shortlistę metryk jakości cropa do decyzji Supervisora. Nie zmieniono `tools/cv_detection_lab/`, runtime, Studio ani frontendu.

Kolejne kroki: Stage 5 benchmark must not begin until Supervisor accepts TEST_NOW shortlist. Po akceptacji należy utworzyć `TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001`.
