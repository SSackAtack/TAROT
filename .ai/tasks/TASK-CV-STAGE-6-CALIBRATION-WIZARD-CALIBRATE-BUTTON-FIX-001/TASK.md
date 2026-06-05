# TASK-CV-STAGE-6-CALIBRATION-WIZARD-CALIBRATE-BUTTON-FIX-001

## Goal
Naprawić błąd w Studio UI, przez który przycisk „Skalibruj” pozostaje zablokowany po zebraniu wymaganych próbek w Asystencie Kalibracji Stanowiska.

Błąd został wykryty w:
TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001

Objaw:
- scenariusz `empty` zebrał 3/3 próbek,
- backend / status przeszedł do stanu `ready_to_score`,
- UI poprawnie pokazało zakończenie zbierania,
- przycisk „Skalibruj” nadal miał `disabled = true`,
- operator nie mógł uruchomić scoringu.

## Scope
Napraw wyłącznie logikę frontendową w Studio UI odpowiedzialną za enable/disable przycisku „Skalibruj”.
Podejrzany plik:
- `app_ar/src/studio/studioConsole.js`

Dozwolone jest też uzupełnienie CSS tylko jeśli obecny stan disabled/active jest wizualnie mylący, ale preferowane jest **bez zmian CSS**.

## Expected Logic
Przycisk „Skalibruj” powinien być aktywny, gdy spełniony jest którykolwiek bezpieczny warunek:
```javascript
autotune.ready_to_score === true
```
albo:
```javascript
autotune.state === "ready_to_score"
```
albo defensywnie:
```javascript
autotune.collected_count >= autotune.required_count
&& autotune.required_count > 0
&& autotune.state !== "idle"
```

Preferowana logika:
```javascript
const isReadyToScore =
    autotune.ready_to_score === true ||
    autotune.state === "ready_to_score" ||
    (
        Number(autotune.collected_count) >= Number(autotune.required_count) &&
        Number(autotune.required_count) > 0 &&
        autotune.state !== "idle"
    )
```
Następnie:
```javascript
calibrateButton.disabled = !isReadyToScore
```
lub odpowiednik zgodny z aktualną strukturą kodu.

## Out of Scope
Nie wolno w tym tasku:
* zmieniać backendu,
* zmieniać payloadu WebSocket,
* zmieniać `calibration_wizard_status.py`,
* zmieniać scoringu,
* zmieniać sample capture,
* zmieniać algorytmów CV,
* robić redesignu panelu,
* dokładać nowych funkcji,
* ruszać katalogu `Komercja/`,
* oznaczac taska jako `APPROVED BY CHATGPT SUPERVISOR` przed review.

## Files Allowed to Change
* `app_ar/src/studio/studioConsole.js`
* `.ai/TASKS_INDEX.md`
* `.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-CALIBRATE-BUTTON-FIX-001/*`
* `app_ar/studio.css` (tylko w razie absolutnej konieczności)

## Acceptance Criteria
1. Po zebraniu wymaganych próbek przy stanie `ready_to_score` przycisk „Skalibruj” jest aktywny.
2. W stanie `idle` przycisk „Skalibruj” pozostaje zablokowany.
3. W trakcie zbierania próbek, gdy `collected_count < required_count`, przycisk „Skalibruj” pozostaje zablokowany.
4. Po anulowaniu wizard wraca do `idle`, a „Skalibruj” znów jest zablokowany.
5. Kliknięcie „Skalibruj” wysyła właściwą komendę WebSocket.
6. `npm --prefix app_ar run build` przechodzi na PASS.
7. Manual smoke potwierdza, że błąd z TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001 został usunięty.
