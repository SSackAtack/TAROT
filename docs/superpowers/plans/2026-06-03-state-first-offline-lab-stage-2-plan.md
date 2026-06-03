# State-First Offline Lab Stage 2 Plan

## Status ogólny

Stage 1 Difference Detection jest zatwierdzony:

```text
APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
```

Stage 2 pozostaje na etapie Research Gate. Benchmark Stage 2 nie został jeszcze uruchomiony ani zaimplementowany.

## Session Status (2026-06-03 Codex)

Stan aktualny: przygotowano research summary dla Stage 2 Region Segmentation / Region Refinement.

Co zostało zrobione: zapisano macierz kandydatów w `.ai/tasks/TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001/RESEARCH_REPORT.md`, wskazano shortlistę `TEST_NOW` i zablokowano benchmark do czasu decyzji Supervisora.

Kolejne kroki: Stage 2 benchmark must not begin until Supervisor accepts TEST_NOW shortlist.

## Co zostało zrobione

- [x] Potwierdzono wejście ze Stage 1: `gray_absdiff_gaussian`.
- [x] Zidentyfikowano ograniczenia Stage 1: bbox regionu zmiany nie jest bboxem karty.
- [x] Przeanalizowano connected components, contours, morphology, merge/split, bbox tightening, shape filters, edge density, watershed i distance transform.
- [x] Wskazano shortlistę `TEST_NOW`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001`: Research Gate Stage 2 Region Segmentation / Region Refinement.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001`: implementacja benchmarku po akceptacji shortlisty.

## Shortlista TEST_NOW

- `connected_components_filtered`
- `morph_close_then_components`
- `dilate_then_merge_components`
- `bbox_padding_then_tighten_by_mask`
- `contour_external_bbox`
- `contour_largest_inside_region`
- `foreground_projection_tightening`
- `rectangularity_filter`
- `solidity_extent_filter`
- `expected_card_size_filter`
- `edge_density_filter`

## Kolejne kroki

Natychmiastowy następny krok dla kolejnego modelu: przekazać shortlistę `TEST_NOW` Supervisorowi. Po akceptacji dopiero wtedy utworzyć i zaimplementować offline benchmark Stage 2 w izolowanym `tools/cv_detection_lab/`, bez zmian runtime.
