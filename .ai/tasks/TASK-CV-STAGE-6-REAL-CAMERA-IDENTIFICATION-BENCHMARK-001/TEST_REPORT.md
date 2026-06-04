# TEST REPORT

## Benchmark

`python -m tools.cv_detection_lab.stage6_real_camera_identification_benchmark ...` => PASS

Przetworzono 28 zatwierdzonych próbek real-camera. Sesje capture nie zostały zmienione.

## Wynik

| Method | Top1 | Top3 | Wrong-deck FAR | Mean runtime proxy |
|---|---:|---:|---:|---:|
| `orb_bfmatcher_ratio_test` | 0.80 | 0.85 | 0.00 | 389.784 ms |
| `akaze_bfmatcher` | 0.70 | 0.70 | 0.75 | 892.476 ms |

## Testy

- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_identification -v` => PASS, 3 tests
- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_identification app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v` => PASS, 34 tests
- `python -m unittest discover -s app_cv/tests -v` => PASS, 410 tests
- `python -B -m py_compile ...` => PASS

## Scope

Brak zmian `app_cv/main.py`, `app_cv/tarotvision/*` i `app_ar/*`.
