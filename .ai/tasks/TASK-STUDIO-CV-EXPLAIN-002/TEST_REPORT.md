# TEST_REPORT: TASK-STUDIO-CV-EXPLAIN-002

## 2026-06-02

Nie uruchamiano testów. Zadanie jest w statusie `TODO`; w tej sesji zapisano tylko zakres follow-up.

## 2026-06-02 Implementation

### RED

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_operator_explainability -v"
```

Wynik: FAIL. Nowy test `test_candidate_gap_explains_rejected_cards` oczekiwał `warn`, a aktualny kod zwracał `ok`.

### GREEN

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_operator_explainability app_cv.tests.test_camera_controls_static -v"
```

Wynik: PASS, 9 testów.

## 2026-06-02 ArUco Consistency Fix

### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability -v
```

Wynik: FAIL. Nowe testy wykazały, że `runtime.table.marker_ids=[10,11,12,13]` nadal dawało wartość `0/4`, a `runtime.table.calibrated=True` z pustą listą markerów dawało zielony stan `ok`.

### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability -v
```

Wynik: PASS, 7 testów.

### Verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability app_cv.tests.test_camera_controls_static -v
```

Wynik: PASS, 13 testów.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 263 testy.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zgłosił istniejące ostrzeżenia o dużym chunku oraz nieskutecznym dynamicznym imporcie `textureCache.js`.
