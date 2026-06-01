# TEST_REPORT: TASK-CV-SNAPSHOT-003

## 2026-06-01

### Pre-check

```text
python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_analyzes_warped_frame_when_table_is_calibrated -v
```

Wynik: oczekiwany FAIL przed implementacja. Analyzer dostawal surowy snapshot, nie klatke `warped`.

### Final verification

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_pipelines_contract -v"
```

Wynik: PASS, 4 testy.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m py_compile app_cv\tarotvision\pipelines\snapshot_first.py"
```

Wynik: PASS.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Wynik: PASS, 194 testy.

Uwaga srodowiskowa: uruchomienie bez eskalacji w sandboxie ladowalo niepelny modul `numpy`; powtorka poza sandboxem z tym samym `PYTHONPATH` przeszla poprawnie.
