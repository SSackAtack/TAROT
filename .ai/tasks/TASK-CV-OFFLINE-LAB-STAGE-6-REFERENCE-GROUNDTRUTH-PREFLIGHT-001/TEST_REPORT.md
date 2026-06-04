# TEST_REPORT

## Data

2026-06-04

## Wynik

`PASS`

## Automated Tests

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight -v
```

Result: `PASS`

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 app_cv.tests.test_cv_detection_lab_stage4 app_cv.tests.test_cv_detection_lab_stage5 -v
```

Result: `PASS` — 51 tests.

```powershell
python -B -m py_compile tools\cv_detection_lab\stage6_preflight.py app_cv\tests\test_cv_detection_lab_stage6_preflight.py
```

Result: `PASS`

```powershell
python -m unittest discover -s app_cv\tests -v
```

Result: `PASS` — 376 tests.

## Manual / Real Preflight

```powershell
python tools\cv_detection_lab\stage6_preflight.py --fixture logs\live_fixtures\event_first_current_debug_verified --reference-deck-dir biblioteka_talii\gilded\produkcja\wzorce_cv --deck-profile biblioteka_talii\gilded\deck_profile.json --ground-truth logs\live_fixtures\event_first_current_debug_verified\ground_truth.json --output logs\offline_replay\stage6_card_identification_preflight
```

Result: `PROVISIONAL_BLOCKED`

Blocking inputs:

- `MISSING_DECK_PROFILE`: `biblioteka_talii\gilded\deck_profile.json`
- `MISSING_GROUND_TRUTH`: `logs\live_fixtures\event_first_current_debug_verified\ground_truth.json`

Stage 5 output check: `PASS`

Output:

```text
logs/offline_replay/stage6_card_identification_preflight/preflight_report.json
logs/offline_replay/stage6_card_identification_preflight/preflight_report.md
```

## Scope Verification

- No runtime files changed.
- No Stage 1-5 benchmark files changed.
- No card identification implemented.
- No new dependencies added.
