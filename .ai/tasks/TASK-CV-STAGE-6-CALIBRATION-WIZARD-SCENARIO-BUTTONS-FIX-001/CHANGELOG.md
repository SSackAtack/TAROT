# Changelog dla TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001

## [1.0.0] - 2026-06-05

### Poprawiono
- Logikę aktywacji przycisków startu scenariuszy w `app_ar/src/studio/studioConsole.js`. Odblokowano przyciski PUSTA MATA, 1 KARTA, 3 KARTY w stanie `recommendation_ready`.
- Zapewniono pełną zgodność stanu przycisków we wszystkich 4 stanach Asystenta Kalibracji (`idle`, `collecting`, `ready_to_score`, `recommendation_ready`).
