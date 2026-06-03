# State-First Offline Lab Stage 2 Plan

## Status ogólny

Stage 1 Difference Detection jest zatwierdzony:

```text
APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
```

Stage 2 ma zaimplementowany pierwszy izolowany benchmark offline. Wynik jest wyłącznie provisional i wymaga manualnego review overlay przez Supervisora.

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
- [x] `TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001`: implementacja benchmarku po akceptacji shortlisty.

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

## Session Status (2026-06-03 Codex Stage 2 Benchmark)

Stan aktualny: benchmark Stage 2 działa offline i wygenerował `42` wiersze macierzy na zatwierdzonych fixture.

Co zostało zrobione: dodano `tools/cv_detection_lab/region_methods.py`, `tools/cv_detection_lab/stage2_region_benchmark.py` oraz testy `app_cv/tests/test_cv_detection_lab_stage2.py`. Benchmark używa Stage 1 `gray_absdiff_gaussian` jako wejścia i zapisuje raporty/debug overlay do `logs/offline_replay/stage2_region/`.

Wynik: `contour_external` jest `PROVISIONAL_RECOMMENDED`, bo ma komplet `PASS` i najniższy runtime w tym przebiegu. Nie oznacza to finalnego `APPROVED_STAGE_2_METHOD`.

Kolejne kroki: Supervisor powinien przejrzeć:

```text
logs/offline_replay/stage2_region/contour_external/empty_to_empty/candidate_overlay.png
logs/offline_replay/stage2_region/contour_external/empty_to_one_card/candidate_overlay.png
logs/offline_replay/stage2_region/contour_external/empty_to_three_cards/candidate_overlay.png
logs/offline_replay/stage2_region/contour_external/one_card_to_three_cards/candidate_overlay.png
logs/offline_replay/stage2_region/contour_external/one_card_to_empty/candidate_overlay.png
logs/offline_replay/stage2_region/contour_external/three_cards_to_empty/candidate_overlay.png
```

Nie przechodzić do Stage 3 przed review.

## Stage 2 Final Decision

Decision:

APPROVED_STAGE_2_METHOD: contour_external

Reason:

Metoda poprawnie przeszła benchmark i manualny overlay review na parach:

- `empty -> empty`
- `empty -> one_card`
- `empty -> three_cards`
- `one_card -> three_cards`
- `one_card -> empty`
- `three_cards -> empty`

Scope:

Stage 2 approval covers Region Segmentation / Region Refinement only.

Important limitation:

Stage 2 bbox = candidate object/card region, not final card geometry or crop.

Next stage:

TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001

## Session Status (2026-06-03 Codex Stage 3 Research Gate)

Stan aktualny: Stage 1 approved: `gray_absdiff_gaussian`. Stage 2 approved: `contour_external`. Next gate: Stage 3 Card Localization research.

Co zostało zrobione: utworzono `TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001` i zapisano shortlistę metod Card Localization / Geometry Extraction do decyzji Supervisora. Nie zmieniono `tools/cv_detection_lab/`, runtime, Studio ani frontendu.

Kolejne kroki: Stage 3 benchmark must not begin until Supervisor accepts TEST_NOW shortlist. Po akceptacji należy utworzyć `TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001`.
