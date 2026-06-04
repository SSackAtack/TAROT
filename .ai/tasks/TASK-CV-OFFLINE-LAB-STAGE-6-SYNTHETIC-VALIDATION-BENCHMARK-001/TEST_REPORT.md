# TEST_REPORT

## Date

2026-06-04

## TDD

Initial generator RED:

```text
ModuleNotFoundError: tools.cv_detection_lab.stage6_synthetic_dataset
```

Initial runner RED:

```text
ModuleNotFoundError: tools.cv_detection_lab.stage6_synthetic_validation_benchmark
```

## Verification

- Stage 6 synthetic validation + identification + preflight: `PASS` — 20 tests.
- Stage 1-5 regression: `PASS` — 51 tests.
- Python compile: `PASS`.
- Full backend suite: `PASS` — 387 tests.
- Manifest reproducibility: `PASS` — 192 identical sample records.
- Representative `yellow_combined` debug sheet visual review: `PASS`.
- Frontend build: `NOT_RUN` — no `app_ar/` changes.

## Scope Verification

- No `app_cv/tarotvision/*` changes.
- No `app_cv/main.py` changes.
- No `app_ar/*` changes.
- No runtime threshold changes.
- No full synthetic image dataset committed.
