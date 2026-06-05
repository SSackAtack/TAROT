# TEST_REPORT

## Data

2026-06-04

## Wynik

`PASS`

## TDD

Initial RED:

```text
ModuleNotFoundError: tools.cv_detection_lab.stage6_identification_methods
```

## Stage 6 Tests

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_identification -v
```

Result: `PASS` — 5 tests.

## Real Benchmark

```powershell
python tools\cv_detection_lab\stage6_card_identification_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --reference-deck-dir biblioteka_talii\gilded\produkcja\wzorce_cv --deck-profile biblioteka_talii\gilded\deck_profile.json --ground-truth logs\live_fixtures\event_first_current_debug_verified\ground_truth.json --output logs\offline_replay\stage6_card_identification
```

Result: `PASS`

Recommended method: `orb_bfmatcher_ratio_test`

## Final Verification

- Stage 1-5 regression: `PASS` — 51 tests.
- Stage 6 identification + preflight: `PASS` — 14 tests.
- Python compile: `PASS`.
- Full backend suite: `PASS` — 381 tests.
- Frontend build: `NOT_RUN` — no `app_ar/` changes.

## Scope Verification

- No runtime files changed.
- No Studio / WebSocket files changed.
- No new dependencies added.

## Manual Review Pack Verification

- Six numbered scenario sheets: `PASS`.
- Benchmark `report.md`, `report.json` and `matrix.csv`: `PASS`.
- ZIP archive created: `PASS`.
