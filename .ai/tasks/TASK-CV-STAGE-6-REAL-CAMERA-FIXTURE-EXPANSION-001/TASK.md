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
- zebrać nowe fizyczne sesje przez Michała/operatora,
- przygotować agregujący manifest i ręcznie potwierdzony ground truth,
- uruchomić preflight,
- wygenerować manual review pack,
- przekazać pack do zatwierdzenia przed jakimkolwiek nowym benchmarkiem.

## Target Capture Coverage

- więcej przypadków `YELLOW` i glare,
- różne kąty światła,
- różne pozycje kart na stole,
- reversed,
- wrong-deck,
- visually similar,
- jasne grafiki do kontroli false positive quality gate,
- ciemne grafiki do kontroli `usable_detail_ratio`.

## Out of Scope

- uruchamianie kolejnego benchmarku przed zatwierdzeniem review pack,
- deklarowanie postępu walidacji bez nowych fizycznych zdjęć,
- runtime integration,
- runtime thresholds,
- zmiany `app_cv/main.py`,
- zmiany `app_cv/tarotvision/*`,
- zmiany `app_ar/*`,
- zmiany WebSocket,
- modyfikowanie istniejącego capture wizard, preflight lub review pack tooling.

## Files Allowed to Change During Capture Phase

- lokalne ignorowane dane pod `logs/live_fixtures/`,
- lokalne ignorowane wyniki pod `logs/offline_replay/`,
- `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-EXPANSION-001/*`,
- `.ai/TASKS_INDEX.md`,
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`.

## Acceptance Criteria

- nowe fizyczne sesje zostały zebrane przez operatora,
- każda próbka ma ręcznie potwierdzony ground truth,
- preflight kończy się `PASS`,
- manual review pack został wygenerowany,
- nie uruchomiono benchmarku,
- task pozostaje zablokowany do zatwierdzenia manual review pack.

## Operator Procedure

Użyć istniejącej instrukcji:

```text
docs/operator/stage6_real_camera_fixture_capture.md
```

oraz istniejącego launchera:

```powershell
.\stage6_capture_wizard.bat
```
