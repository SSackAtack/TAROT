# Wykaz Zmian — TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001

## 1. Modyfikowane Pliki Produkcyjne

Brak zmian w runtime produkcyjnym.

## 2. Nowe Narzędzia Offline

### `tools/cv_detection_lab/region_methods.py`

Dodano izolowane metody Stage 2 region segmentation/refinement:

- connected components baseline,
- morphology close,
- dilation + bbox merge,
- external contours,
- largest contour inside region,
- padding + mask tightening,
- projection tightening.

Moduł raportuje metryki kandydatów: bbox/mask area ratio, foreground fill, aspect ratio, rectangularity, solidity, extent, edge density oraz oversized/split/merge flags.

### `tools/cv_detection_lab/stage2_region_benchmark.py`

Dodano CLI benchmarku Stage 2. Narzędzie uruchamia Stage 1 `gray_absdiff_gaussian`, przekazuje maskę do metod Stage 2 i zapisuje:

- `matrix.csv`,
- `report.json`,
- `report.md`,
- `stage1_mask.png`,
- `candidate_mask.png`,
- `candidate_overlay.png`,
- `tightened_overlay.png`,
- `region_debug.json`.

## 3. Pliki Testowe

### `app_cv/tests/test_cv_detection_lab_stage2.py`

Dodano 7 testów:

- budowa 6 par fixture,
- baseline one-candidate,
- empty-to-empty PASS,
- merge rozbitego obiektu,
- oversized bbox flag,
- wymagane kolumny CSV,
- provisional report + manual review paths.

## 4. Dokumentacja

Dodano komplet dokumentów:

- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001/TASK.md`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001/STATE.md`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001/TEST_REPORT.md`

Zaktualizowano:

- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-2-plan.md`
