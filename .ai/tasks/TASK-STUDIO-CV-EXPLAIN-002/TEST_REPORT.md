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
