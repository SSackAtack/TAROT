# Raport z Testów — TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001

## 1. Testy Automatyczne (Python)

### Focused Tests (Skoncentrowane testy benchmarku RWS)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv;."; python -m unittest app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark -v`
* **Wynik:**
```text
test_extract_card_on_synthetic_frame (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_extract_card_on_synthetic_frame) ... ok
test_run_rws_benchmark_with_invalid_args_exits (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_run_rws_benchmark_with_invalid_args_exits) ... ok
test_run_rws_benchmark_with_missing_references_exits (app_cv.tests.test_cv_detection_lab_stage6_rws_expansion_benchmark.TestStage6RwsExpansionBenchmark.test_run_rws_benchmark_with_missing_references_exits) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.021s

OK
```

### Stage 6 Related Tests (Powiązane testy Stage 6)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv;."; python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture_expansion app_cv.tests.test_cv_detection_lab_stage6_real_camera_quality_gate -v`
* **Wynik:**
```text
test_expansion_preflight_blocks_ground_truth_identity_mismatch ... ok
test_expansion_preflight_blocks_incomplete_pack ... ok
test_expansion_preflight_blocks_missing_capture_file ... ok
test_expansion_preflight_passes_complete_eight_sample_pack ... ok
test_main_launcher_defaults_to_minimal_rws_expansion ... ok
test_minimal_rws_plan_has_eight_balanced_samples ... ok
test_shared_step_output_uses_expansion_total_instead_of_legacy_28 ... ok
test_benchmark_rate_handles_empty_and_nonempty_sets ... ok
test_clear_textured_crop_is_accepted ... ok
test_highlight_mask_matches_crop_shape ... ok
test_large_local_glare_requests_retry_or_manual_review ... ok
test_low_match_signal_escalates_clear_crop_to_manual_review ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.496s

OK
```

### Full Backend Suite (Pełna paczka testów backendowych)
* **Status:** `PASS`
* **Komenda uruchomienia:** `$env:PYTHONPATH="app_cv;."; python -m unittest discover -s app_cv/tests -v`
* **Wynik:** `Ran 431 tests in 21.530s - OK`

---

## 2. Testy Kompilacji (py_compile)
* **Status:** `PASS`
* **Komenda uruchomienia:** `python -B -m py_compile tools/cv_detection_lab/stage6_rws_expansion_benchmark.py tools/cv_detection_lab/stage6_real_camera_quality_gate.py`

---

## 3. Sprawdzenie Formatowania i Stylu (git diff --check)
* **Status:** `PASS`
* **Komenda uruchomienia:** `git diff --check`

---

## 4. Wykonanie i Dane Wyjściowe Benchmarku

### Komenda Uruchomienia Benchmarku
* `$env:PYTHONPATH="app_cv;."; python tools/cv_detection_lab/stage6_rws_expansion_benchmark.py`

### Ścieżka Wyjściowa Raportu
* `logs/offline_replay/stage6_rws_expansion_benchmark/`

### Podsumowanie Uruchomienia
* **sample_count:** 8
* **processed_count:** 8
* Wszystkie 8 próbek z fizycznej paczki `logs/live_fixtures/stage6_real_camera_fixture_expansion_rws_minimal` zostało pomyślnie przetworzonych.
