# Test Report for TASK-CV-STAGE-6-RWS-AUTOTUNE-RUNTIME-COMMANDS-001

## Automated Tests
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_tuning_protocol -v`
  - Wynik: **PASS**
  - Liczba testów: 41 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_autotune_lifecycle -v`
  - Wynik: **PASS**
  - Liczba testów: 7 testów
- `$env:PYTHONPATH="app_cv"; python -m unittest discover -s app_cv/tests -v`
  - Wynik: **PASS**
  - Liczba testów: 382 testy
- `python -m py_compile app_cv/main.py`
  - Wynik: **PASS**
- `python -m compileall app_cv/tarotvision`
  - Wynik: **PASS**
- `npm --prefix app_ar run build`
  - Wynik: **NOT_RUN** (brak zmian we frontendzie)

## Smoke Tests
- Uruchomienie backendu i weryfikacja za pomocą skryptu `smoke_test.py`:
  - Połączenie do `ws://localhost:8765` -> **PASS**
  - Odczyt stanu początkowego (Autotune: `idle`) -> **PASS**
  - Wysłanie `autotune_start` (Zmiana stanu na `collecting`) -> **PASS**
  - Wysłanie `autotune_calibrate` (Brak crasha, bezpieczne ostrzeżenie) -> **PASS**
  - Wysłanie `autotune_cancel` (Powrót do stanu `idle`) -> **PASS**
  - Zatrzymanie backendu bez błędów -> **PASS**
