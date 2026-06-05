# Changelog for TASK-CV-STAGE-6-RWS-AUTOTUNE-RUNTIME-COMMANDS-001

## [Released] - 2026-06-05
- **main.py**: Dodano obsługę komend WebSocket dla autotuningu (`autotune_start`, `autotune_calibrate`, `autotune_cancel`, `autotune_apply`, `autotune_save`).
- **main.py**: Zintegrowano globalny stan sesji autotuningu oparty o klasy `AutotuneSession`, `AutotuneSessionLog` oraz `ProfileStore`.
- **main.py**: Rozszerzono `build_operator_snapshot` o dynamiczną strukturę `calibration.autotune` o schemacie wymaganym przez Studio UI.
- **status_store.py**: Dodano domyślną strukturę `calibration.autotune` (w stanie `idle`) przy inicjalizacji `StatusStore`.
- **test_autotune_lifecycle.py**: Dodano dedykowany zestaw testów jednostkowych weryfikujących cykl życia i walidację komend autotuningu.
