# Wykaz Zmian — TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001

## 1. Modyfikowane Pliki Produkcyjne

Brak zmian w runtime produkcyjnym.

---

## 2. Nowe Narzędzia Offline

### `tools/cv_detection_lab/methods.py`

* Dodano metody różnicowania obrazów dla Stage 1: grayscale fixed, Gaussian, median, Otsu, LAB weighted, HSV weighted i illumination-normalized grayscale.

### `tools/cv_detection_lab/stage1_diff_benchmark.py`

* Dodano CLI benchmarku, loader fixture, generowanie par testowych, ekstrakcję regionów, zapis `matrix.csv`, `report.json`, `report.md` i obrazów debug.

---

## 3. Pliki Testowe

### `app_cv/tests/test_cv_detection_lab_stage1.py`

* Testuje budowę par fixture.
* Testuje zapis raportów i obrazów debug.
* Testuje, że baseline `empty -> empty` daje `PASS` i zero regionów.

---

## 4. Dokumentacja

### `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/`

* Dodano komplet dokumentów taska.

### `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-1-plan.md`

* Dopisano wyniki pierwszego benchmarku offline.
