# TEST REPORT: TASK-CV-GEOMETRY-FALLBACK-001

* **Data testu:** 2026-06-01
* **Asystent AI:** Codex
* **Gałąź testowa:** `codex/snapshot-first-recognition-hardening`

## Testy uruchomione

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=E:\Antigravity\Projekty\TAROT\.tmp_pydeps;app_cv && python -m unittest app_cv.tests.test_detection_diagnostics app_cv.tests.test_snapshot_analyzer app_cv.tests.test_card_detection_profiles app_cv.tests.test_table_calibration app_cv.tests.test_pipelines_contract -v"
```

Wynik: `PASS`, 35 testów.

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=E:\Antigravity\Projekty\TAROT\.tmp_pydeps;app_cv && python -m py_compile app_cv\main.py app_cv\tarotvision\card_detection.py app_cv\tarotvision\card_detection_profiles.py app_cv\tarotvision\detection_diagnostics.py app_cv\tarotvision\snapshot_analyzer.py app_cv\tarotvision\table_calibration.py app_cv\tarotvision\pipelines\snapshot_first.py"
```

Wynik: `PASS`.

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=E:\Antigravity\Projekty\TAROT\.tmp_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Wynik: `PASS`, 219 testów. Podczas importu `main.py` pojawił się background thread exception dla portu WebSocket `8765`, bo port był już zajęty, ale cały przebieg unittest zakończył się `OK`.

## Uwagi środowiskowe

Pierwsze uruchomienie testów na `C:\tmp\tarot_pydeps` zostało zablokowane przez uszkodzony namespace `cv2` bez `IMREAD_UNCHANGED`. Zależności testowe zostały zainstalowane do świeżego katalogu `E:\Antigravity\Projekty\TAROT\.tmp_pydeps` i na nim wykonano weryfikację.

## Ryzyka do live testu

- `minAreaRect` zwiększa liczbę kandydatów geometrycznych, ale publikacja karty nadal wymaga rozpoznania ORB.
- Kolejne luzowanie 3/2/1-edge nie zostało wdrożone; wymaga osobnego spike po analizie nowych metryk.
