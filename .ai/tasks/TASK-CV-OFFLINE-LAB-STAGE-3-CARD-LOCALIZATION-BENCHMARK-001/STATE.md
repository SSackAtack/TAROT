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
