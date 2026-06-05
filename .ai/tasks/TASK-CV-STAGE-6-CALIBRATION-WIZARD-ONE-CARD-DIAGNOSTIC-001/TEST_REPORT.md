# TEST REPORT: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-DIAGNOSTIC-001

## Rezultaty testów jednostkowych

Uruchomiono pełny suite testów backendowych poleceniem:
`cmd.exe /c "set PYTHONPATH=app_cv && python -m unittest discover -s app_cv/tests -p \"test_*.py\""`

### Rezultat końcowy
- **Status**: **PASS (OK)**
- **Liczba wykonanych testów**: 421
- **Czas wykonania**: 17.844s

### Przebieg testów zbierania próbki
Pomyślnie wykonano wszystkie 12 testów z pliku `app_cv/tests/test_autotune_pipeline_sample_capture.py` (w tym nowo dodane testy):
- `test_collects_unrecognized_one_card_sample` -> PASS
- `test_collects_partially_recognized_three_cards_sample` -> PASS
- `test_collects_empty_sample_with_false_positives` -> PASS
- `test_collects_one_card_sample_when_expected_count_one` -> PASS
- `test_collects_three_cards_sample_when_expected_count_three` -> PASS
