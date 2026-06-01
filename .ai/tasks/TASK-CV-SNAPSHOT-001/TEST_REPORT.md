# TEST_REPORT: TASK-CV-SNAPSHOT-001

## 2026-06-01

### Pre-check

```text
python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Wynik: oczekiwany FAIL przed implementacja. Guard wykryl `StateFirstLegacyPipeline`, `legacy_pipeline`, `USE_SNAPSHOT_FIRST_CV`, `USE_TABLE_CARD_DETECTION` i `STATE-FIRST OPTIMIZATION` w `main.py`.

### Final verification

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v"
```

Wynik: PASS, 5 testow.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\__init__.py app_cv\tarotvision\pipelines\snapshot_first.py"
```

Wynik: PASS.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Wynik: PASS, 188 testow.

Uwaga srodowiskowa: pierwsze uruchomienie unittest bez eskalacji zaladowalo niepelny modul `numpy` bez `zeros`; powtorka poza sandboxem z tym samym `PYTHONPATH` przeszla poprawnie.
