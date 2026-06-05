# Changelog for TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SAMPLE-CAPTURE-001

## [Released] - 2026-06-05
- **snapshot_first.py**: Dodano opcjonalny callback `autotune_sample_recorder` do klasy `SnapshotFirstPipeline` oraz wywołanie go po wykonaniu analizy klatki snapshotu.
- **main.py**: Zaimplementowano funkcję callback `record_autotune_sample_from_snapshot` i przekazano ją do konstruktora `SnapshotFirstPipeline`.
- **main.py**: Wprowadzono walidację zgodności wykrytych kart z oczekiwaną liczbą dla aktywnego scenariusza (`empty` -> 0, `one_card` -> 1, `three_cards` -> 3).
- **test_autotune_pipeline_sample_capture.py**: Utworzono 9 nowych testów jednostkowych weryfikujących poprawność zbierania próbek wizardu w integracji z potokiem wideo.
