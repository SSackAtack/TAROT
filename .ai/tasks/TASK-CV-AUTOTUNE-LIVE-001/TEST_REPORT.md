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
