# TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001

## Cel

Zaimplementować izolowany offline benchmark Stage 2:

```text
Region Segmentation / Region Refinement
```

Benchmark używa zatwierdzonej metody Stage 1:

```text
APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
```

Stage 2 przekształca regiony zmiany w stabilniejsze kandydaty obiektów/kart. To nie jest etap cropowania, deskew ani identyfikacji kart.

## Zakres

Dozwolone:

- `tools/cv_detection_lab/region_methods.py`
- `tools/cv_detection_lab/stage2_region_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage2.py`
- dokumentacja taska i planu.

Zakazane:

- zmiany runtime w `app_cv/tarotvision/*`,
- zmiany `app_cv/main.py`,
- zmiany `app_ar/*`,
- integracja z WebSocket, Studio UI, ArUco, ORB/FLANN,
- Stage 3 albo rozpoznawanie kart.

## Metody Benchmarku

Główne warianty pipeline:

- `baseline_components`
- `morph_close_components`
- `dilate_merge_components`
- `contour_external`
- `largest_contour_inside_region`
- `padding_tighten_by_mask`
- `projection_tightening`

Metryki/filtry raportowane dla kandydatów:

- rectangularity,
- solidity,
- extent,
- expected size / bbox area ratio,
- foreground fill ratio,
- edge density,
- oversized/split/merge flags.

## CLI

```powershell
python tools\cv_detection_lab\stage2_region_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage2_region
```

## Kryteria Akceptacji

- Benchmark działa offline bez kamery, Studio i WebSocket.
- Testuje 6 par fixture state-first.
- Generuje `matrix.csv`, `report.json`, `report.md` i obrazy debug.
- Raportuje candidate count, added/removed counts i metryki jakości regionów.
- Nie commitować `logs/offline_replay/`.
- Wynik pozostaje `PROVISIONAL_RECOMMENDED`.
