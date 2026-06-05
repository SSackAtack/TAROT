# Changelog for TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STATUS-SNAPSHOT-001

## [Released] - 2026-06-05
- **calibration_wizard_status.py [NEW]**: Utworzono moduł budowania statusu asystenta kalibracji. Zapewnia on spójny, kompletny i JSON-safe kontrakt WebSocket niezależnie od stanu sesji (w tym w stanie `idle` i `collecting`).
- **main.py [MODIFY]**: Zrefaktoryzowano funkcję `autotune_status_payload()`, zastępując surowe słowniki wywołaniem nowej funkcji `build_calibration_wizard_status`.
- **test_calibration_wizard_status.py [NEW]**: Dodano 13 testów jednostkowych i integracyjnych weryfikujących poprawność pól, odporność na brakujące klucze sesji/raportu oraz serializację.
- **Contract updates**: Dodano nowe pola pomocnicze dla Studio UI (`schema_version = 1`, `mode = "calibration_wizard"`, `current_step_ready`, `overall_wizard_ready = False`, `warnings`, `blocking_issues`).
