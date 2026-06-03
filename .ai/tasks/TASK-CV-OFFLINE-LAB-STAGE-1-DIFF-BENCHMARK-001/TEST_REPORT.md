# Raport z Testów — TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001

## 1. Testy Automatyczne Backend (Python)

* **Status:** `PASS`
* **Komenda uruchomienia 1:** `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 -v`
* **Komenda uruchomienia 2:** `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests -v`

### Wynik konsoli:

```text
Ran 3 tests in 0.130s
OK

Ran 319 tests in 9.370s
OK
```

## 1a. Kompilacja Python

* **Status:** `PASS`
* **Komenda uruchomienia:** `python -B -m py_compile tools\cv_detection_lab\methods.py tools\cv_detection_lab\stage1_diff_benchmark.py app_cv\tests\test_cv_detection_lab_stage1.py`

### Wynik konsoli:

```text
PASS
```

---

## 2. Offline Benchmark

* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage1_diff_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage1_diff`

### Wynik konsoli:

```text
{
  "recommended_method": "gray_absdiff_gaussian",
  "rows": 42
}
```

### Output lokalny:

```text
logs/offline_replay/stage1_diff/matrix.csv
logs/offline_replay/stage1_diff/report.json
logs/offline_replay/stage1_diff/report.md
logs/offline_replay/stage1_diff/<method>/<pair>/{diff,mask,regions_overlay}.png
```

Wygenerowano `126` obrazów debug.

---

## 3. Testy Kompilacji Frontend (Node/Vite)

* **Status:** `NOT_RUN`
* **Uzasadnienie:** task nie modyfikuje `app_ar/`.

---

## 4. Testy Manualne

Nie uruchamiano kamery ani Studio. To jest benchmark offline na zatwierdzonych fixture.

## TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-REFINE-001

### Summary

Doprecyzowano metryki regionów i raportowanie benchmarku Stage 1. `region_count` bazuje teraz na `merged_region_count`, a raport wymaga ręcznego review overlay przed zatwierdzeniem metody.

### Metrics added

- `raw_region_count`
- `filtered_region_count`
- `merged_region_count`
- `ignored_small_count`
- `ignored_large_count`
- `largest_region_area_ratio`
- `largest_merged_region_area_ratio`
- `recommendation_status`
- `manual_review_paths`

### Benchmark result

- `recommended_method`: `gray_absdiff_gaussian`
- `recommendation_status`: `PROVISIONAL_RECOMMENDED`
- `rows`: `42`
- output: `logs/offline_replay/stage1_diff`

### Tests

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 -v
=> PASS, 8 tests

python -B -m py_compile tools\cv_detection_lab\methods.py tools\cv_detection_lab\stage1_diff_benchmark.py app_cv\tests\test_cv_detection_lab_stage1.py
=> PASS

$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage1_diff_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage1_diff
=> PASS, recommended_method=gray_absdiff_gaussian, rows=42

$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests -v
=> PASS, 324 tests
```

Frontend build: `NOT_RUN`, ponieważ task nie modyfikuje `app_ar/`.

### Decision

Na tym etapie: `PROVISIONAL_RECOMMENDED: gray_absdiff_gaussian`. Manual review overlays required before `APPROVED_STAGE_1_METHOD`.

### Required next action

Supervisor ma przejrzeć overlay dla `gray_absdiff_gaussian`. Dopiero po tym można zatwierdzić Stage 1 albo zlecić dodatkowy refinement.
