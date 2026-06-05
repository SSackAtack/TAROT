# TEST_REPORT

## Data

2026-06-04

## Wynik

`PASS`

## Ground Truth Check

```powershell
python tools\cv_detection_lab\stage6_preflight.py --fixture logs\live_fixtures\event_first_current_debug_verified --reference-deck-dir biblioteka_talii\gilded\produkcja\wzorce_cv --deck-profile biblioteka_talii\gilded\deck_profile.json --ground-truth logs\live_fixtures\event_first_current_debug_verified\ground_truth.json --output logs\offline_replay\stage6_card_identification_preflight
```

Result: `PASS`

Ground truth summary:

- `label_count`: 10
- `unknown_count`: 0
- `not_in_reference_scope_count`: 0

## Automated Tests

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight -v
```

Result: `PASS` — 9 tests.

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 app_cv.tests.test_cv_detection_lab_stage4 app_cv.tests.test_cv_detection_lab_stage5 -v
```

Result: `PASS` — 51 tests.

```powershell
python -m unittest discover -s app_cv\tests -v
```

Result: `PASS` — 376 tests.

## Frontend

Result: `NOT_RUN` — no `app_ar/` changes.

## Scope Verification

- No runtime files changed.
- No Stage 6 benchmark implemented.
- No card identification code implemented.
- No new dependencies added.
