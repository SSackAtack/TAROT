# TASK-CV-SNAPSHOT-003: Warp ArUco przed analiza snapshotu

## Cel

Uzyc sprostowanej klatki stolu z `TableCalibration.warp_frame()` jako wejscia do `SnapshotAnalyzer`, gdy kalibracja ArUco jest dostepna.

## Zakres

- `app_cv/tarotvision/pipelines/snapshot_first.py`
- `app_cv/tests/test_pipelines_contract.py`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- Przy `table_calibration.calibrated == True` pipeline przekazuje do `snapshot_analyzer.analyze()` wynik `warp_frame()`.
- Gdy `warp_frame()` zwroci `None` albo tabela nie jest skalibrowana, pipeline analizuje oryginalny snapshot.
- Metryka `snapshot_analysis_warped` pokazuje `1` dla analizy po warp i `0` dla fallbacku.
