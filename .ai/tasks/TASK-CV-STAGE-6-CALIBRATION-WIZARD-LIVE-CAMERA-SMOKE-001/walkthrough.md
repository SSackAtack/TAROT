# Walkthrough — TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001

## Informacje ogólne
* Data i godzina: 2026-06-05 14:05
* Branch: `task/cv-stage-6-calibration-wizard-live-camera-smoke-001`
* Commit hash: PENDING (dokumentacja)
* System/Sprzęt: HP EliteBook 830 G6 + AnkerWork C310

## Przebieg testu

1. **Uruchomienie baseline**:
   - Przetestowano budowanie frontendu (`npm run build` w `app_ar`): **PASS**.
   - Przetestowano testy jednostkowe backendu (`test_calibration_wizard_status.py`, `test_calibration_wizard_scoring.py`): **PASS**.

2. **Testy integracyjne na żywo**:
   - Podniesiono backend CV oraz deweloperski serwer Vite w tle.
   - Otworzono konsolę Studio w przeglądarce i nawiązano stabilne połączenie WebSocket.
   - Rozpoczęto scenariusz `empty` (Pusta mata). Operator zdjął kartę i machnął ręką nad matą.
   - System pomyślnie zarejestrował 3/3 próbek i przeszedł do stanu `ready_to_score: true` oraz `overall_wizard_ready: true`.

3. **Wykryty problem (FAIL)**:
   - Przycisk "Skalibruj" (`autotune_calibrate`) pozostał zablokowany (`disabled = true`).
   - Inspekcja kodu wykazała błąd logiczny w [studioConsole.js](file:///e:/Antigravity/Projekty/TAROT/app_ar/src/studio/studioConsole.js#L486):
     ```javascript
     if (btnCalibrate) btnCalibrate.disabled = !(isCollecting && readyToScore)
     ```
     Po zebraniu próbek stan (`state`) zmienia się z `"collecting"` na `"ready_to_score"`, przez co `isCollecting` staje się `false` i przycisk jest trwale blokowany.

4. **Koniec testu**:
   - Zgodnie z instrukcją zadania, test przerwano bez dokonywania zmian w kodzie produkcyjnym.
   - Wyniki udokumentowano, serwery wyłączono.
   - Zrzuty ekranu dokumentujące stany znajdują się w katalogu scratch.
