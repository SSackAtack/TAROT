# State-First Offline Lab Stage 4 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
Stage 3 approved: hybrid_edge_plus_contour.
```

Next gate: Stage 4 Crop / Deskew / Normalize research.
Stage 4 benchmark must not begin until Supervisor accepts TEST_NOW shortlist.

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
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001`: implementacja benchmarku po akceptacji shortlisty.

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

## Kolejne kroki

Natychmiastowy następny krok dla kolejnego modelu: przekazać shortlistę `TEST_NOW` Supervisorowi. Po akceptacji dopiero wtedy utworzyć i zaimplementować offline benchmark Stage 4 w izolowanym `tools/cv_detection_lab/`, bez zmian runtime.
