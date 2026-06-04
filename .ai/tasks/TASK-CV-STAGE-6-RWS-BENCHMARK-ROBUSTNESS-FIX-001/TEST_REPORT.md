# Raport z Testów — TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001

## 1. Testy Jednostkowe (Python)

### Focused Tests (Skoncentrowane testy benchmarku RWS)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv;."; python -m unittest app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark -v`
* **Wynik:**
```text
test_build_benchmark_summary_aggregates_extraction_failures (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_build_benchmark_summary_aggregates_extraction_failures) ... ok
test_build_benchmark_summary_handles_empty_runtimes (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_build_benchmark_summary_handles_empty_runtimes) ... ok
test_extract_card_on_synthetic_frame (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_extract_card_on_synthetic_frame) ... ok
test_run_rws_benchmark_with_invalid_args_exits (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_run_rws_benchmark_with_invalid_args_exits) ... ok
test_run_rws_benchmark_with_missing_references_exits (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_run_rws_benchmark_with_missing_references_exits) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.027s

OK
```

### Stage 6 Related Tests (Powiązane testy Stage 6)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv;."; python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture_expansion app_cv.tests.test_cv_detection_lab_stage6_real_camera_quality_gate app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark -v`
* **Wynik:**
```text
Ran 17 tests in 0.500s

OK
```

### Full Backend Suite (Pełna paczka testów backendowych)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv;."; python -m unittest discover -s app_cv/tests -v`
* **Wynik:**
```text
Ran 433 tests in 17.138s

OK
```

---

## 2. Kompilacja Kodu (py_compile)
* **Status:** `PASS`
* **Komenda uruchomienia:** `python -B -m py_compile tools/cv_detection_lab/stage6_rws_expansion_benchmark.py tools/cv_detection_lab/stage6_real_camera_quality_gate.py`

---

## 3. Walidacja Stylu (git diff --check)
* **Status:** `PASS`
* **Komenda uruchomienia:** `git diff --check`
