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

### Glare false-positive candidate validation RED

```text
python -m unittest tests.test_card_candidate_validation tests.test_snapshot_analyzer tests.test_operator_explainability
```

Wynik: FAIL. Brakowalo modulu `tarotvision.card_candidate_validation`; `SnapshotAnalyzer` przekazywal gladki crop do rozpoznawania i przyjmowal wymuszony false match; `CV Explain` nie rozroznial odrzucenia cropa bez cech karty.

### Glare false-positive candidate validation GREEN

```text
python -m unittest tests.test_card_candidate_validation tests.test_snapshot_analyzer tests.test_operator_explainability tests.test_pipelines_contract tests.test_autotune_scoring tests.test_autotune_session
```

Wynik: PASS, 33 testy.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 267 testow.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil istniejace ostrzezenia o duzym chunku oraz nieskutecznym dynamicznym imporcie `textureCache.js`.

### Continuation verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 267 testow.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil te same istniejace ostrzezenia: duzy chunk po minifikacji oraz nieskuteczny dynamiczny import `src/renderer/textureCache.js`.

### Event-first Task 6 CV Explain and Diagnostics

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability -v
```

Wynik: FAIL oczekiwany. Brakowalo krokow `change_detection` i `empty_reference` w payloadzie CV Explain.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability -v
```

Wynik: PASS, 11 testow.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability -v
```

Wynik: PASS, 47 testow.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\operator_explainability.py app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 300 testow.

### Event-first Task 5 Autotune Creates Session Reference

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Wynik: FAIL oczekiwany, 3 porazki:
- brak `message.scenario == "empty"` / `background_model.clear()` / sygnalow bootstrapu w `main.py`,
- brak `BackgroundModel.capture_many()` po trzeciej pustej probce,
- brak walidacji `BackgroundModel.changed_ratio()`.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Wynik: PASS, 25 testow.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 297 testow.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 296 testow.

### Event-first Task 5 Supervisor fix

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_empty_reference_capture_records_frames_when_change_detector_reports_no_change -v
```

Wynik: FAIL oczekiwany. Przy aktywnym `change_detector`, istniejącym `previous_stable_snapshot` i `no_change_hold_previous` recorder nie był wywoływany (`0 != 3`), więc `capture_many()` nie mógł powstać.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_empty_reference_capture_records_frames_when_change_detector_reports_no_change -v
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Wynik: PASS, 26 testow.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

### Event-first background diff plan

Wynik: PLAN ONLY. Nie uruchamiano testow, poniewaz w tej sesji zapisano dokument planistyczny bez zmian produkcyjnych.

Plik planu:

```text
docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md
```

### Event-first plan clarification

PLAN ONLY. Nie uruchamiano testów kodu, ponieważ zmieniono wyłącznie dokumentację planistyczną. Zweryfikowano ręcznie diff dokumentacji.

Zweryfikowany zakres:

```text
docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md
.ai/TASKS_INDEX.md
```

### Continuation manual live smoke

Wynik: NOT RUN w tej sesji. Nadal wymagany jest test z fizyczna kamera i stolem: `empty`, `one_card`, `three_cards`, rekomendacja, `Apply`, zapis profilu w `logs/calibration_profiles/` oraz kontrola `CV Explain` przy realnym odblasku.

### Studio sidebar accordion

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_camera_controls_static -v
```

Wynik: PASS, 7 testow.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil te same istniejace ostrzezenia: duzy chunk po minifikacji oraz nieskuteczny dynamiczny import `src/renderer/textureCache.js`.

```text
Browser QA: http://127.0.0.1:5174/?studio=1
```

Wynik: PASS. Studio renderuje osobne sekcje akordeonu, `Aktywne Talie` rozwija sie po kliknieciu, `Auto Tune` pozostaje osobna sekcja i konsola przegladarki nie zglosila bledow.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 268 testow.

### Auto Tune wizard MVP RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_autotune_session app_cv.tests.test_autotune_session_log app_cv.tests.test_tuning_protocol app_cv.tests.test_camera_controls_static -v
```

Wynik: FAIL. Brakowalo `stage_result` i `next_action` w `AutotuneSession`, modulu `tarotvision.autotune_session_log`, parsera `autotune_calibrate` oraz przyciskow `Skalibruj`/`Save Profile` w Studio.

### Auto Tune wizard MVP GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_autotune_session app_cv.tests.test_autotune_session_log app_cv.tests.test_tuning_protocol app_cv.tests.test_camera_controls_static -v
```

Wynik: PASS, 55 testow.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\autotune_session.py app_cv\tarotvision\autotune_session_log.py app_cv\tarotvision\tuning_protocol.py app_cv\main.py
```

Wynik: PASS. Poprzednia proba bez `-B` zakonczyla sie bledem Windows `WinError 5` na zablokowanym pliku `__pycache__`.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil te same istniejace ostrzezenia: duzy chunk po minifikacji oraz nieskuteczny dynamiczny import `src/renderer/textureCache.js`.

### Event-first amendment merge

PLAN ONLY. Nie uruchamiano testów kodu, ponieważ zmieniono wyłącznie dokumentację planistyczną.

Zweryfikowano ręcznie, że `docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md` zawiera teraz:

- sekcję `ROI Semantics` rozróżniającą `roi_hints is None`, `roi_hints == []` i `roi_hints == [...]`;
- wymagany test `test_analyze_with_empty_roi_hints_does_not_fallback_to_global_detection`;
- ostrzeżenie przed `roi_hints or None` w integracji runtime;
- walidację `empty_reference` przez `BackgroundModel.changed_ratio(analysis_frame, threshold=20)`, nie przez `analysis_frame` porównany z samym sobą;
- dodatkowe kryteria akceptacji dla `roi_hints=[]` i reference-vs-current validation.

Usunięto osobne pliki erraty:

```text
docs/superpowers/plans/2026-06-02-event-first-background-diff-plan-amendment-001.md
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT_EVENT_FIRST_AMENDMENT_001.md
```

### Event-first Task 1 Stable Empty Reference

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model -v
```

Wynik: FAIL zgodnie z oczekiwaniem. Brakowało metod `BackgroundModel.capture_many()` i `BackgroundModel.changed_ratio()`.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model -v
```

Wynik: PASS, 5 testów.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\background_model.py
```

Wynik: PASS.

#### Full backend verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 282 testy.

### Event-first Task 2 ChangeDetector

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_change_detection -v
```

Wynik: FAIL zgodnie z oczekiwaniem. Brakowało modułu `tarotvision.change_detection`.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_change_detection -v
```

Wynik: PASS, 4 testy.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\change_detection.py
```

Wynik: PASS.

#### Full backend verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 286 testów.

### Event-first Task 3 SnapshotAnalyzer ROI Hints

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Wynik: FAIL zgodnie z oczekiwaniem. `SnapshotAnalyzer.analyze()` nie przyjmował argumentu `roi_hints`.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Wynik: PASS, 13 testów.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\snapshot_analyzer.py
```

Wynik: PASS.

#### Full backend verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 288 testów.

### Event-first Task 4 Runtime Pipeline Integration

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_passes_change_rois_to_analyzer -v
```

Wynik: FAIL zgodnie z oczekiwaniem. `SnapshotFirstPipeline.__init__()` nie przyjmował `change_detector`.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit.TestMainStaticAudit.test_main_wires_change_detector_into_snapshot_pipeline -v
```

Wynik: FAIL zgodnie z oczekiwaniem. `main.py` nie importował ani nie przekazywał `ChangeDetector`.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_passes_change_rois_to_analyzer -v
```

Wynik: PASS, 1 test.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit.TestMainStaticAudit.test_main_wires_change_detector_into_snapshot_pipeline -v
```

Wynik: PASS, 1 test.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_passes_empty_roi_list_without_global_fallback -v
```

Wynik: PASS, 1 test.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 20 testów.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

#### Full backend verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 291 testów.

### Event-first Task 4 Supervisor fix

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_holds_previous_state_on_global_shift -v
```

Wynik: FAIL przed poprawką. `global_shift=True` nie był obsłużony jako hold-state.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_preserves_cards_when_no_added_or_removed_regions -v
```

Wynik: FAIL przed poprawką. Brak regionów zmian przy istniejących kartach uruchamiał analizę i mógł prowadzić do czyszczenia layoutu.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_holds_previous_state_on_global_shift app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_preserves_cards_when_no_added_or_removed_regions -v
```

Wynik: PASS, 2 testy.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 22 testy.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

#### Full backend verification

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 293 testy.

```text
Browser QA: http://127.0.0.1:5174/?studio=1
```

Wynik: PASS. Panel Auto Tune renderuje przyciski `Pusta mata`, `1 karta`, `3 karty`, `Skalibruj`, `Apply`, `Save Profile`, `Cancel`; konsola przegladarki nie zglosila bledow. Nie klikano akcji live, aby nie mieszac w aktywnej sesji operatora.

### Preview controls visibility

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_camera_controls_static -v
```

Wynik: PASS, 7 testow.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil te same istniejace ostrzezenia: duzy chunk po minifikacji oraz nieskuteczny dynamiczny import `src/renderer/textureCache.js`.

```text
Browser QA: http://127.0.0.1:5174/?studio=1
```

Wynik: PASS. Sekcja `Widok podgladu` jest rozwinieta, przyciski `Wirtualny stol`, `Kamera`, `PiP` oraz suwak rozmiaru PiP sa widoczne; konsola przegladarki bez bledow.

### PiP slider cap fix

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_camera_controls_static -v
```

Wynik: PASS, 8 testow.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil te same istniejace ostrzezenia: duzy chunk po minifikacji oraz nieskuteczny dynamiczny import `src/renderer/textureCache.js`.

```text
Browser QA: http://127.0.0.1:5174/?studio=1
```

Wynik: PASS. Programowy pomiar PiP w trybie Studio: 38% = okolo 493.74px, 45% = okolo 584.70px, roznica = okolo 90.96px. Suwak nie ma juz martwej strefy w zakresie 38-45%.

### Auto Tune forced sampling fix

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_gate app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract app_cv.tests.test_autotune_session app_cv.tests.test_autotune_session_log -v
```

Wynik: PASS, 31 testow.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\snapshot_gate.py app_cv\tarotvision\pipelines\snapshot_first.py app_cv\main.py
```

Wynik: PASS.

```text
Live Browser QA: http://127.0.0.1:5174/?studio=1
```

Wynik: PASS techniczny. Po kliknieciu `Pusta mata` logi utworzyly `stage_started`, trzy `sample_collected` i `stage_completed` w katalogu `logs/autotune_sessions/`. Najnowszy wynik live: `empty` zakonczyl sie `FAIL`, bo system wykryl false positives na pustej macie (`candidate_count` 1-2, `accepted_count` 1). UI pokazal `READY_TO_SCORE` oraz `FAIL: Pusta mata FAIL: wykryto false positive na macie`.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 280 testow.

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zglosil te same istniejace ostrzezenia: duzy chunk po minifikacji oraz nieskuteczny dynamiczny import `src/renderer/textureCache.js`.

### Event-first Task 7 Live Smoke

#### Targeted event-first suite

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability -v
```

Wynik: PASS, 47 testów.

#### Full backend suite

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 300 testów.

#### Frontend build

```text
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Wynik: PASS. Vite zgłosił istniejące ostrzeżenia: nieskuteczny dynamiczny import `src/renderer/textureCache.js` oraz chunk większy niż 500 kB.

#### Current backend payload check

Wynik: PASS diagnostyczny. Stary proces backendu CV na portach `8765/8766` nie publikował pól Task 6, więc został zatrzymany. Po uruchomieniu backendu z bieżącego branchu payload WebSocket zawierał:

```text
background_reference_active=false
empty_reference_capture_active=false
empty_reference_frame_count=0
operator_explainability_steps=decks, aruco, snapshot, empty_reference, change_detection, candidates, recognition
```

#### Live smoke: Pusta mata

```text
WebSocket command: {"type":"autotune_start","scenario":"empty"}
```

Wynik: RED. Po starcie `empty_reference_capture_active=true`, ale etap pozostał na `empty 0/3`; `empty_reference_frame_count=0`, `background_reference_active=false`, `background_reference_validation_ratio=null`.

Najnowszy log sesji autotuningu:

```text
logs/autotune_sessions/autotune_20260603_000944_1780438184277849800_empty_stage_started.json
```

Nie powstały pliki `sample_collected` ani `stage_completed` dla tej próby.

Metryki `logs/cv_metrics.jsonl` po starcie pokazują:

```text
empty_reference_capture_active=true
empty_reference_frame_count=0
snapshot_samples_taken=1.0
snapshot_rejected_count=1.0
stable_for_ms=0.0
table.marker_ids=[]
```

Wniosek: Task 7 nie spełnia kryterium akceptacji "`Pusta mata` nie wisi na `0/3`". Scenariusze jedna karta, trzy karty, no-change, removal i global shift nie zostały uruchomione, bo pustej referencji nie udało się zbudować.

### Event-first Task 7 Snapshot Quality Diagnostics

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_reports_quality_reason_when_all_samples_rejected -v
```

Wynik: FAIL oczekiwany. Pipeline ustawiał `snapshot_reject_reason=all_samples_rejected`, ale layout nie zawierał `snapshot_quality_reject_reason`, więc operator i logi nie wyjaśniały, czy problemem jest ciemność, kontrast, ostrość czy prześwietlenie.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability app_cv.tests.test_pipelines_contract -v
```

Wynik: PASS, 27 testów.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\operator_explainability.py app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability -v
```

Wynik: PASS, 49 testów.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 302 testy.

#### Live diagnostic retry

```text
WebSocket command: {"type":"autotune_start","scenario":"empty"}
```

Wynik: PARTIAL PASS / NOT FINAL TASK 7. Backend z bieżącą diagnostyką zebrał `empty 3/3`, utworzył `background_reference_active=true`, zapisał `sample_collected` i `stage_completed`, a `stage_result` był `PASS`.

Ograniczenie: ta powtórka działała przy `table.calibrated=false`, `marker_ids=[]`, `snapshot_analysis_warped=0.0`, więc nie weryfikuje docelowego smoke z aktywną kalibracją ArUco.

### Event-first Task 7 Empty Layout Hold Fix

#### Regression

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_empty_reference_capture_records_false_positive_without_publishing_layout app_cv.tests.test_main_static_audit.TestMainStaticAudit.test_autotune_empty_stage_bootstraps_reference_before_validation -v
```

Wynik: PASS, 2 testy.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 62 testy.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 303 testy.

#### Live retest after fix

Warunek wejściowy:

```text
table.calibrated=true
marker_ids=[10, 11, 12, 13]
cards=[]
```

Komenda:

```text
WebSocket command: {"type":"autotune_start","scenario":"empty"}
```

Wynik: PARTIAL PASS / nadal RED dla pełnego Task 7.

Po poprawce runtime nie publikuje fałszywych kart podczas `Pusta mata`:

```text
detected=false
cards_len=0
empty_reference_false_positive_hold=1.0
background_reference_active=true
background_reference_validation_ratio=0.01
background_reference_validation_warning=0.0
snapshot_analysis_warped=1.0
```

Log sesji nadal poprawnie klasyfikuje etap `empty` jako FAIL, bo false positives występują w próbkach:

```text
stage_result=FAIL
sample 1: candidate_count=3, accepted_count=2
sample 2: candidate_count=2, accepted_count=1
sample 3: candidate_count=2, accepted_count=1
```

Wniosek: naprawiono zanieczyszczanie layoutu fałszywymi kartami podczas kalibracji pustej maty. Pełny smoke nadal nie jest green, bo trzeba zmniejszyć false positives detektora na pustej macie po warpie ArUco.

### Event-first Empty Reference Status Fix

#### Regression

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_autotune_session app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 19 testów.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\autotune_session.py app_cv\main.py
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability app_cv.tests.test_autotune_session app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 69 testów.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 303 testy.

#### Live retest after status fix

Warunek wejściowy:

```text
table.calibrated=true
marker_ids=[10, 11, 12, 13]
```

Komenda:

```text
WebSocket command: {"type":"autotune_start","scenario":"empty"}
```

Wynik: PASS dla nowego kontraktu pustej referencji:

```text
stage_result=PASS
empty_reference_status=PASS
background_reference_active=true
background_reference_validation_ratio=0.0
background_reference_validation_warning=0.0
detected=false
cards_len=0
empty_reference_false_positive_hold=1.0
diagnostics.false_positive_count=7
diagnostics.legacy_detector_false_positive=true
```

Wniosek: `Pusta mata` tworzy referencję i nie publikuje false positives do layoutu. False positives starego detektora są zachowane jako warning/diagnostyka do osobnego taska, a nie jako bloker referencji tła.

### Event-first Previous Stable Seed Fix

#### RED

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_empty_reference_finalization_seeds_previous_stable_snapshot -v
```

Wynik: FAIL oczekiwany. Po finalizacji `empty_reference` `pipeline.previous_stable_snapshot` pozostawał `None`, więc następny stabilny snapshot mógł użyć `roi_hints=None` i wrócić do globalnej detekcji.

#### GREEN

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_empty_reference_finalization_seeds_previous_stable_snapshot -v
```

Wynik: PASS.

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m py_compile app_cv\tarotvision\pipelines\snapshot_first.py
```

Wynik: PASS.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability app_cv.tests.test_autotune_session app_cv.tests.test_main_static_audit -v
```

Wynik: PASS, 70 testów.

```text
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Wynik: PASS, 304 testy.

#### Live retest after seed fix

Warunek wejściowy:

```text
table.calibrated=true
marker_ids=[10, 11, 12, 13]
```

Komenda:

```text
WebSocket command: {"type":"autotune_start","scenario":"empty"}
```

Wynik: PASS dla pustej referencji i stabilnej pustej maty po finalizacji:

```text
empty_reference_status=PASS
background_reference_active=true
background_reference_validation_warning=0.0
completed_detected=false
completed_cards_len=0
post_observation_count=53
post_max_cards_len=0
post_any_detected=false
diagnostics.false_positive_count=4
diagnostics.legacy_detector_false_positive=true
```

Wniosek: po finalizacji pustej referencji pipeline nie publikuje już później false positives na stabilnej pustej macie. False positives starego detektora pozostają tylko diagnostyką etapu `empty`.

### Event-first Task 7 One Card Smoke

Warunek wejściowy:

```text
background_reference_active=true
table.calibrated=true
marker_ids=[10, 11, 12, 13]
jedna karta fizycznie położona na macie
```

Wynik payloadu live:

```text
detected=true
cards_len=1
card.name=Gilded_03
card.confidence=0.4
card.orientation=reversed
background_reference_active=true
snapshot_analysis_warped=1.0
```

Metryki rolling z `logs/cv_metrics.jsonl`:

```text
change_added_count=0.333
change_region_count=0.333
change_removed_count=0.0
change_global_shift=0.667
change_mask_ratio=0.467
snapshot_quads_found=2.0
snapshot_recognition_attempts=2.0
snapshot_recognition_rejections=0.75
layout_publish_count=1.0
layout_changed=1.0
```

Wniosek: scenariusz jednej karty przeszedł funkcjonalnie (`cards_len=1`, brak dodatkowych kart), ale diagnostyka change detection nie jest jeszcze idealnie czysta, bo rolling metrics pokazują część próbek jako `global_shift`. Obserwować to przy trzech kartach, no-change i removal.
