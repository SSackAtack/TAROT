# TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001

## Cel

Zaimplementować izolowany offline benchmark Stage 4 Crop / Deskew / Normalize.

## Kontekst

Zatwierdzony pipeline wejściowy:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
Stage 3: hybrid_edge_plus_contour
```

## Zakres

Dozwolone:

- `tools/cv_detection_lab/crop_deskew_methods.py`
- `tools/cv_detection_lab/stage4_crop_deskew_normalize_benchmark.py`
- `app_cv/tests/test_cv_detection_lab_stage4.py`
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001/`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-4-plan.md`

## Poza zakresem

- Identyfikacja kart
- ORB / FLANN / template matching
- Integracja runtime
- WebSocket / Studio UI
- Stage 5 / Stage 6

## Kryteria akceptacji

- Stage 4 benchmark działa offline bez kamery, Studio i WebSocket
- Używa Stage 1/2/3 jako wejścia
- Testuje 6 par fixture
- Dla removed używa previous_snapshot
- Generuje matrix.csv, report.json, report.md i crop debug sheets
- Nie identyfikuje kart
- Testy Stage 4 PASS
- Testy Stage 1/2/3 nadal PASS
- Full backend suite PASS
- Wynik jest tylko PROVISIONAL_RECOMMENDED

## Branch

```text
task/cv-event-first-plan-001-clarify-autotune-runtime
```

## Commit Message

```text
feat: uruchom benchmark stage4 crop deskew normalize
```
