# State-First Offline Lab Stage 3 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
```

Next gate: Stage 3 Card Localization research.
Stage 3 benchmark must not begin until Supervisor accepts TEST_NOW shortlist.

## Session Status (2026-06-03 Codex)

Stan aktualny: przygotowano research summary dla Stage 3 Card Localization / Geometry Extraction.

Co zostało zrobione: zapisano macierz kandydatów w `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/RESEARCH_REPORT.md`, wskazano shortlistę `TEST_NOW` i zablokowano benchmark do czasu decyzji Supervisora.

Kolejne kroki: Supervisor powinien zaakceptować albo skorygować shortlistę `TEST_NOW`.

## Co zostało zrobione

- [x] Potwierdzono wejście ze Stage 1: `gray_absdiff_gaussian`.
- [x] Potwierdzono wejście ze Stage 2: `contour_external`.
- [x] Zidentyfikowano ograniczenie Stage 2: bbox regionu kandydata nie jest finalną geometrią karty.
- [x] Przeanalizowano kontury, `approxPolyDP`, `minAreaRect`, edge-supported bbox, Hough/LSD lines, corner evidence i scoring borderów.
- [x] Wskazano shortlistę `TEST_NOW`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001`: Research Gate Stage 3 Card Localization / Geometry Extraction.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001`: implementacja benchmarku po akceptacji shortlisty.

## Shortlista TEST_NOW

- `contour_largest_inside_candidate`
- `approx_poly_dp_quad`
- `min_area_rect_candidate`
- `bounding_rect_tight`
- `edge_supported_bbox`
- `border_evidence_scoring`
- `projection_profile_tight_bbox`
- `corner_detection_good_features`
- `hybrid_contour_plus_min_area_rect`
- `hybrid_edge_plus_contour`

## Kolejne kroki

Natychmiastowy następny krok dla kolejnego modelu: przekazać shortlistę `TEST_NOW` Supervisorowi. Po akceptacji dopiero wtedy utworzyć i zaimplementować offline benchmark Stage 3 w izolowanym `tools/cv_detection_lab/`, bez zmian runtime.
