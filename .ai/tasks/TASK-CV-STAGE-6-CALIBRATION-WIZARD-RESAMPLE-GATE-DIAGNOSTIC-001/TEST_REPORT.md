# TEST REPORT: TASK-CV-STAGE-6-CALIBRATION-WIZARD-RESAMPLE-GATE-DIAGNOSTIC-001

## Rezultaty testów jednostkowych

Uruchomiono pełny suite testów backendowych poleceniem:
`cmd.exe /c "set PYTHONPATH=app_cv && python -m unittest discover -s app_cv/tests -p \"test_*.py\""`

### Rezultat końcowy
- **Status**: **PASS (OK)**
- **Liczba wykonanych testów**: 423
- **Czas wykonania**: 21.454s

### Przebieg testów jednostkowych bramki i zbierania próbek
- Testy bramki `SnapshotGate` (w tym nowy test `test_re_arms_after_publish_or_reject`) -> PASS (6/6)
- Testy zbierania próbek `test_autotune_pipeline_sample_capture` -> PASS (13/13)
