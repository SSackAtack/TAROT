# TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001 — Research Stage 1 Difference Detection

## 1. Cel i Tło Techniczne

Etap koncepcyjny nowego silnika CV został zakończony. Dalsze prace nie mają łatać obecnego runtime pipeline. Ten task uruchamia pierwszy obowiązkowy Research Gate dla izolowanego offline labu state-first.

Celem jest wybrać metody warte przetestowania w Stage 1, czyli w detekcji różnic między stabilnymi snapshotami:

```text
empty_reference + previous_snapshot + current_snapshot + known_cards
```

Na tym etapie nie lokalizujemy jeszcze kart, nie rozpoznajemy nazw i nie zmieniamy runtime. Badamy tylko, które techniki mogą wiarygodnie odpowiedzieć:

- czy zaszła istotna zmiana,
- gdzie zaszła zmiana,
- ile jest głównych regionów zmiany,
- czy zmiana jest lokalna czy globalna.

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

> [!IMPORTANT]
> To jest task researchowo-planistyczny. Nie wolno zmieniać kodu produkcyjnego runtime ani progów obecnego pipeline.

### Pliki Dopuszczone do Modyfikacji

* `[NEW]` `.ai/tasks/TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001/TASK.md`
* `[NEW]` `.ai/tasks/TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001/STATE.md`
* `[NEW]` `.ai/tasks/TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001/CHANGELOG.md`
* `[NEW]` `.ai/tasks/TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001/TEST_REPORT.md`
* `[NEW]` `.ai/tasks/TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001/RESEARCH_REPORT.md`
* `[MODIFY]` `.ai/TASKS_INDEX.md`
* `[NEW]` `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-1-plan.md`

---

## 3. Poza Zakresem (Out of Scope)

Nie wolno w tym zadaniu zmieniać:

* `app_cv/tarotvision/pipelines/snapshot_first.py`
* `app_cv/tarotvision/snapshot_analyzer.py`
* `app_cv/tarotvision/change_detection.py`
* `app_cv/tarotvision/background_model.py`
* `app_cv/main.py`
* `app_ar/`
* WebSocket protocol
* ArUco calibration
* ORB / FLANN thresholds
* candidate validation
* runtime empty reference behavior

Nie wolno dodawać nowych bibliotek. Research może oznaczyć metodę jako `REQUIRES_APPROVAL`, ale nie daje zgody na zależność.

---

## 4. Kryteria Akceptacji

Zadanie uznaje się za ukończone, gdy:

- [x] Powstał raport researchowy Stage 1.
- [x] Powstała macierz technik z decyzjami `TEST_NOW`, `TEST_LATER`, `REJECT_FOR_NOW`, `REQUIRES_APPROVAL`.
- [x] Powstał benchmark plan dla par fixture `empty`, `one_card`, `three_cards`.
- [x] Powstał plan wykonawczy dla kolejnego taska offline benchmarku.
- [x] `.ai/TASKS_INDEX.md` zawiera wpis taska.
- [x] Nie zmieniono kodu runtime ani frontendu.
