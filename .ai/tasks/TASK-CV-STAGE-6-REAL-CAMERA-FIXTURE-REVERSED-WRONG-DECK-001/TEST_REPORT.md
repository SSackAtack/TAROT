# TEST_REPORT

## TDD

Initial RED:

```text
ModuleNotFoundError: tools.cv_detection_lab.stage6_real_camera_fixture
```

## Focused Tests

```text
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v
PASS - 9 tests
```

## Regression Tests

```text
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v
PASS - 20 tests

python -B -m py_compile tools/cv_detection_lab/stage6_real_camera_fixture.py tools/cv_detection_lab/stage6_real_camera_preflight.py tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py
PASS

$env:PYTHONPATH='app_cv'; python -m unittest discover -s app_cv/tests -v
PASS - 396 tests
```

Initial full discovery without `PYTHONPATH=app_cv` failed during collection because
`tarotvision` was not importable. The configured full backend command above passed.

Frontend build: `NOT_RUN` - no `app_ar` changes.

## Scope

- Runtime files: unchanged.
- Live fixture capture mechanism: unchanged.
- Physical capture: not performed.
- Expected task status: `PROVISIONAL_BLOCKED`.
