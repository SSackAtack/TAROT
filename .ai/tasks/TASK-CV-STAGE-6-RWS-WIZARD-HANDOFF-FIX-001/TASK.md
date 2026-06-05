# TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001 — Wizard RWS Handoff Fix

## Cel
Doprowadzić commit cc6d4df do stanu bezpiecznego do przejęcia po Codexie.

## Zakres
- Poprawienie `stage6_capture_wizard.bat` tak, aby tryby `rws`, `legacy` oraz domyślny interaktywny przechodziły przez check zajętości kamery (`CAMERA_OWNER_PID`), a tryby `plan` i `legacy-plan` go omijały.
- Usunięcie z `test_cv_detection_lab_stage6_real_camera_fixture_expansion.py` zależności od absolutnej ścieżki zewnętrznego startera `E:\Antigravity\Projekty\START_TAROT_STAGE6_RWS_8_PROBEK.bat`.
- Poprawienie opisu testów w `TEST_REPORT.md` poprzedniego zadania (usunięcie twierdzeń o realnym uruchomieniu).

## Poza zakresem (Out of Scope)
- Capture nowych próbek.
- Benchmark.
- Integracja runtime.
- Zmiana progów (thresholds).
- `app_cv/main.py`, `app_cv/tarotvision/*`, `app_ar/*`, WebSocket.

## Kryteria akceptacji
- Wszystkie testy jednostkowe przechodzą pomyślnie.
- Kompilacja python (`py_compile`) przechodzi bez błędów.
- Dokumentacja zadania jest kompletna.
