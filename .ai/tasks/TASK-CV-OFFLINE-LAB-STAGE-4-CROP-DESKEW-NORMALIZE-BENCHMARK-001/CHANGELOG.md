# CHANGELOG

- dodano `tools/cv_detection_lab/crop_deskew_methods.py`
- dodano `tools/cv_detection_lab/stage4_crop_deskew_normalize_benchmark.py`
- dodano `app_cv/tests/test_cv_detection_lab_stage4.py`
- brak zmian runtime
- brak identyfikacji kart
- brak integracji WebSocket / Studio

## TASK-CV-OFFLINE-LAB-STAGE-4-REVIEW-PATHS-FIX-001

- Added no-crop placeholder `crop_debug_sheet.png` for manual review paths.
- Added regression test ensuring `empty_to_empty` manual review sheet exists.
- Added regression test ensuring all `manual_review_paths` files exist.
- No runtime changes.
- No card identification changes.

## TASK-CV-OFFLINE-LAB-STAGE-4-MANUAL-REVIEW-PACK-001

- Prepared local review pack with 6 crop debug sheets for Supervisor.
- Created README_FOR_SUPERVISOR.md with review criteria.
- Created ZIP archive for distribution.
- No code changes. Packaging only.
