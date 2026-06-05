# TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## 1. Cel i Tło Techniczne

Celem zadania jest wyjaśnić, dlaczego scenariusz `one_card` w Calibration Wizard ma poprawną geometrię (`detected_count=1` dla 3/3 próbek), ale nie przechodzi acceptance/recognition (`accepted_total=1/3`) przy fizycznej talii Gilded i aktywnej talii runtime `gilded`.

Poprzedni task `TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-GEOMETRY-STABILIZATION-001` potwierdził:

- `empty`: PASS bez false positives.
- `one_card` geometria: PASS, `detected_count=1` dla wszystkich 3 próbek.
- `one_card` acceptance: FAIL, `accepted_total=1/3`.
- fizyczna talia: Gilded.
- aktywna talia runtime/Studio: `gilded`.

Problem nie jest już traktowany jako geometria konturu. Następny root cause może leżeć w jakości cropa, deskew/orientacji, progach recognition, danych referencyjnych talii Gilded albo w sposobie raportowania acceptance w Calibration Wizard.

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

> [!IMPORTANT]
> Najpierw diagnostyka. Nie luzować progów recognition ani acceptance bez dowodów.

### Pliki Dopuszczone do Inspekcji

* `app_cv/tarotvision/snapshot_analyzer.py`
* `app_cv/tarotvision/card_recognition.py`
* `app_cv/tarotvision/pipelines/snapshot_first.py`
* `app_cv/main.py`
* `app_cv/tarotvision/calibration_wizard_scoring.py`
* `app_cv/tests/test_snapshot_analyzer.py`
* `app_cv/tests/test_autotune_pipeline_sample_capture.py`
* `app_cv/tests/test_calibration_wizard_scoring.py`
* `logs/autotune_sessions/`
* `logs/debug_calibration/`
* `logs/cv_runtime.log`

### Pliki Dopuszczone do Modyfikacji

Preferowany zakres produkcyjny, maksymalnie 1-3 pliki:

* `[MODIFY optional]` `app_cv/tarotvision/snapshot_analyzer.py`
* `[MODIFY optional]` `app_cv/tarotvision/card_recognition.py`
* `[MODIFY optional]` `app_cv/tarotvision/pipelines/snapshot_first.py`
* `[MODIFY optional]` `app_cv/main.py` tylko jeśli potrzebne do minimalnej diagnostyki runtime
* `[MODIFY optional]` `app_cv/tarotvision/calibration_wizard_scoring.py` tylko jeśli root cause jest w scoringu, nie w recognition

Testy:

* `[MODIFY optional]` `app_cv/tests/test_snapshot_analyzer.py`
* `[MODIFY optional]` `app_cv/tests/test_autotune_pipeline_sample_capture.py`
* `[MODIFY optional]` `app_cv/tests/test_calibration_wizard_scoring.py`

Dokumentacja:

* `[NEW/MODIFY]` `.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001/*`
* `[MODIFY]` `.ai/TASKS_INDEX.md`

---

## 3. Poza Zakresem (Out of Scope)

* Nie zmieniać `app_cv/tarotvision/card_detection_profiles.py` ani dalszych progów geometrii.
* Nie zmieniać `app_ar/public/active_decks.json`; lokalna zmiana `gilded` jest poza zakresem commita.
* Nie zmieniać frontend UI.
* Nie zmieniać WebSocket API.
* Nie dodawać nowych bibliotek.
* Nie zmieniać aktywnych talii poza manualnym smoke testem operatora.
* Nie robić dużej przebudowy ORB/FLANN ani loadera wzorców bez osobnej decyzji Michała.

---

## 4. Wymagana Diagnostyka

Zebrać dowody dla 3 próbek `one_card` z poprawną geometrią Gilded:

- `detected_count`
- `candidate_count`
- `accepted_count`
- `recognition_rejections`
- `recognition_confidences`
- nazwa najlepszego dopasowania, jeśli istnieje
- liczba keypointów cropa i referencji, jeśli dostępna
- liczba raw matches / good matches / inliers, jeśli dostępna
- orientacja (`upright` / `reversed` / `unknown`)
- powód odrzucenia recognition, jeśli istnieje
- ścieżka debug cropa albo snapshotu dla odrzuconych próbek

Minimalny wynik diagnostyczny musi odpowiedzieć:

1. Czy crop z odrzuconych próbek jest poprawny wizualnie?
2. Czy recognition nie zwraca wyniku, bo brakuje matchy?
3. Czy wynik istnieje, ale odpada przez `MIN_MATCH_COUNT`, `RATIO_THRESH` albo `MIN_INLIER_RATIO`?
4. Czy orientacja/reversed wpływa na confidence?
5. Czy problem dotyczy konkretnej karty Gilded, czy losowej jakości próbek?
6. Czy scoring wizardu wymaga `accepted_count=1` we wszystkich 3 próbkach, a recognition akceptuje tylko 1 z nich?

---

## 5. Kryteria Akceptacji

Zadanie uznaje się za ukończone diagnostycznie, gdy:

- [ ] Root cause `accepted_total=1/3` jest wskazany na podstawie danych, nie zgadywania.
- [ ] Jeśli fix jest mały i bezpieczny, dodano test jednostkowy przed zmianą.
- [ ] Jeśli fix nie jest mały, task kończy się raportem `DIAGNOSTIC_COMPLETE_FIX_REQUIRED`.
- [ ] `one_card` po zgodnej talii Gilded osiąga `accepted_total=3/3` albo raport wyjaśnia, dlaczego nie.
- [ ] `empty` pozostaje PASS po ewentualnym fixie.
- [ ] Nie ma zmian w geometrii.
- [ ] `app_ar/public/active_decks.json` nie trafia do commita.

---

## 6. Testy Wymagane

Minimalnie po zmianach kodu:

```powershell
$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_snapshot_analyzer -v
$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_autotune_pipeline_sample_capture -v
$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_calibration_wizard_scoring -v
$env:PYTHONPATH="app_cv"; python -m unittest discover -s app_cv/tests -p "test_*.py"
```

Frontend build:

```text
NOT_RUN — frontend not changed
```

Manual smoke po fixie albo po diagnostyce:

```text
ONE_CARD Gilded
- detected_count:
- accepted_total:
- stage_result:
- recognition rejection reason:
```
