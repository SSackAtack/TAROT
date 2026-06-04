# TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-EXPANSION-001

## Goal

Rozszerzyć real-camera fixture dla dalszej walidacji offline Stage 6 ORB
i quality gate, wykorzystując istniejące narzędzia operatorskie.

## Initial Status

```text
BLOCKED_BY_OPERATOR_CAPTURE
WAITING_FOR_NEW_REAL_CAMERA_CAPTURE
```

## Scope

- użyć istniejącego capture wizard, preflight i generatora manual review pack,
- dodać osobny minimalny wizard ekspansji RWS i osobny preflight paczki,
- ustawić główny launcher Stage 6 domyślnie na nową paczkę 8 próbek,
- zachować stary plan 28 próbek tylko jako jawną opcję `legacy`,
- zebrać nowe fizyczne sesje przez Michała/operatora,
- przygotować agregujący manifest i ręcznie potwierdzony ground truth,
- uruchomić preflight,
- wygenerować manual review pack,
- przekazać pack do zatwierdzenia przed jakimkolwiek nowym benchmarkiem.

## Target Capture Coverage

Minimalna paczka 8 zdjęć RWS na jasnej macie:

- 2 jasne karty bez celowego glare,
- 2 jasne karty z glare,
- 2 ciemne karty bez celowego glare,
- 2 ciemne karty z glare,
- po 4 upright i reversed,
- centrum, lewa i prawa strona maty.

## Out of Scope

- uruchamianie kolejnego benchmarku przed zatwierdzeniem review pack,
- deklarowanie postępu walidacji bez nowych fizycznych zdjęć,
- runtime integration,
- runtime thresholds,
- zmiany `app_cv/main.py`,
- zmiany `app_cv/tarotvision/*`,
- zmiany `app_ar/*`,
- zmiany WebSocket,
- zmiana planu lub kontraktu istniejącego 28-próbkowego fixture,
- uruchamianie starego planu bez jawnego wyboru operatora.

## Files Allowed to Change During Capture Phase

- lokalne ignorowane dane pod `logs/live_fixtures/`,
- lokalne ignorowane wyniki pod `logs/offline_replay/`,
- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-EXPANSION-001/*`,
- `.ai/TASKS_INDEX.md`,
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`.
- `tools/cv_detection_lab/stage6_real_camera_fixture_expansion_wizard.py`,
- `tools/cv_detection_lab/stage6_real_camera_capture_wizard.py`,
- `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture_expansion.py`,
- `stage6_capture_expansion_rws.bat`,
- `stage6_capture_wizard.bat`,
- `docs/operator/stage6_real_camera_fixture_capture.md`.

## Acceptance Criteria

- nowe fizyczne sesje zostały zebrane przez operatora,
- każda próbka ma ręcznie potwierdzony ground truth,
- preflight kończy się `PASS`,
- manual review pack został wygenerowany,
- nie uruchomiono benchmarku,
- task pozostaje zablokowany do zatwierdzenia manual review pack.

## Operator Procedure

Na izolowanej gałęzi Stage 6 uruchomić główny launcher:

```powershell
.\stage6_capture_wizard.bat
```

Domyślna opcja uruchamia paczkę RWS 8 próbek. Stary plan 28 próbek jest
dostępny tylko po jawnym wyborze `legacy`.

Na aktualnej maszynie dostępny jest też stabilny starter niezależny od gałęzi:

```powershell
E:\Antigravity\Projekty\START_TAROT_STAGE6_RWS_8_PROBEK.bat
```
