# TEST_REPORT

## Data

2026-06-04

## Wynik

`PASS`

## RED

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage5 -v
```

Wynik oczekiwany:

```text
ModuleNotFoundError: No module named 'tools.cv_detection_lab.crop_quality_methods'
FAILED (errors=1)
```

## GREEN

### Stage 5 testy

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage5 -v
```

Wynik:

```text
Ran 11 tests in 2.072s
OK
```

Testy:

1. `test_builds_six_pairs` — PASS
2. `test_removed_pairs_use_previous_frame` — PASS
3. `test_empty_to_empty_gives_no_crops_and_pass` — PASS
4. `test_quality_metrics_on_valid_synthetic_crop` — PASS
5. `test_blurry_crop_lowers_sharpness_score` — PASS
6. `test_overexposed_crop_sets_flag_or_ratio` — PASS
7. `test_bad_aspect_sets_flag_or_lowers_score` — PASS
8. `test_matrix_has_required_columns` — PASS
9. `test_report_has_provisional_manual_review_and_threshold_status` — PASS
10. `test_no_identification_files_are_generated` — PASS
11. `test_manual_review_paths_all_exist` — PASS

### Py compile

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -B -m py_compile tools\cv_detection_lab\crop_quality_methods.py tools\cv_detection_lab\stage5_crop_quality_validation_benchmark.py app_cv\tests\test_cv_detection_lab_stage5.py
```

Wynik: PASS

### Stage 1/2/3/4 regresja

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 app_cv.tests.test_cv_detection_lab_stage4 -v
```

Wynik:

```text
Ran 34 tests in 2.034s
OK
```

### Benchmark CLI

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage5_crop_quality_validation_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage5_crop_quality_validation
```

Wynik:

```json
{
  "recommended_method": "quality_metric_suite_v1",
  "recommendation_status": "PROVISIONAL_RECOMMENDED",
  "threshold_status": "BENCHMARK_HEURISTIC_ONLY",
  "rows": 6
}
```

Matrix summary:

```text
empty_to_empty => PASS
empty_to_one_card => YELLOW
empty_to_three_cards => YELLOW
one_card_to_three_cards => YELLOW
one_card_to_empty => YELLOW
three_cards_to_empty => YELLOW
```

### Full backend suite

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests -v
```

Wynik:

```text
Ran 361 tests in 8.232s
OK
```

## Frontend

`NOT_RUN` — task nie zmienia `app_ar/`.

---

## TASK-CV-OFFLINE-LAB-STAGE-5-FOREGROUND-MARGIN-FIX-001

### RED

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage5 -v
```

Wynik oczekiwany:

```text
FAILED (failures=3)
```

Failujace regresje:

```text
test_top_margin_detected_on_synthetic_crop
test_crop_without_large_margin_has_lower_top_margin_than_crop_with_margin
test_background_margin_score_reacts_to_extra_margin
```

Powod: `top_margin_ratio` pozostawal `0.0`, a `background_margin_score` pozostawal `1.0`, poniewaz broad brightness mask traktowal prawie caly crop jako foreground.

### Stage 5 testy

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage5 -v
```

Wynik:

```text
Ran 14 tests in 2.037s
OK
```

Nowe regresje:

1. `test_top_margin_detected_on_synthetic_crop` — PASS
2. `test_crop_without_large_margin_has_lower_top_margin_than_crop_with_margin` — PASS
3. `test_background_margin_score_reacts_to_extra_margin` — PASS

### Stage 1/2/3/4 regresja

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 app_cv.tests.test_cv_detection_lab_stage4 -v
```

Wynik:

```text
Ran 34 tests in 2.182s
OK
```

### Py compile

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -B -m py_compile tools\cv_detection_lab\crop_quality_methods.py tools\cv_detection_lab\stage5_crop_quality_validation_benchmark.py app_cv\tests\test_cv_detection_lab_stage5.py
```

Wynik: PASS

### Benchmark CLI

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage5_crop_quality_validation_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage5_crop_quality_validation
```

Wynik:

```json
{
  "recommended_method": "quality_metric_suite_v1",
  "recommendation_status": "PROVISIONAL_RECOMMENDED",
  "threshold_status": "BENCHMARK_HEURISTIC_ONLY",
  "rows": 6
}
```

### Full backend suite

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests -v
```

Wynik:

```text
Ran 364 tests in 12.878s
OK
```

### Frontend

`NOT_RUN` — task nie zmienia `app_ar/`.

---

## TASK-CV-OFFLINE-LAB-STAGE-5-MANUAL-REVIEW-PACK-001

### Artefact check

```powershell
Get-ChildItem logs\offline_replay\stage5_crop_quality_validation\manual_review_pack_quality_metric_suite_v1 -Filter *.png
```

Wynik:

```text
6 PNG files present
```

### Backend

`NOT_RUN` — task kopiuje istniejace artefakty manual review i aktualizuje dokumentacje.

### Frontend

`NOT_RUN` — task nie zmienia `app_ar/`.
