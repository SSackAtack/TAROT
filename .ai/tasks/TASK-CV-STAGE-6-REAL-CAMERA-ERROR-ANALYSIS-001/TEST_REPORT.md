# TEST REPORT

## Error Analysis

`python -m tools.cv_detection_lab.stage6_real_camera_error_analysis ...` => PASS

- Top-1 errors: `4`
- Outside Top-3: `3`
- Review sheets: `4`
- Full `matrix.csv`, benchmark report and `extracted_crops/` included.
- ZIP: `logs/offline_replay/stage6_real_camera_error_analysis_review_pack.zip`
- ZIP SHA-256: `10FC4B525FFA549A5D79F819BFF266A8CDF6B7E4C0D02766E67303D7C940AE03`

## Tests

- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_error_analysis -v` => PASS, 5 tests
- `python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_error_analysis app_cv.tests.test_cv_detection_lab_stage6_real_camera_identification app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v` => PASS, 28 tests
- `python -m unittest discover -s app_cv/tests -v` => PASS, 415 tests
- `python -m py_compile ...` => PASS

## Scope

Brak zmian runtime, ground truth i aplikacji.
