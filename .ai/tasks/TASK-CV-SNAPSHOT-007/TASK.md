# TASK-CV-SNAPSHOT-007: Recognition-aware snapshot autotuning

## Cel

Dodać scoring autotuningu snapshotów, który uwzględnia nie tylko geometrię wykrytego prostokąta karty, ale też jakość rozpoznania cropa.

## Zakres

- `app_cv/tarotvision/snapshot_autotune.py`
- `app_cv/tarotvision/auto_tuner.py`
- `app_cv/tarotvision/runtime_config.py`
- `app_cv/tests/test_snapshot_autotune.py`
- `app_cv/tests/test_auto_tuner.py`
- `app_cv/tests/test_runtime_config.py`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- `score_snapshot_candidate()` nagradza kandydatów z dobrym rozpoznaniem i karze brak rozpoznania.
- `tune_snapshot_detection_params()` zachowuje wynik geometrycznego autotunera i dodaje `recognition` oraz `recognition_aware_score`.
- `RuntimeConfig.metadata()` eksportuje `CARD_DETECT_MAX_CANDIDATES` i `CARD_DETECT_MIN_AREA_RATIO`.
- Istnieją testy jednostkowe dla scoringu, integracji autotunera i metadanych runtime.
