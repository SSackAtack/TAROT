# TASK-CV-SNAPSHOT-008: Local benchmark script dla talii i mat

## Cel

Dodać stabilny kontrakt lokalnego benchmarku snapshot recognition dla próbek operatorskich z różnych talii i mat.

## Zakres

- `scripts/benchmark_snapshot_recognition.py`
- `app_cv/tests/test_benchmark_snapshot_recognition.py`
- `README.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- Skrypt czyta próbki z `testdata/snapshots/{deck_id}/{mat_id}/*.jpg`.
- Skrypt zapisuje CSV z kolumnami `path`, `deck_id`, `mat_id`, `accepted`, `card_count`.
- `summarize_results()` raportuje `total`, `accepted` i `accept_rate`.
- Repo nie zawiera fizycznych próbek kamery.
- `.gitignore` blokuje lokalne próbki `testdata/snapshots/`.
