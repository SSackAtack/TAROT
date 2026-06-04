# CHANGELOG

## Modyfikowane pliki

- `stage6_capture_wizard.bat`:
  - Przeniesiono warunki `rws` i `legacy` pod sprawdzanie zajętości kamery (`CAMERA_OWNER_PID`), co wymusza przejście przez check.
- `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture_expansion.py`:
  - Usunięto test `test_branch_independent_starter_blocks_when_backend_main_owns_camera` odwołujący się do zewnętrznego pliku dewelopera Michała.
  - Zaktualizowano `test_main_launcher_defaults_to_minimal_rws_expansion`, aby weryfikował obecność komunikatów blokady i kodu wyjścia `2` bezpośrednio na pliku z repozytorium.
- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-EXPANSION-001/TEST_REPORT.md`:
  - Zmieniono „Occupied-camera starter smoke” na „Occupied-camera starter static check”.
- `.ai/TASKS_INDEX.md`:
  - Zarejestrowano nowe zadanie `TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001`.
