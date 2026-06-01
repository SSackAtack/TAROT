# TASK-CV-SNAPSHOT-001: Snapshot-first jako jedyny pipeline CV

## Cel

Usunac runtime legacy state-first z backendu CV i utrwalic `SnapshotFirstPipeline` jako jedyna produkcyjna sciezke rozpoznawania kart.

## Zakres

- `app_cv/main.py`
- `app_cv/tarotvision/pipelines/__init__.py`
- `app_cv/tarotvision/pipelines/state_first_legacy.py`
- `app_cv/tests/test_pipelines_contract.py`
- `app_cv/tests/test_main_static_audit.py`
- `README.md`
- `.ai/PROJECT_STATE.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- `main.py` nie importuje, nie inicjalizuje i nie branchuje do `StateFirstLegacyPipeline`.
- `TAROTVISION_SNAPSHOT_FIRST` nie decyduje o runtime CV.
- `tarotvision.pipelines.__all__` eksportuje tylko `VisionPipeline` i `SnapshotFirstPipeline`.
- Test statyczny blokuje powrot `StateFirstLegacyPipeline`, `legacy_pipeline`, `USE_SNAPSHOT_FIRST_CV` i `USE_TABLE_CARD_DETECTION` do `main.py`.
- Dokumentacja opisuje snapshot-first jako jedyna sciezke produkcyjna.
