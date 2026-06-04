# TEST_REPORT

## Data

2026-06-03

## Wynik

`PASS`

## Komendy

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage3 -v"
```

Wynik:

```text
Ran 8 tests in 0.265s
OK
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 -v"
```

Wynik:

```text
Ran 15 tests in 0.308s
OK
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -B -m py_compile tools\cv_detection_lab\card_localization_methods.py tools\cv_detection_lab\stage3_card_localization_benchmark.py app_cv\tests\test_cv_detection_lab_stage3.py"
```

Wynik:

```text
PASS
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python tools\cv_detection_lab\stage3_card_localization_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage3_card_localization"
```

Wynik:

```json
{
  "recommended_method": "hybrid_edge_plus_contour",
  "rows": 42
}
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -m unittest discover -s app_cv\tests -v"
```

Wynik:

```text
Ran 339 tests in 9.873s
OK
```

## Frontend

`NOT_RUN` - task nie zmienia `app_ar/` ani frontendowego runtime.

## Manual review

Wymagane przed zatwierdzeniem Stage 3:

```text
logs/offline_replay/stage3_card_localization/hybrid_edge_plus_contour/*/card_geometry_overlay.png
```

## TASK-CV-OFFLINE-LAB-STAGE-3-MANUAL-REVIEW-PACK-001

### Summary

Prepared local manual review pack for Stage 3 `hybrid_edge_plus_contour` geometry overlays.

### Files prepared locally

- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/01_empty_to_empty_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/02_empty_to_one_card_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/03_empty_to_three_cards_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/04_one_card_to_three_cards_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/05_one_card_to_empty_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/hybrid_edge_plus_contour/06_three_cards_to_empty_card_geometry_overlay.png`
- `logs/offline_replay/stage3_manual_review_pack/README_FOR_SUPERVISOR.md`
- `logs/offline_replay/stage3_manual_review_pack_hybrid_edge_plus_contour.zip`

### Tests

No algorithmic tests required. Packaging only.

Verification:

- confirmed all 6 PNG files exist
- confirmed README exists
- confirmed ZIP exists

### Decision

Stage 3 still `PROVISIONAL_RECOMMENDED`.

Waiting for Supervisor visual review.

### Required next action

Michal uploads the six PNG overlays to ChatGPT Supervisor for manual Stage 3 review.

## TASK-CV-OFFLINE-LAB-STAGE-3-DECISION-001

### Manual Review

Reviewed overlays for `hybrid_edge_plus_contour`:

- `empty_to_empty`: PASS
- `empty_to_one_card`: PASS
- `empty_to_three_cards`: PASS
- `one_card_to_three_cards`: PASS
- `one_card_to_empty`: PASS
- `three_cards_to_empty`: PASS

### Decision

APPROVED_STAGE_3_METHOD: hybrid_edge_plus_contour

### Automated Tests

NOT_RUN — documentation-only stage gate.

### Notes

Automated tests were already executed in `TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001`.

This task only records the Supervisor decision after manual overlay review.
