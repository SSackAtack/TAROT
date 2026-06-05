# TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001

## Goal
Naprawić błąd w Studio UI, przez który po zakończeniu kalibracji scenariusza empty i przejściu do stanu recommendation_ready przyciski wyboru kolejnych scenariuszy (PUSTA MATA, 1 KARTA, 3 KARTY) pozostają zablokowane.

Błąd został wykryty w:
TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001

Problem:
1. Operator uruchamia scenariusz empty.
2. System zbiera 3/3 próbek.
3. Przycisk „Skalibruj” poprawnie się odblokowuje.
4. Kliknięcie „Skalibruj” wysyła autotune_calibrate.
5. Backend/UI przechodzi do stanu recommendation_ready.
6. UI pokazuje „REKOMENDACJA GOTOWA” i sugeruje kolejny krok.
7. Przyciski PUSTA MATA, 1 KARTA, 3 KARTY są nadal disabled = true.
8. Operator nie może przejść do kolejnego scenariusza bez kliknięcia „Anuluj”.
9. Kliknięcie „Anuluj” resetuje postęp, więc workflow kalibracji jest zablokowany.

## Scope
Napraw wyłącznie logikę enable/disable przycisków startu scenariuszy w Studio UI.
Podejrzany plik:
- `app_ar/src/studio/studioConsole.js`

Nie zmieniaj backendu.

## Expected Logic
Przyciski startu scenariuszy powinny być aktywne, gdy wizard nie jest w trakcie zbierania próbek i nie czeka na scoring aktualnego scenariusza.
Bezpieczna minimalna logika:
```javascript
const canStartScenario =
    state === 'idle' ||
    state === 'cancelled' ||
    state === 'recommendation_ready'

if (btnStartEmpty) btnStartEmpty.disabled = !canStartScenario
if (btnStartOne) btnStartOne.disabled = !canStartScenario
if (btnStartThree) btnStartThree.disabled = !canStartScenario
```

## Out of Scope
Nie wolno w tym tasku:
* zmieniać backendu,
* zmieniać payloadu WebSocket,
* zmieniać scoringu,
* zmieniać sample capture,
* zmieniać algorytmów CV,
* zmieniać calibration_wizard_status.py,
* robić redesignu panelu,
* dodawać nowych funkcji,
* ruszać katalogu Komercja/,
* oznaczać taska jako APPROVED BY CHATGPT SUPERVISOR przed review.

## Files Allowed to Change
* `app_ar/src/studio/studioConsole.js`
* `.ai/TASKS_INDEX.md`
* `.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001/*`

## Acceptance Criteria
1. W stanie idle przyciski PUSTA MATA, 1 KARTA, 3 KARTY są aktywne.
2. W stanie collecting przyciski startu scenariuszy są zablokowane.
3. W stanie ready_to_score przyciski startu scenariuszy są zablokowane, a „Skalibruj” jest aktywny.
4. W stanie recommendation_ready przyciski PUSTA MATA, 1 KARTA, 3 KARTY są aktywne.
5. Kliknięcie 1 KARTA w stanie recommendation_ready wysyła poprawną komendę WebSocket startu scenariusza.
6. Kliknięcie 3 KARTY w stanie recommendation_ready wysyła poprawną komendę WebSocket startu scenariusza.
7. Przycisk „Anuluj” nadal działa i resetuje stan.
8. `npm --prefix app_ar run build` przechodzi na PASS.
9. Manual UI smoke potwierdza naprawę Blocker 2.
