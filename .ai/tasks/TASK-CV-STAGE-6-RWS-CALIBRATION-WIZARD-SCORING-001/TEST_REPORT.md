# Test Report for TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SCORING-001

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
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_calibration_wizard_scoring -v`
  - Wynik: **PASS**
  - Liczba testów: 9 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_calibration_wizard_scoring_integration -v`
  - Wynik: **PASS**
  - Liczba testów: 5 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest discover -s app_cv/tests -v`
  - Wynik: **PASS**
  - Liczba testów: 405 testów
- `python -m py_compile app_cv/main.py`
  - Wynik: **PASS**
- `python -m compileall app_cv/tarotvision`
  - Wynik: **PASS**
- Frontend build (`npm --prefix app_ar run build`)
  - Wynik: **NOT_RUN** (brak zmian we frontendzie)
- GitHub Actions CI
  - Wynik: **PENDING** (będzie uruchomiony po pushu brancha)

## Smoke Tests

- Uruchomienie backendu i weryfikacja za pomocą zaktualizowanego skryptu `smoke_test.py` (połączenie WebSocket, start sesji wizardu, wysłanie calibrate bez próbek, anulowanie sesji, brak crasha serwera i weryfikacja typów danych) -> **PASS** (wykonany pomyślnie)
- Manual camera smoke
  - Wynik: **NOT_RUN** (brak fizycznej kamery w środowisku testowym)
