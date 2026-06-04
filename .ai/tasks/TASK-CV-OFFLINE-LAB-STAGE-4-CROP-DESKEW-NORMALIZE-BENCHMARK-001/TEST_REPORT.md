# TEST_REPORT

## Data

2026-06-04

## Wynik

`PASS`

## Komendy

### py_compile

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -B -m py_compile tools\cv_detection_lab\crop_deskew_methods.py tools\cv_detection_lab\stage4_crop_deskew_normalize_benchmark.py app_cv\tests\test_cv_detection_lab_stage4.py
```

Wynik: PASS

### Stage 4 testy

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage4 -v
```

Wynik:

```text
Ran 9 tests in 0.806s
OK
```

Testy:
1. test_builds_six_pairs — PASS
2. test_removed_pairs_crop_source — PASS
3. test_returns_target_size — PASS
4. test_expand_quad_about_center — PASS
5. test_landscape_rotated_to_portrait — PASS
6. test_no_crops_for_identical_frames — PASS
7. test_matrix_has_required_columns — PASS
8. test_report_has_provisional_and_manual_review — PASS
9. test_no_forbidden_files — PASS

### Stage 1/2/3 regresja

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 -v
```

Wynik:

```text
Ran 23 tests in 0.476s
OK
```

### Benchmark CLI

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage4_crop_deskew_normalize_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage4_crop_deskew_normalize
```

Wynik:

```json
{
  "recommended_pipeline": "quad_warp_perspective_fixed_aspect__resize_only_normalization",
  "recommendation_status": "PROVISIONAL_RECOMMENDED",
  "rows": 60
}
```

### Full backend suite

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests
```

Wynik:

```text
Ran 348 tests in 2.344s
OK
```

## Frontend

`NOT_RUN` — task nie zmienia `app_ar/`.

## Manual review

Wymagane przed zatwierdzeniem Stage 4:

```text
logs/offline_replay/stage4_crop_deskew_normalize/quad_warp_perspective_fixed_aspect__resize_only_normalization/*/crop_debug_sheet.png
```

---

## TASK-CV-OFFLINE-LAB-STAGE-4-REVIEW-PATHS-FIX-001

Data: 2026-06-04

### py_compile

Wynik: PASS

### Stage 4 testy (po fixie)

```text
Ran 11 tests in 1.387s
OK
```

Nowe testy:
10. test_empty_to_empty_manual_review_path_exists — PASS
11. test_manual_review_paths_all_exist — PASS

### Stage 1/2/3 regresja

```text
Ran 23 tests in 0.461s
OK
```

### Benchmark CLI

```json
{
  "recommended_pipeline": "quad_warp_perspective_fixed_aspect__resize_only_normalization",
  "recommendation_status": "PROVISIONAL_RECOMMENDED",
  "rows": 60
}
```

Placeholder `empty_to_empty/crop_debug_sheet.png` istnieje: `True`

### Full backend suite

```text
Ran 350 tests in 10.795s
OK
```

### Frontend

`NOT_RUN` — task nie zmienia `app_ar/`.
