# CHANGELOG: TASK-CV-STAGE-6-CALIBRATION-WIZARD-RESAMPLE-GATE-DIAGNOSTIC-001

## Wersja 1.0.0 (2026-06-05)

- **app_cv/main.py**: Wdrożono szczegółową diagnostykę HUD (za pomocą `add_operator_warning`) oraz logowanie `[WIZARD DIAG]` w `record_autotune_sample_from_snapshot` informujące o powodzie odrzucenia/akceptacji próbki.
- **app_cv/tests/test_snapshot_gate.py**: Dodano test jednostkowy `test_re_arms_after_publish_or_reject` weryfikujący poprawne re-armowanie bramki.
- **app_cv/tests/test_autotune_pipeline_sample_capture.py**: Zaktualizowano asercje o weryfikację poprawności generowanych warningów.
