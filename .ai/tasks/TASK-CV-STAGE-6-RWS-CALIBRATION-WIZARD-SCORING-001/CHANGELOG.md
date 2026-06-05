# Changelog for TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SCORING-001

## [Released] - 2026-06-05
- **calibration_wizard_scoring.py**: Utworzono dedykowany moduł z logiką scoringu próbek asystenta kalibracji. Wylicza on średnie metryki dla aktywnych scenariuszy, ocenia je pod kątem progów (pewność rozpoznania, fałszywi kandydaci, odrzucenia geometryczne, czas analizy) i zwraca JSON-safe raport z oceną stanowiska (`score`, `grade`, `warnings`, `blocking_issues` i `ready_for_session`).
- **main.py**: Zintegrowano scoring z runtime: dodano globalny raport `autotune_quality_report`, wyzwalany w komendzie `autotune_calibrate` po zgromadzeniu próbek. Zaktualizowano `autotune_status_payload()`, aby wstrzykiwać raport do statusu WebSocket.
- **main.py**: Wdrożono mechanizm resetowania raportu przy komendach startu (`autotune_start`) i anulowania (`autotune_cancel`) sesji wizardu.
- **test_calibration_wizard_scoring.py**: Dodano 9 testów jednostkowych weryfikujących poprawność reguł scoringowych, odporność na brakujące klucze i serializację JSON.
- **test_calibration_wizard_scoring_integration.py**: Dodano 5 testów integracyjnych badających poprawne przejścia stanu i resetowanie raportu w integracji z główną logiką WebSocket backendu.
