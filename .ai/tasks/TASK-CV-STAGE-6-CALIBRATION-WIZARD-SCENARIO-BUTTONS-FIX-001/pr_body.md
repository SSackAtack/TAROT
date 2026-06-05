# Pull Request — TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001

## Task ID
TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001

## Base Commit
4dd9ec2f85465cb33a9ec1d052be572e81177651

## Head Commit
1d51989e22dd0af6fc108d4b3a886a8ff7fb85ff

## Root Cause
W `app_ar/src/studio/studioConsole.js` stan `recommendation_ready` nie był uwzględniony w warunku `canStartScenario`, przez co przyciski wyboru kolejnych scenariuszy (PUSTA MATA, 1 KARTA, 3 KARTY) pozostawały zablokowane po udanej kalibracji pierwszego scenariusza (`empty`).

## Files Changed
- `app_ar/src/studio/studioConsole.js`
- `.ai/TASKS_INDEX.md`
- Utworzono katalog zadania `.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001/` z plikami `TASK.md`, `STATE.md`, `TEST_REPORT.md`, `CHANGELOG.md` oraz screenshotem `evidence_idle.png`.

## Tests Run
- Kompilacja frontendu: `npm --prefix app_ar run build` => PASS
- Weryfikacja manualna UI w przeglądarce: PASS (przyciski odblokowane w stanie gotowej rekomendacji i w stanie idle, kliknięcia prawidłowo wysyłają WebSocket `autotune_start`, Anuluj poprawnie resetuje system).

## Manual UI Smoke Result
Potwierdzona poprawna zmiana stanów przycisków w DOM (aktywne w `idle`/`recommendation_ready`, zablokowane w `collecting`).

## Physical Smoke
NOT_RUN

Awaiting ChatGPT Supervisor review.
