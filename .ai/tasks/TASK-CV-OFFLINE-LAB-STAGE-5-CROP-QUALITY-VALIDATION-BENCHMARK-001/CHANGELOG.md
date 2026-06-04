# CHANGELOG

- dodano `tools/cv_detection_lab/crop_quality_methods.py`
- dodano `tools/cv_detection_lab/stage5_crop_quality_validation_benchmark.py`
- dodano `app_cv/tests/test_cv_detection_lab_stage5.py`
- dodano dokumentacje taska Stage 5 benchmark
- zaktualizowano `.ai/TASKS_INDEX.md`
- zaktualizowano plan Stage 5
- brak zmian runtime
- brak identyfikacji kart
- brak ORB / FLANN / template matching / OCR
- brak integracji WebSocket / Studio
- brak zmian `app_ar/`

## TASK-CV-OFFLINE-LAB-STAGE-5-FOREGROUND-MARGIN-FIX-001

- Improved foreground/card bbox estimation for Stage 5 margin metrics.
- Added regression tests for synthetic top margin and background margin behavior.
- Removed the broad brightness-only foreground mask path (`gray > 25`).
- No runtime changes.
- No card identification changes.
- No ORB / FLANN / template matching / OCR.
