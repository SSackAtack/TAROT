# TEST_REPORT: TASK-CV-SNAPSHOT-006

## 2026-06-01

### Final verification

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_background_model app_cv.tests.test_tuning_protocol app_cv.tests.test_card_detection_profiles -v"
```

Wynik: PASS, 41 testów.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m py_compile app_cv\main.py app_cv\tarotvision\background_model.py app_cv\tarotvision\card_detection_profiles.py app_cv\tarotvision\tuning_protocol.py app_cv\tarotvision\snapshot_analyzer.py"
```

Wynik: PASS.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Wynik: PASS, 207 testów.

Uwaga środowiskowa: uruchomienie bez eskalacji w sandboxie ładowało niepełny moduł `numpy`; powtórka poza sandboxem z tym samym `PYTHONPATH` przeszła poprawnie.
