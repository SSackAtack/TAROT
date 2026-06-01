# TEST_REPORT: TASK-STUDIO-CV-EXPLAIN-001

## 2026-06-01

### RED

```text
cmd /c "set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_operator_explainability -v"
```

Wynik: FAIL, brak `tarotvision.operator_explainability`.

```text
cmd /c "set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_status_store app_cv.tests.test_operator_explainability app_cv.tests.test_main_static_audit -v"
```

Wynik: FAIL, `main.py` nie publikował jeszcze `operator.explainability`.

```text
cmd /c "set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_camera_controls_static -v"
```

Wynik: FAIL, `studioConsole.js` nie zawierał jeszcze panelu `CV Explain`.

### GREEN

```text
cmd /c "set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_operator_explainability -v"
```

Wynik: PASS, 4 testy.

### Full verification

```text
cmd /c "set PYTHONPATH=E:\Antigravity\Projekty\TAROT\.tmp_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Wynik: PASS, 234 testy.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zgłosił istniejące ostrzeżenia o dużym chunku i nieskutecznym dynamicznym imporcie `textureCache.js`.

```text
Browser smoke: http://127.0.0.1:5173/?studio=1
```

Wynik: PASS dla startu Studio bez błędu JavaScript panelu. Konsola zgłosiła oczekiwane w tym trybie błędy `ERR_CONNECTION_REFUSED` dla backendu CV (`ws://localhost:8765/`, `http://localhost:8766/video_feed.mjpg`) oraz standardowy warning Web Audio przed gestem użytkownika.

```text
cmd /c "set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_status_store app_cv.tests.test_operator_explainability app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v"
```

Wynik: PASS, 27 testów.

```text
cmd /c "set PYTHONPATH=app_cv && python -m unittest app_cv.tests.test_camera_controls_static -v"
```

Wynik: PASS, 4 testy.
