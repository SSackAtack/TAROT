# State of TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SAMPLE-CAPTURE-001

## Status
DONE

## Session Status (2026-06-05)
Wdrożono i pomyślnie zweryfikowano mechanizm kontrolowanego zbierania próbek wizardu kalibracji w integracji ze `SnapshotFirstPipeline`.

## Checklist
- [x] Modyfikacja `SnapshotFirstPipeline` - dodanie callbacku `autotune_sample_recorder` i wywołanie go po analizie.
- [x] Modyfikacja `main.py` - implementacja callbacku `record_autotune_sample_from_snapshot` i przekazanie go do pipeline.
- [x] Dodanie w `main.py` walidacji zgodności liczby kart z aktywnym scenariuszem.
- [x] Utworzenie testów jednostkowych w `app_cv/tests/test_autotune_pipeline_sample_capture.py`.
- [x] Uruchomienie automatycznych testów.
- [x] Smoke test z uruchomieniem backendu i weryfikacją procesu zbierania próbek.
