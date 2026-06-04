# State-First Offline Lab Stage 3 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
```

Stage 3 final decision: `APPROVED_STAGE_3_METHOD: hybrid_edge_plus_contour`.
Next gate: `TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001`.

## Session Status (2026-06-03 Codex)

Stan aktualny: przygotowano research summary dla Stage 3 Card Localization / Geometry Extraction.

Co zostało zrobione: zapisano macierz kandydatów w `.ai/tasks/TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001/RESEARCH_REPORT.md`, wskazano shortlistę `TEST_NOW` i zablokowano benchmark do czasu decyzji Supervisora.

Kolejne kroki: Supervisor powinien zaakceptować albo skorygować shortlistę `TEST_NOW`.

## Session Status (2026-06-03 Codex Stage 3 Benchmark)

Stan aktualny: zaimplementowano i uruchomiono izolowany offline benchmark Stage 3 Card Localization / Geometry Extraction.

Co zostało zrobione: dodano `card_localization_methods.py`, `stage3_card_localization_benchmark.py` oraz testy `test_cv_detection_lab_stage3.py`. Benchmark korzysta z `gray_absdiff_gaussian` i `contour_external`, generuje `matrix.csv`, `report.json`, `report.md` oraz overlay/debug per metoda i para fixture.

Kolejne kroki: Supervisor powinien recznie sprawdzic overlaye rekomendowanej metody `hybrid_edge_plus_contour` w `logs/offline_replay/stage3_card_localization/hybrid_edge_plus_contour/*/card_geometry_overlay.png`. Nie rozpoczynac Stage 4 przed akceptacja.

## Co zostało zrobione

- [x] Potwierdzono wejście ze Stage 1: `gray_absdiff_gaussian`.
- [x] Potwierdzono wejście ze Stage 2: `contour_external`.
- [x] Zidentyfikowano ograniczenie Stage 2: bbox regionu kandydata nie jest finalną geometrią karty.
- [x] Przeanalizowano kontury, `approxPolyDP`, `minAreaRect`, edge-supported bbox, Hough/LSD lines, corner evidence i scoring borderów.
- [x] Wskazano shortlistę `TEST_NOW`.
- [x] Zaimplementowano benchmark Stage 3 w izolowanym `tools/cv_detection_lab/`.
- [x] Zweryfikowano pary `removed` na klatce `previous`.
- [x] Wygenerowano raport benchmarku i overlaye diagnostyczne.
- [x] Wybrano prowizoryczna rekomendacje `hybrid_edge_plus_contour`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001`: Research Gate Stage 3 Card Localization / Geometry Extraction.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001`: implementacja benchmarku po akceptacji shortlisty.

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

Natychmiastowy następny krok dla kolejnego modelu: wykonac manual review overlayow rekomendowanej metody `hybrid_edge_plus_contour`:

```text
logs/offline_replay/stage3_card_localization/hybrid_edge_plus_contour/*/card_geometry_overlay.png
```

Po akceptacji Supervisora oznaczyc Stage 3 jako zatwierdzone wejscie do kolejnego etapu. Nie rozpoczynac Stage 4 przed ta decyzja.

## Stage 3 Final Decision

Decision:

APPROVED_STAGE_3_METHOD: hybrid_edge_plus_contour

Reason:

Metoda poprawnie przeszła benchmark i manualny overlay review na parach:

- `empty -> empty`
- `empty -> one_card`
- `empty -> three_cards`
- `one_card -> three_cards`
- `one_card -> empty`
- `three_cards -> empty`

Scope:

Stage 3 approval covers Card Localization / Geometry Extraction only.

Approved output:

- `bbox`
- `rotated_bbox`
- `quad_points`
- `ordered_quad_points`
- `geometry_confidence`

Important limitation:

Stage 3 does not approve crop, deskew, crop quality, card identification or runtime integration.

Next stage:

TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001

## Session Status (2026-06-03 Codex Stage 4 Research Gate)

Stan aktualny: Stage 1 approved: `gray_absdiff_gaussian`. Stage 2 approved: `contour_external`. Stage 3 approved: `hybrid_edge_plus_contour`. Next gate: Stage 4 Crop / Deskew / Normalize research.

Co zostało zrobione: utworzono `TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001` i zapisano shortlistę metod crop / deskew / normalize do decyzji Supervisora. Nie zmieniono `tools/cv_detection_lab/`, runtime, Studio ani frontendu.

Kolejne kroki: Stage 4 benchmark must not begin until Supervisor accepts TEST_NOW shortlist. Po akceptacji należy utworzyć `TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001`.
