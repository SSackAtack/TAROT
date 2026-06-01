# CHANGELOG: TASK-CV-SNAPSHOT-006

## 2026-06-01

- Dodano `BackgroundModel` z `capture`, `clear` i `foreground_mask`.
- Dodano parsing `background_capture` i `background_clear`.
- Dodano flagę `pending_background_capture` w `main.py`.
- Podłączono `background_model` do `SnapshotAnalyzer` i `find_card_quads_multi_profile()`.
- Dodano testy modelu tła i profilu `background_diff`.
