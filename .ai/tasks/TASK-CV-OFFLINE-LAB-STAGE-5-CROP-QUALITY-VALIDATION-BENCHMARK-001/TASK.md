# TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001

## Goal

Zaimplementowac izolowany offline benchmark Stage 5:

```text
Crop Quality Validation
```

Stage 5 ocenia, czy crop wygenerowany w Stage 4 jest jakosciowo gotowy do przyszlej identyfikacji karty.

## Scope

Dozwolone:

- `tools/cv_detection_lab/crop_quality_methods.py`
- `tools/cv_detection_lab/stage5_crop_quality_validation_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage5.py`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001/`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-5-plan.md`

## Out of Scope

Zakazane:

- Card Identification
- ORB / FLANN recognition
- template matching
- OCR
- porownanie z baza kart
- ML classifier
- runtime integration
- `app_cv/tarotvision/*`
- `app_cv/main.py`
- `app_ar/*`
- WebSocket / Studio UI
- Stage 6

## Files Allowed to Change

- `tools/cv_detection_lab/crop_quality_methods.py`
- `tools/cv_detection_lab/stage5_crop_quality_validation_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage5.py`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001/TASK.md`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001/STATE.md`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001/TEST_REPORT.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-5-plan.md`

## Acceptance Criteria

- Stage 5 benchmark dziala offline bez kamery, Studio i WebSocket.
- Uzywa Stage 1 `gray_absdiff_gaussian`, Stage 2 `contour_external`, Stage 3 `hybrid_edge_plus_contour` i Stage 4 `quad_warp_perspective_fixed_aspect__resize_only_normalization`.
- Testuje 6 par fixture.
- Dla `removed` uzywa `previous_snapshot` jako `crop_source_frame`.
- Generuje `matrix.csv`, `report.json`, `report.md` i crop quality debug sheets.
- Generuje `crop_XX_quality_overlay.png` i `crop_XX_metrics.json`.
- Raportuje quality flags, `crop_quality_score` i `identification_readiness_score`.
- Oznacza progi jako `BENCHMARK_HEURISTIC_ONLY`.
- Nie identyfikuje kart.
- Nie tworzy plikow ORB/template/classification/OCR.
- Nie dotyka runtime.
- Testy Stage 5 PASS.
- Testy Stage 1/2/3/4 nadal PASS.
- Full backend suite PASS.
- Wynik jest tylko `PROVISIONAL_RECOMMENDED`, nie final `APPROVED`.

## Tests Required

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage5 -v
python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 app_cv.tests.test_cv_detection_lab_stage3 app_cv.tests.test_cv_detection_lab_stage4 -v
python -B -m py_compile tools\cv_detection_lab\crop_quality_methods.py tools\cv_detection_lab\stage5_crop_quality_validation_benchmark.py app_cv\tests\test_cv_detection_lab_stage5.py
python tools\cv_detection_lab\stage5_crop_quality_validation_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage5_crop_quality_validation
python -m unittest discover -s app_cv\tests -v
```

Frontend:

```text
NOT_RUN
```

Uzasadnienie: task nie zmienia `app_ar/`.

## Reports Required

- `STATE.md`
- `CHANGELOG.md`
- `TEST_REPORT.md`

## Branch

```text
task/cv-event-first-plan-001-clarify-autotune-runtime
```

## Commit Message

```text
feat: uruchom benchmark stage5 crop quality
```
