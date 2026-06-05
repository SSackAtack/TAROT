# TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001 — Offline Stage 1 Difference Benchmark

## 1. Cel i Tło Techniczne

Ten task implementuje pierwszy techniczny element nowej strategii state-first: izolowany benchmark offline dla Stage 1 Difference Detection.

Benchmark porównuje zatwierdzone fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

i generuje:

- macierz wyników,
- raport JSON/Markdown,
- obrazy debug: `diff.png`, `mask.png`, `regions_overlay.png`.

---

## 2. Rygorystyczny Zakres Modyfikacji

### Pliki Dopuszczone do Modyfikacji

* `[NEW]` `tools/__init__.py`
* `[NEW]` `tools/cv_detection_lab/__init__.py`
* `[NEW]` `tools/cv_detection_lab/methods.py`
* `[NEW]` `tools/cv_detection_lab/stage1_diff_benchmark.py`
* `[NEW]` `app_cv/tests/test_cv_detection_lab_stage1.py`
* `[NEW]` `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/TASK.md`
* `[NEW]` `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/STATE.md`
* `[NEW]` `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/CHANGELOG.md`
* `[NEW]` `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/TEST_REPORT.md`
* `[MODIFY]` `.ai/TASKS_INDEX.md`
* `[MODIFY]` `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-1-plan.md`

---

## 3. Poza Zakresem

Nie zmieniano:

* runtime CV,
* Studio UI,
* WebSocket protocol,
* ArUco calibration,
* ORB / FLANN thresholds,
* candidate validation,
* istniejącego `ChangeDetector`.

Nie dodano nowych bibliotek.

---

## 4. Kryteria Akceptacji

- [x] Benchmark działa offline bez kamery i bez Studio.
- [x] Benchmark używa zatwierdzonych fixture jako wejścia.
- [x] Każda metoda generuje metryki i debug obrazy.
- [x] `matrix.csv` zawiera metody, pary, runtime, region count, expected region count i verdict.
- [x] `report.json` i `report.md` wskazują rekomendowaną metodę.
- [x] Testy jednostkowe sprawdzają fixture pairs, zapis raportów i baseline no-change.
