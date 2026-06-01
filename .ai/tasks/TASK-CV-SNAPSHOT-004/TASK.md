# TASK-CV-SNAPSHOT-004: Diagnostyka porazek snapshot-first

## Cel

Dodac minimalna diagnostyke etapow detekcji i rozpoznania, zeby kolejne taski mogly odroznic problem lokalizacji karty od problemu ORB/matchingu.

## Zakres

- `app_cv/tarotvision/recognition_debug.py`
- `app_cv/tarotvision/card_detection_debug.py`
- `app_cv/tarotvision/card_recognition.py`
- `app_cv/tarotvision/snapshot_analyzer.py`
- `app_cv/tarotvision/pipelines/snapshot_first.py`
- `app_cv/tests/test_recognition_debug.py`
- `app_cv/tests/test_snapshot_analyzer.py`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- `SnapshotAnalysisResult` zawiera `diagnostics`.
- Analyzer raportuje `quads_found`, `recognition_attempts` i `recognition_rejections`.
- Pipeline publikuje metryki `snapshot_quads_found`, `snapshot_recognition_attempts` i `snapshot_recognition_rejections`.
- `recognize_card_crop()` zachowuje dotychczasowe API, a nowa funkcja debugowa jest osobna.
