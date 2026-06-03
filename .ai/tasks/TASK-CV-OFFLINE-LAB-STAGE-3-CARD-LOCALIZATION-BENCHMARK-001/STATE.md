# STATE

## Status

`DONE`

## Data

2026-06-03

## Realizator

Codex

## Stan aktualny

Offline benchmark Stage 3 Card Localization / Geometry Extraction zostal zaimplementowany w izolowanym `tools/cv_detection_lab/`.

Benchmark korzysta z zatwierdzonego wejscia:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
```

Nie wykonuje cropowania, deskew, rozpoznawania kart ani integracji runtime.

## Co zostalo zrobione

- Dodano modul metod lokalizacji geometrii kart.
- Dodano CLI benchmarku Stage 3 generujacy macierz wynikow, raporty i overlaye diagnostyczne.
- Dodano testy jednostkowe Stage 3, w tym walidacje par `removed` na klatce `previous`.
- Uruchomiono benchmark na `logs/live_fixtures/event_first_current_debug_verified`.
- Wybrano prowizoryczna rekomendacje `hybrid_edge_plus_contour`.

## Wyniki benchmarku

```text
Output: logs/offline_replay/stage3_card_localization
Rows: 42
Methods: 7
Pairs: 6
Recommended method: hybrid_edge_plus_contour
Recommendation status: PROVISIONAL_RECOMMENDED
Manual review required: true
```

## Kolejne kroki

Supervisor powinien recznie sprawdzic overlaye:

```text
logs/offline_replay/stage3_card_localization/hybrid_edge_plus_contour/*/card_geometry_overlay.png
```

Po akceptacji Supervisora mozna zatwierdzic Stage 3 jako wejscie do kolejnego etapu. Nie rozpoczynac Stage 4 przed manual review.

## TASK-CV-OFFLINE-LAB-STAGE-3-MANUAL-REVIEW-PACK-001

### Summary

Prepared local manual review pack for Stage 3 `hybrid_edge_plus_contour` geometry overlays.

### Files prepared locally

- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/01_empty_to_empty_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/02_empty_to_one_card_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/03_empty_to_three_cards_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/04_one_card_to_three_cards_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/05_one_card_to_empty_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/06_three_cards_to_empty_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/README_FOR_SUPERVISOR.md`
- `logs/offline_replay/stage3_manual_review_pack_hybrid_edge_plus_contour.zip`

### Tests

No algorithmic tests required. Packaging only.

Verification:

- confirmed all 6 PNG files exist
- confirmed README exists
- confirmed ZIP exists

### Decision

Stage 3 still `PROVISIONAL_RECOMMENDED`.

Waiting for Supervisor visual review.

### Required next action

Michal uploads the six PNG overlays to ChatGPT Supervisor for manual Stage 3 review.

## TASK-CV-OFFLINE-LAB-STAGE-3-DECISION-001

### Supervisor Manual Review

Manualnie przejrzano overlaye `hybrid_edge_plus_contour` dla 6 par testowych:

- `empty_to_empty`
- `empty_to_one_card`
- `empty_to_three_cards`
- `one_card_to_three_cards`
- `one_card_to_empty`
- `three_cards_to_empty`

### Decision

APPROVED_STAGE_3_METHOD: hybrid_edge_plus_contour

### Scope of Approval

Zatwierdzenie dotyczy tylko Stage 3 Card Localization / Geometry Extraction:

- wyznaczanie geometrii karty wewnątrz regionu kandydata Stage 2,
- generowanie bbox / rotated bbox / quad points / ordered quad points,
- poprawne działanie dla `added` regions,
- poprawne działanie dla `removed` regions z użyciem `previous_snapshot`,
- poprawne działanie w modelu kaskadowym `one_card -> three_cards`,
- przygotowanie danych geometrycznych dla przyszłego Stage 4.

### Known Limitation

Stage 3 nie zatwierdza jeszcze cropowania, deskew, normalizacji ani identyfikacji kart.

`ordered_quad_points` są wejściem do przyszłego Stage 4, ale Stage 4 musi dopiero potwierdzić jakość crop/deskew.

### Required Next Action

Utworzyć:

TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001
