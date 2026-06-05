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
| manual camera smoke | PASS | Druga runda testu fizycznego powiodła się. Kalibracja przechodzi od pustej maty, 1 do 3 kart na realnej kamerze USB (HP EliteBook 830 G6 + AnkerWork C310). Wszystkie przyciski wyboru kolejnych scenariuszy są aktywne w stanie `recommendation_ready` i poprawnie uruchamiają kolejne kroki. |
| GitHub Actions CI | PASS | Runy weryfikacji kodu przeszły na zielono na masterze |

## Podsumowanie wymagane przez instrukcję zadania:

* komenda: `npm --prefix app_ar run build`
* czy frontend build był: PASS
* czy backend tests były: PASS
* czy smoke Studio UI był: PASS (UI smoke simulation: PASS)
* czy manual camera smoke był: PASS (przepływ pusty -> 1 karta -> 3 karty zweryfikowany na stanowisku)
* czy GitHub Actions był: PASS

## Dowód weryfikacji (Evidence)
* Zrzut ekranu po zakończeniu kalibracji scenariusza "Trzy karty" z wynikiem score=0.98 (ocena "Bardzo dobrze") z odblokowanymi i aktywnymi przyciskami wyboru scenariuszy:
  ![Weryfikacja fizyczna zakończona sukcesem](file:///e:/Antigravity/Projekty/TAROT/.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001/evidence_wizard_success.png)
