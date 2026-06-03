# TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001

## Cel

Zaimplementowac izolowany offline benchmark Stage 3: Card Localization / Geometry Extraction dla state-first offline labu.

Stage 3 przyjmuje zatwierdzony pipeline wejscia:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
```

Wyjsciem Stage 3 jest geometria karty dla kazdego kandydata regionu ze Stage 2:

- `card_bbox`
- `rotated_card_bbox`
- `quad_points`
- `geometry_confidence`
- metryki pomocnicze do decyzji Supervisora

## Zakres

Dozwolone zmiany:

- `tools/cv_detection_lab/card_localization_methods.py`
- `tools/cv_detection_lab/stage3_card_localization_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage3.py`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001/*`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-3-plan.md`

## Poza zakresem

- brak cropowania kart
- brak deskew/perspective transform
- brak rozpoznawania kart
- brak integracji runtime
- brak Stage 4
- brak zmiany semantyki Stage 1 i Stage 2

## Kryteria akceptacji

- Benchmark uruchamia Stage 1 `gray_absdiff_gaussian` i Stage 2 `contour_external`.
- Benchmark testuje pary fixture:
  - `empty_to_empty`
  - `empty_to_one_card`
  - `empty_to_three_cards`
  - `one_card_to_three_cards`
  - `one_card_to_empty`
  - `three_cards_to_empty`
- Dla par `removed` geometria jest wyciagana z klatki `previous`, nie z pustej klatki `current`.
- Wyniki sa zapisane jako `matrix.csv`, `report.json`, `report.md` oraz overlay/debug per metoda i para.
- Raport oznacza rekomendacje jako prowizoryczna i wymaga manual review.
- Testy jednostkowe Stage 3 i regresja Stage 1/Stage 2 przechodza lokalnie.

## Wynik

Zaimplementowano benchmark Stage 3 i metody lokalizacji geometrii kart.

Rekomendowana metoda po automatycznym benchmarku:

```text
hybrid_edge_plus_contour
```

Status rekomendacji:

```text
PROVISIONAL_RECOMMENDED
```

Manual review pozostaje wymagany przed przejsciem do Stage 4.
