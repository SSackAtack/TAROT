# Raport z Testów — TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001

## 1. Testy Automatyczne Stage 2

* **Status:** `PASS`
* **Komenda:** `python -m unittest app_cv.tests.test_cv_detection_lab_stage2 -v`
* **Wynik:** `Ran 7 tests ... OK`

## 2. Testy Regresyjne Stage 1

* **Status:** `PASS`
* **Komenda:** `python -m unittest app_cv.tests.test_cv_detection_lab_stage1 -v`
* **Wynik:** `Ran 8 tests ... OK`

## 3. Kompilacja Python

* **Status:** `PASS`
* **Komenda:** `python -B -m py_compile tools\cv_detection_lab\region_methods.py tools\cv_detection_lab\stage2_region_benchmark.py app_cv\tests\test_cv_detection_lab_stage2.py`

## 4. Offline Benchmark Stage 2

* **Status:** `PASS`
* **Komenda:** `python tools\cv_detection_lab\stage2_region_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage2_region`
* **Wynik:**

```json
{
  "recommended_method": "contour_external",
  "rows": 42
}
```

Output lokalny:

```text
logs/offline_replay/stage2_region/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/stage1_mask.png
  <method>/<pair>/candidate_mask.png
  <method>/<pair>/candidate_overlay.png
  <method>/<pair>/tightened_overlay.png
  <method>/<pair>/region_debug.json
```

## 5. Pełny Backend Suite

* **Status:** `PASS`
* **Komenda:** `python -m unittest discover -s app_cv\tests -v`
* **Wynik:** `Ran 331 tests ... OK`

## 6. Frontend Build

* **Status:** `NOT_RUN`
* **Uzasadnienie:** task nie modyfikuje `app_ar/`.

## 7. Uwagi Środowiskowe

Lokalny katalog zależności `C:\tmp\tarot_pydeps` musiał zostać odtworzony, bo sandboxowy import widział uszkodzony namespace `numpy`. Testy uruchomiono z dostępem do odtworzonych zależności OpenCV/NumPy.

## TASK-CV-OFFLINE-LAB-STAGE-2-MANUAL-REVIEW-PACK-001

### Summary

Prepared local manual review pack for Stage 2 `contour_external` overlays.

### Files prepared locally

- `logs/offline_replay/stage2_manual_review_pack/contour_external/01_empty_to_empty_candidate_overlay.png`
- `logs/offline_replay/stage2_manual_review_pack/contour_external/02_empty_to_one_card_candidate_overlay.png`
- `logs/offline_replay/stage2_manual_review_pack/contour_external/03_empty_to_three_cards_candidate_overlay.png`
- `logs/offline_replay/stage2_manual_review_pack/contour_external/04_one_card_to_three_cards_candidate_overlay.png`
- `logs/offline_replay/stage2_manual_review_pack/contour_external/05_one_card_to_empty_candidate_overlay.png`
- `logs/offline_replay/stage2_manual_review_pack/contour_external/06_three_cards_to_empty_candidate_overlay.png`
- `logs/offline_replay/stage2_manual_review_pack/README_FOR_SUPERVISOR.md`
- `logs/offline_replay/stage2_manual_review_pack_contour_external.zip`

### Tests

No algorithmic tests required. Packaging only.

Verification:

- confirmed all 6 PNG files exist
- confirmed README exists
- confirmed ZIP exists

### Decision

Stage 2 still `PROVISIONAL_RECOMMENDED`.

Waiting for Supervisor visual review.

### Required next action

Michał uploads the six PNG overlays to ChatGPT Supervisor for manual Stage 2 review.
