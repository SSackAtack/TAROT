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

## Ponowna weryfikacja po zmergowaniu poprawki (PR #26)

1. **Pobranie poprawek i merge mastera**:
   - Zmergowano najnowszy `master` zawierający fix z [TASK-CV-STAGE-6-CALIBRATION-WIZARD-CALIBRATE-BUTTON-FIX-001](file:///e:/Antigravity/Projekty/TAROT/.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-CALIBRATE-BUTTON-FIX-001/TASK.md) do brancha smoke testu.

2. **Przebieg ponownych testów dymnych (Symulacja UI)**:
   - Podniesiono deweloperski serwer Vite w tle.
   - Zweryfikowano wszystkie scenariusze kalibracji (`empty`, `one_card`, `three_cards`) pod kątem zachowania przycisków za pomocą symulacji stanów WebSocket w konsoli JS:
     - We wszystkich scenariuszach przycisk „Skalibruj” staje się w 100% aktywny (enabled) dokładnie po zebraniu kompletnych próbek (3/3) oraz w stanie `ready_to_score`.
     - Kliknięcie przycisku „Skalibruj” poprawnie przesyła komendę `{ "type": "autotune_calibrate" }` przez WebSocket.
     - Przycisk „Anuluj” poprawnie resetuje stan i blokuje przycisk kalibracji.
   - Wszystkie scenariusze w warunkach symulacji zakończyły się wynikiem **PASS**.

3. **Fizyczny test operatorski (HP EliteBook 830 G6 + AnkerWork C310)**:
   - Operator (Michał) uruchomił system CV na fizycznym sprzęcie.
   - Pomyślnie przeprowadzono scenariusz `empty` (Pusta mata) i zebrano 3/3 próbek.
   - Przycisk "Skalibruj" poprawnie się odblokował i po kliknięciu wywołał kalibrację oraz scoring.
   - Backend zwrócił stan `recommendation_ready` (wynik score 0.54, ocena "Problem") i zalecił przejście do testu 1 karta.

4. **Wykryty nowy problem (Blocker 2 - FAIL)**:
   - Po otrzymaniu stanu `recommendation_ready`, wszystkie przyciski wyboru scenariusza (`PUSTA MATA`, `1 KARTA`, `3 KARTY`) oraz przycisk "Skalibruj" pozostały zablokowane (`disabled = true`).
   - Operator nie mógł kliknąć przycisku `1 KARTA` ani `3 KARTY` bez uprzedniego kliknięcia "Anuluj" (co resetuje cały postęp kalibracji).
   - Przyczyna: Warunek aktywacji przycisków startowych w [studioConsole.js](file:///e:/Antigravity/Projekty/TAROT/app_ar/src/studio/studioConsole.js#L479) ogranicza ich działanie wyłącznie do stanów `idle` oraz `cancelled`. W stanie `recommendation_ready` przyciski są zablokowane.

5. **Koniec testu**:
   - Zgodnie z wytycznymi zadania integracyjnego, test przerwano po wykryciu blockera. Nie wprowadzano zmian w kodzie produkcyjnym. Zgłoszono błąd do Supervisor review.
