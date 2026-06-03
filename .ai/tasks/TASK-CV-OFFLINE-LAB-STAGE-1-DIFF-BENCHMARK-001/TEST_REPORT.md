# Raport z Testów — TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001

## 1. Testy Automatyczne Backend (Python)

* **Status:** `PASS`
* **Komenda uruchomienia 1:** `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 -v`
* **Komenda uruchomienia 2:** `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests -v`

### Wynik konsoli:

```text
Ran 3 tests in 0.130s
OK

Ran 319 tests in 9.370s
OK
```

## 1a. Kompilacja Python

* **Status:** `PASS`
* **Komenda uruchomienia:** `python -B -m py_compile tools\cv_detection_lab\methods.py tools\cv_detection_lab\stage1_diff_benchmark.py app_cv\tests\test_cv_detection_lab_stage1.py`

### Wynik konsoli:

```text
PASS
```

---

## 2. Offline Benchmark

* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage1_diff_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage1_diff`

### Wynik konsoli:

```text
{
  "recommended_method": "gray_absdiff_gaussian",
  "rows": 42
}
```

### Output lokalny:

```text
logs/offline_replay/stage1_diff/matrix.csv
logs/offline_replay/stage1_diff/report.json
logs/offline_replay/stage1_diff/report.md
logs/offline_replay/stage1_diff/<method>/<pair>/{diff,mask,regions_overlay}.png
```

Wygenerowano `126` obrazów debug.

---

## 3. Testy Kompilacji Frontend (Node/Vite)

* **Status:** `NOT_RUN`
* **Uzasadnienie:** task nie modyfikuje `app_ar/`.

---

## 4. Testy Manualne

Nie uruchamiano kamery ani Studio. To jest benchmark offline na zatwierdzonych fixture.
