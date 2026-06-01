# CHANGELOG: TASK-CV-SNAPSHOT-001

## 2026-06-01

- Dodano guard w `test_main_static_audit.py` przeciw runtime fallbackowi state-first.
- Usunieto kontrakt testowy `StateFirstLegacyPipeline`.
- Usunieto eksport i plik `state_first_legacy.py`.
- Przestawiono `main.py` na bezwarunkowe wywolanie `SnapshotFirstPipeline`.
- Zaktualizowano README i `.ai/PROJECT_STATE.md` pod snapshot-first-only.
