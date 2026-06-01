# CHANGELOG: TASK-CV-SNAPSHOT-008

## 2026-06-01

- Dodano `scripts/benchmark_snapshot_recognition.py`.
- Dodano test kontraktu `app_cv/tests/test_benchmark_snapshot_recognition.py`.
- Udokumentowano lokalną konwencję próbek `testdata/snapshots/{deck_id}/{mat_id}/*.jpg` w README.
- Dodano `testdata/snapshots/` do `.gitignore`, żeby lokalne próbki z kamery nie trafiły przypadkiem do repo.
- Poprawiono test kontraktu benchmarku, aby importował `scripts/` poprawnie także wtedy, gdy CI uruchamia testy z katalogu `app_cv`.
