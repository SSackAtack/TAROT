# CHANGELOG: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-DIAGNOSTIC-001

## Wersja 1.0.0 (2026-06-05)

- **app_cv/main.py**: Zmieniono warunek zbierania próbki w `record_autotune_sample_from_snapshot` na oparty o detekcję geometryczną (`detected_count == expected_count`) zamiast rozpoznania dla scenariuszy `one_card` i `three_cards`.
- **app_cv/main.py**: Uzupełniono słownik próbki o klucze `"candidate_count"`, `"false_positive_count"`, `"geometry_score"`, `"recognition_score"`, `"matching_ms"`.
- **app_cv/tests/test_autotune_pipeline_sample_capture.py**: Zaktualizowano testy i dodano asercje weryfikujące poprawność nowo wprowadzonych pól oraz zbieranie próbek bez pełnego rozpoznania kart.
