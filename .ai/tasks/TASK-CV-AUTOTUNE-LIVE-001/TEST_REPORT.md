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

### Task 7 Studio Auto Tune panel RED

```text
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest app_cv.tests.test_camera_controls_static -v"
```

Wynik: FAIL. Nowy test `test_studio_autotune_panel_sends_operator_commands` oczekiwał panelu `studio-autotune-panel`, renderera statusu i komend `autotune_start/apply/cancel`.

### Task 7 Studio Auto Tune panel GREEN

```text
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest app_cv.tests.test_camera_controls_static -v"
```

Wynik: PASS, 5 testów.

```text
cmd /c "npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build"
```

Wynik: PASS. Vite zgłosił ostrzeżenia o dużym chunku oraz nieskutecznym dynamicznym imporcie `textureCache.js`.

### Task 8 profile save/apply RED

```text
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest app_cv.tests.test_profile_store app_cv.tests.test_main_static_audit -v"
```

Wynik: FAIL. Nowe testy oczekiwały `ProfileStore.save_autotune_recommendation()`, `load_parameters()` i użycia zapisu rekomendacji z metadanymi w `main.py`.

### Task 8 profile save/apply GREEN

```text
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest app_cv.tests.test_profile_store app_cv.tests.test_main_static_audit -v"
```

Wynik: PASS, 12 testów.

### Task 9 documentation/runbook

```text
Dokumentacja-only: README.md, .ai/TASKS_INDEX.md i notatki TASK-CV-AUTOTUNE-LIVE-001.
```

Wynik: PASS przez review diffu; brak zmian wykonywalnych.

### Task 10 automatic full verification

```text
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest discover -s app_cv\tests -v"
```

Wynik: PASS, 255 testów.

```text
cmd /c "npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build"
```

Wynik: PASS. Vite zgłosił ostrzeżenia o dużym chunku oraz nieskutecznym dynamicznym imporcie `textureCache.js`.

### Task 10 manual live smoke

Wynik: NOT RUN w tej sesji. Test wymaga fizycznej kamery i ręcznej obsługi Studio:

1. Uruchomić `start_tarotvision_studio.bat`.
2. Potwierdzić preview kamery i ArUco.
3. Uruchomić Auto Tune dla `empty`, `one_card`, `three_cards`.
4. Potwierdzić rekomendację, kliknąć `Apply`, zapisać profil i sprawdzić `logs/calibration_profiles/`.

### Post-Task 10 recognition diagnostics hook RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_main_static_audit -v
```

Wynik: FAIL. Nowe testy oczekiwały `recognize_crop_with_debug` w `SnapshotAnalyzer`, `autotune_sample_recorder` w `SnapshotFirstPipeline` oraz podłączenia `record_autotune_sample_from_snapshot` w `main.py`.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_card_recognition.RecognizeCardCropTest.test_debug_reports_top_match_ranking -v
```

Wynik: FAIL. `recognize_card_crop_with_debug()` zwracał `not_enough_crop_descriptors` zamiast rankingu top-matchy, bo debug nie korzystał ze wspólnej ścieżki detekcji cech.

### Post-Task 10 recognition diagnostics hook GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 23 testy.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_card_recognition.RecognizeCardCropTest.test_debug_reports_top_match_ranking -v
```

Wynik: PASS, 1 test.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_card_recognition app_cv.tests.test_recognition_debug app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_main_static_audit app_cv.tests.test_autotune_session app_cv.tests.test_autotune_scoring -v
```

Wynik: PASS, 46 testów.

### Post-Task 10 full automatic verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 261 testów.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zgłosił istniejące ostrzeżenia o dużym chunku oraz nieskutecznym dynamicznym imporcie `textureCache.js`.
