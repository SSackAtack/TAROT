# Wykaz Zmian — TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001

## 1. Modyfikowane Pliki Produkcyjne

Brak zmian w runtime produkcyjnym.

---

## 2. Nowe Narzędzia Offline

### `tools/cv_detection_lab/methods.py`

* Dodano metody różnicowania obrazów dla Stage 1: grayscale fixed, Gaussian, median, Otsu, LAB weighted, HSV weighted i illumination-normalized grayscale.

### `tools/cv_detection_lab/stage1_diff_benchmark.py`

* Dodano CLI benchmarku, loader fixture, generowanie par testowych, ekstrakcję regionów, zapis `matrix.csv`, `report.json`, `report.md` i obrazów debug.

---

## 3. Pliki Testowe

### `app_cv/tests/test_cv_detection_lab_stage1.py`

* Testuje budowę par fixture.
* Testuje zapis raportów i obrazów debug.
* Testuje, że baseline `empty -> empty` daje `PASS` i zero regionów.
* Dodano regresje dla refinementu Stage 1: merge bliskich komponentów, liczenie `ignored_small_count`, liczenie `ignored_large_count`, obecność nowych kolumn CSV oraz provisional/manual-review fields w `report.json`.

---

## 4. Dokumentacja

### `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/`

* Dodano komplet dokumentów taska.

### `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-1-plan.md`

* Dopisano wyniki pierwszego benchmarku offline.

## TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-REFINE-001

### Summary

Rozszerzono benchmark Stage 1 o bogatszą diagnostykę regionów przed formalnym Stage Gate.

### Metrics added

- `raw_region_count`
- `filtered_region_count`
- `merged_region_count`
- `ignored_small_count`
- `ignored_large_count`
- `largest_region_area_ratio`
- `largest_merged_region_area_ratio`
- `verdict_basis`
- `recommendation_status`
- `manual_review_paths`

### Benchmark result

- `recommended_method`: `gray_absdiff_gaussian`
- `recommendation_status`: `PROVISIONAL_RECOMMENDED`
- `rows`: `42`
- output: `logs/offline_replay/stage1_diff`

### Decision

Stage 1 nie jest jeszcze finalnie zatwierdzony. `gray_absdiff_gaussian` jest tylko provisional recommendation do ręcznego review overlay.

## TASK-CV-OFFLINE-LAB-STAGE-1-MANUAL-REVIEW-PACK-001

### Summary

Prepared local manual review pack for `gray_absdiff_gaussian` overlays.

### Files prepared locally

- `logs/offline_replay/stage1_manual_review_pack/gray_absdiff_gaussian/01_empty_to_empty_regions_overlay.png`
- `logs/offline_replay/stage1_manual_review_pack/gray_absdiff_gaussian/02_empty_to_one_card_regions_overlay.png`
- `logs/offline_replay/stage1_manual_review_pack/gray_absdiff_gaussian/03_empty_to_three_cards_regions_overlay.png`
- `logs/offline_replay/stage1_manual_review_pack/gray_absdiff_gaussian/04_one_card_to_three_cards_regions_overlay.png`
- `logs/offline_replay/stage1_manual_review_pack/gray_absdiff_gaussian/05_one_card_to_empty_regions_overlay.png`
- `logs/offline_replay/stage1_manual_review_pack/gray_absdiff_gaussian/06_three_cards_to_empty_regions_overlay.png`
- `logs/offline_replay/stage1_manual_review_pack/README_FOR_SUPERVISOR.md`
- `logs/offline_replay/stage1_manual_review_pack_gray_absdiff_gaussian.zip`

### Tests

No algorithmic tests required. This is local packaging only.

Optional verification:

- confirmed all 6 PNG files exist
- confirmed ZIP exists

### Decision

Stage 1 still `PROVISIONAL_RECOMMENDED`. Waiting for Supervisor visual review.

### Required next action

Michał uploads the six PNG overlays to ChatGPT Supervisor for visual review.

## TASK-CV-OFFLINE-LAB-STAGE-1-DECISION-001

- Supervisor zatwierdził `gray_absdiff_gaussian` jako metodę Stage 1 Difference Detection.
- Zatwierdzenie dotyczy wyłącznie detekcji różnic, nie segmentacji kart ani cropowania.
- Znane ograniczenie: bboxy mogą obejmować tło/refleksy, szczególnie przy środkowej karcie.
- Następny krok: Research Gate Stage 2 Region Segmentation.
