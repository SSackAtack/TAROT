# Test Report for TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SAMPLE-CAPTURE-001

## Automated Tests
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_tuning_protocol -v`
  - Wynik: **PASS**
  - Liczba testów: 41 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_autotune_lifecycle -v`
  - Wynik: **PASS**
  - Liczba testów: 7 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_autotune_pipeline_sample_capture -v`
  - Wynik: **PASS**
  - Liczba testów: 9 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest discover -s app_cv/tests -v`
  - Wynik: **PASS**
  - Liczba testów: 391 testów
- `python -m py_compile app_cv/main.py`
  - Wynik: **PASS**
- `python -m compileall app_cv/tarotvision`
  - Wynik: **PASS**
- `npm --prefix app_ar run build`
  - Wynik: **NOT_RUN** (brak zmian we frontendzie)
- GitHub Actions CI
  - Wynik: **PASS**

## Smoke Tests
- Uruchomienie backendu i weryfikacja za pomocą skryptu `smoke_test.py` (odczyt stanu, autotune_start, autotune_calibrate, autotune_cancel) -> **PASS**
- Manual camera smoke -> **NOT_RUN** (brak fizycznej kamery w środowisku testowym)
