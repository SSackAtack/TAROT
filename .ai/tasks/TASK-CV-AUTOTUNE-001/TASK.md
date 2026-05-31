# TASK-CV-AUTOTUNE-001 — Offline single-frame rectangle autotune prototype

## 1. Cel i Tło Techniczne

Zbudować offline prototyp autotunera, który na pojedynczym zapisanym obrazie/snapshotcie i znanej karcie testuje różne parametry detekcji prostokąta karty, korzystając z nowej parametryzacji `find_card_quads` z TASK-CV-RECT-001.

Celem zadania jest udowodnienie, że backend potrafi automatycznie zidentyfikować optymalną kombinację parametrów (progi Canny, min area, tryb konturów), przy której słabo widoczna karta na ciemnym tle (np. Boski Tarot) zostaje stabilnie wykryta jako prostokątny kandydat.

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

### Pliki Dopuszczone do Modyfikacji
* `[NEW]` `auto_tuner.py` (app_cv/tarotvision/auto_tuner.py)
* `[NEW]` `test_auto_tuner.py` (app_cv/tests/test_auto_tuner.py)
* `[MODIFY]` `TASKS_INDEX.md` (.ai/TASKS_INDEX.md)

---

## 3. Poza Zakresem (Out of Scope)

* Brak zmian w `main.py`, `card_recognition.py`, `camera_session.py`, `studioConsole.js`, `studio.css`, skryptach startowych, jsonach manifestu.
* Brak obsługi live-apply, zapisu profili JSON, integracji z WebSocket, suwaków w Studio Console.
* Brak zmian progów ORB, FLANN, RANSAC.

---

## 4. Kryteria Akceptacji (Acceptance Criteria)

Zadanie uznaje się za ukończone, gdy:
- [x] Utworzono moduł `auto_tuner.py` zawierający funkcję `tune_card_detection_params` oraz klasę wrapper `AutoTuner`.
- [x] Zaimplementowano rygorystyczny algorytm wyszukiwania w ograniczonej przestrzeni coarse search (max 250 iteracji).
- [x] Zaimplementowano funkcję scoringową `score_candidate_quad` oceniającą quady pod kątem proporcji, wielkości i centralności na obrazie.
- [x] Dodano testy jednostkowe w `test_auto_tuner.py` w pełni pokrywające wymagane scenariusze.
- [x] Wszystkie testy backendu (187) przechodzą bezbłędnie.
- [x] Frontend buduje się poprawnie (`npm run build`).
