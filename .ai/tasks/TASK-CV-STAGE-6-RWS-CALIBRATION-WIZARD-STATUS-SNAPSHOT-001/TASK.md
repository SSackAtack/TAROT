# TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STATUS-SNAPSHOT-001

## Cel
Ustabilizować backendowy status snapshot dla Calibration Wizard. Zapewnić kompletną, przewidywalną, JSON-safe strukturę danych pod kluczem `calibration.autotune`, eliminując konieczność sprawdzania istnienia poszczególnych pól w Studio UI.

## Zakres
- Utworzenie modułu `calibration_wizard_status.py` z funkcją `build_calibration_wizard_status`.
- Integracja buildera w `main.py` w funkcji `autotune_status_payload()`.
- Zapewnienie pełnej kompatybilności wstecznej (nie usuwamy starych pól).
- Dodanie nowych pól kontraktowych dla UI: `schema_version`, `mode`, `current_step_ready`, `overall_wizard_ready`, `warnings`, `blocking_issues`.
- Utrzymanie podziału na `recommendation` oraz `quality_report`.
- Wdrożenie testów jednostkowych w `test_calibration_wizard_status.py`.

## Kryteria akceptacji
- Status payload jest stabilny i ma kompletny zbiór pól w stanach `idle`, `collecting` i po wyliczeniu raportu.
- `schema_version` jest ustawiona na `1`.
- `mode` jest ustawiona na `"calibration_wizard"`.
- `current_step_ready` jest aliasem dla `ready_for_session` z raportu.
- `overall_wizard_ready` wynosi `False`.
- `autotune_apply` i `autotune_save` działają poprawnie.
- Wszystkie testy automatyczne i integracyjne przechodzą pomyślnie.
