# Raport testowy dla TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001

## Wyniki testów i weryfikacji

| Test | Result | Evidence / Notes |
| :--- | :--- | :--- |
| `npm --prefix app_ar run build` | PASS | Vite buduje produkcyjny frontend bez błędów |
| backend status tests | PASS | $env:PYTHONPATH="app_cv"; python -m unittest app_cv.tests.test_calibration_wizard_status -v => 13 testów OK |
| Studio start | PASS | Serwer deweloperski uruchomił się pod adresem http://localhost:5173/ |
| WebSocket connection | PASS | WebSocket nawiązał stabilne połączenie |
| idle state | PASS | Stan początkowy zmapowany poprawnie, przyciski i placeholdery wyświetlane bez błędów |
| empty scenario (UI) | PASS | Zebrano 3/3 próbek (symulacja), przycisk "Skalibruj" staje się aktywny i kliknięcie wysyła komendę `autotune_calibrate` |
| one_card scenario (UI) | PASS | Zebrano próbki (symulacja), przycisk "Skalibruj" staje się aktywny i wysyła komendę kalibracji |
| three_cards scenario (UI) | PASS | Zebrano próbki (symulacja), przycisk "Skalibruj" staje się aktywny i wysyła komendę kalibracji |
| cancel/reset | PASS | Przycisk Anuluj działa poprawnie, resetuje stan sesji i blokuje przycisk "Skalibruj" |
| backend logs clean | PASS | Brak tracebacków w logach |
| Manual UI smoke simulation | PASS | Wszystkie scenariusze i zachowanie przycisków przetestowane pomyślnie w przeglądarce po merge PR #26 |
| manual camera smoke | FAIL | Przyciski wyboru scenariusza (np. "1 KARTA") pozostają zablokowane (disabled=true) po zakończeniu kalibracji pustej maty |
| GitHub Actions CI | PENDING | Oczekiwanie na runy po pushu |

## Podsumowanie wymagane przez instrukcję zadania:

* komenda: `npm --prefix app_ar run build`
* czy frontend build był: PASS
* czy backend tests były: PASS
* czy smoke Studio UI był: PASS (UI smoke simulation: PASS)
* czy manual camera smoke był: FAIL (przyciski startu zablokowane po kalibracji pustej maty)
* czy GitHub Actions był: PENDING

## Wykryty błąd logiczny (Blocker 2):
Po zakończeniu scenariusza `empty` i kliknięciu "Skalibruj", backend przechodzi w stan `recommendation_ready` (UI wyświetla "REKOMENDACJA GOTOWA"). 

W pliku `app_ar/src/studio/studioConsole.js` (linie 479-485) przyciski startu scenariusza są aktywowane warunkiem `isIdleOrCancelled`:
```javascript
const isIdleOrCancelled = state === 'idle' || state === 'cancelled'
if (btnStartEmpty) btnStartEmpty.disabled = !isIdleOrCancelled
if (btnStartOne) btnStartOne.disabled = !isIdleOrCancelled
if (btnStartThree) btnStartThree.disabled = !isIdleOrCancelled
```
Ponieważ `state` wynosi `'recommendation_ready'`, flagi te są trwale ustawiane na `disabled = true`, co uniemożliwia operatorowi przejście do kolejnego kroku (kliknięcia `1 KARTA` lub `3 KARTY`), mimo że instrukcja "NASTĘPNY KROK" wprost to zaleca.

### Sugerowana poprawka:
Zmienić warunek aktywacji przycisków startu na:
```javascript
const canStartScenario = state !== 'collecting' && state !== 'ready_to_score'
if (btnStartEmpty) btnStartEmpty.disabled = !canStartScenario
if (btnStartOne) btnStartOne.disabled = !canStartScenario
if (btnStartThree) btnStartThree.disabled = !canStartScenario
```

## Wykryty błąd logiczny:
W pliku `app_ar/src/studio/studioConsole.js` (linia 443) zdefiniowano warunek włączenia przycisku kalibracji:
`btnCalibrate.disabled = !(isCollecting && readyToScore)`
Jednak po zebraniu kompletnych próbek (3/3), backend zmienia stan (`state`) z `"collecting"` na `"ready_to_score"`. Przez to zmienna `isCollecting = state === 'collecting'` przyjmuje wartość `false`, co trwale blokuje przycisk "Skalibruj".

### Sugerowana poprawka:
Zmienić warunek na:
`btnCalibrate.disabled = !((isCollecting || state === 'ready_to_score') && readyToScore)`
