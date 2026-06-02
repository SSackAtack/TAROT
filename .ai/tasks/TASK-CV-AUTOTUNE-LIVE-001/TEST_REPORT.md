# TEST_REPORT: TASK-CV-AUTOTUNE-LIVE-001

## 2026-06-02 Codex

### Foundation baseline

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_auto_tuner app_cv.tests.test_snapshot_autotune app_cv.tests.test_runtime_config -v"
```

Wynik: PASS, 15 testów.

### Candidate vs accepted diagnostics

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_operator_explainability app_cv.tests.test_camera_controls_static -v"
```

Wynik: PASS, 9 testów.

### New autotuning foundation modules

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_operator_explainability app_cv.tests.test_camera_controls_static app_cv.tests.test_auto_tuner app_cv.tests.test_snapshot_autotune app_cv.tests.test_runtime_config app_cv.tests.test_autotune_scoring app_cv.tests.test_autotune_profiles app_cv.tests.test_autotune_session -v"
```

Wynik: PASS, 32 testy.

### Full branch verification

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Wynik: PASS, 243 testy.

```text
cmd.exe /c npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zgłosił istniejące ostrzeżenia o dużym chunku oraz nieskutecznym dynamicznym imporcie `textureCache.js`.

### Task 5 protocol RED

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_tuning_protocol -v"
```

Wynik: FAIL. Parser odrzucał `autotune_start`, `autotune_apply`, `autotune_save` i `autotune_cancel` jako unsupported message type.

### Task 5 protocol GREEN

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_tuning_protocol -v"
```

Wynik: PASS, 39 testów.

### Task 6 backend orchestration RED

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit -v"
```

Wynik: FAIL. Nowy test `test_main_handles_autotune_without_auto_apply` oczekiwał importów i obsługi komend autotuningu w `main.py`.

### Task 6 backend orchestration GREEN

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_tuning_protocol -v"
```

Wynik: PASS, 44 testy.

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m py_compile app_cv\main.py app_cv\tarotvision\autotune_session.py app_cv\tarotvision\autotune_profiles.py app_cv\tarotvision\autotune_scoring.py app_cv\tarotvision\tuning_protocol.py"
```

Wynik: PASS.
