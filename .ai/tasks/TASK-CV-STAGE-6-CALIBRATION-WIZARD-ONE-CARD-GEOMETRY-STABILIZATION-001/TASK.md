# TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-GEOMETRY-STABILIZATION-001

## Goal

Ustabilizować detekcję geometryczną jednej karty (`one_card`) w Calibration Wizard tak, aby scenariusz `one_card` mógł dojść do 3/3 na fizycznym stanowisku operatorskim.

Problem nie dotyczy `SnapshotGate` ani ponownego wyzwalania snapshotów. Poprzedni task potwierdził, że bramka snapshotów re-armuje się poprawnie, a system reaguje na ruch. Aktualny problem: detektor geometryczny często zwraca `detected_count = 0` albo `detected_count = 2` zamiast oczekiwanego `1`.

## Current Verified State

* `empty`: PASS.
* `one_card`: DIAGNOSTIC_PASS / CALIBRATION_FAIL.
* `three_cards`: NOT_RUN.
* HUD / next_action poprawnie pokazuje powód odrzucenia.
* Problem leży po stronie geometrii detektora, nie po stronie recognition/ORB.

## Scope

Najpierw diagnostyka, dopiero potem minimalny fix.

Do sprawdzenia:

1. Dlaczego pojedyncza karta w realnym obrazie jest wykrywana jako:
   * `0` kandydatów,
   * albo `2` kandydatów.
2. Który profil geometrii daje wynik:
   * `canny_low`,
   * `canny_default`,
   * `adaptive_light`,
   * `adaptive_dark`,
   * `min_area_rect`,
   * ewentualnie `background_diff`.
3. Jakie są powody odrzucenia konturów:
   * `area`,
   * `non_quad`,
   * `non_convex`,
   * `aspect`,
   * `min_area_rect_aspect`.
4. Czy problem wynika z:
   * zbyt słabych krawędzi karty,
   * odbić światła,
   * zbyt ciemnej / zbyt jasnej maty,
   * cienia dłoni,
   * zbyt ostrego `min_area_ratio`,
   * błędnej deduplikacji,
   * rozbicia jednej karty na dwa kontury,
   * wykrywania elementów tła jako dodatkowych kandydatów.

## Out of Scope

Nie zmieniać:

* ORB / FLANN / recognition.
* aktywnych talii.
* WebSocket payload poza istniejącymi polami diagnostycznymi.
* frontend UI, chyba że jest konieczne pokazanie istniejącej diagnostyki.
* algorytmu Calibration Wizard jako całości.
* `SnapshotGate`.
* dużego refaktoru `main.py`.

Nie dodawać nowych bibliotek.

## Files Allowed to Inspect

* `app_cv/tarotvision/card_detection.py`
* `app_cv/tarotvision/card_detection_profiles.py`
* `app_cv/tarotvision/snapshot_analyzer.py`
* `app_cv/tarotvision/pipelines/snapshot_first.py`
* `app_cv/main.py`
* `app_cv/tests/test_card_detection.py`
* `app_cv/tests/test_snapshot_analyzer.py`
* `app_cv/tests/test_autotune_pipeline_sample_capture.py`
* logs:
  * `logs/cv_runtime.log`
  * `logs/cv_metrics.jsonl`
  * debug snapshots/crops, jeśli istnieją

## Files Allowed to Change

Preferowany mały zakres:
* `app_cv/tarotvision/card_detection.py`
* `app_cv/tarotvision/card_detection_profiles.py`
* `app_cv/tests/test_card_detection.py`
* `.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-GEOMETRY-STABILIZATION-001/*`
* `.ai/TASKS_INDEX.md`

Opcjonalnie, tylko jeśli potrzebne do zebrania dowodów:
* `app_cv/tarotvision/snapshot_analyzer.py`
* `app_cv/tarotvision/pipelines/snapshot_first.py`
* `app_cv/main.py`

Limit produkcyjny: maksymalnie 1–3 pliki produkcyjne. Jeśli potrzeba więcej, zatrzymać task i zgłosić Human Override.

## Required Diagnostic Evidence

Przed zmianą progów lub algorytmu zebrać dowody:

1. Minimum 3 przypadki `one_card` z wynikiem `detected_count = 0`.
2. Minimum 3 przypadki `one_card` z wynikiem `detected_count = 2`, jeśli występują.
3. Dla każdego przypadku zapisać:
   * obraz wejściowy / snapshot debug,
   * `best_profile`,
   * `quads_final`,
   * `profiles[*].quads`,
   * `profiles[*].reject_reasons`,
   * `contours_total`,
   * `candidates_after_quad`,
   * `min_area_rect_candidates`,
   * `min_area_rect_accepted`.

Jeśli nie da się automatycznie zapisać obrazu wejściowego, dodać minimalny tryb debug tylko dla Calibration Wizard / one_card. Debug nie może zapychać dysku — maksymalnie kilka ostatnich snapshotów albo zapis tylko przy odrzuceniu.

## Preferred Fix Direction

Najpierw sprawdzić, czy problem da się rozwiązać parametrycznie:

1. Delikatne dostrojenie profili in `card_detection_profiles.py`.
2. Lepsza deduplikacja kandydatów, jeśli jedna karta daje dwa quady.
3. Lepsza selekcja najlepszego profilu dla scenariusza `one_card`.
4. Bezpieczny fallback `min_area_rect`, jeśli strict quad detection gubi kartę.
5. Ewentualnie osobny profil `calibration_one_card`, ale tylko jeśli zwykłe profile nie wystarczą.

Nie robić dużej przebudowy detektora.

## Acceptance Criteria

1. `empty` nadal przechodzi 3/3.
2. `one_card` na fizycznym stanowisku:
   * licznik dochodzi do 3/3,
   * bez ręcznego restartowania kreatora,
   * po normalnym ruchu dłonią/kartą,
   * z jasną diagnostyką przy odrzuceniach.
3. `one_card` nie generuje wielu fałszywych kandydatów na pustej macie.
4. Jeśli `three_cards` nie jest testowane w tym tasku, musi być oznaczone jako NOT_RUN.
5. Nie ma regresji w testach `card_detection`, `snapshot_analyzer`, `autotune_pipeline_sample_capture`.
6. Nie ma zmian w ORB/recognition.
7. Nie ma zmian w frontendzie bez uzasadnienia.

## Tests Required

Minimum:
```bash
set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_card_detection -v
set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_snapshot_analyzer -v
set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_autotune_pipeline_sample_capture -v
set PYTHONPATH=app_cv && python -m unittest discover -s app_cv/tests -p "test_*.py"
```

Jeśli dotknięto frontend lub payload widoczny w Studio:
```bash
npm --prefix app_ar run build
```
