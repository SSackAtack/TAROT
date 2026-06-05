# TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SCORING-001

## Cel
Dodać scoring jakości zebranych próbek wizardu kalibracji, pozwalający odpowiedzieć operatorowi na pytanie, czy stanowisko jest gotowe do sesji oraz co ewentualnie poprawić (oświetlenie, ostrość, cienie, itp.).

## Zakres
- Utworzenie modułu `calibration_wizard_scoring.py` z czystą logiką scoringu (JSON-safe raport).
- Integracja scoringu w `main.py` pod komendę `autotune_calibrate`.
- Resetowanie raportu przy `autotune_start` i `autotune_cancel`.
- Wprowadzenie komunikacji diagnostycznej dla operatora poprzez wskaźniki `quality_report` w payloadzie statusu WebSocket.
- Ochrona kompatybilności rekomendacji profilowych (brak auto-apply parametrów).
- Zapewnienie odporności na brakujące dane w próbkach.

## Kryteria akceptacji
- Dodano scoring jakości próbek jako czystą funkcję w osobnym module.
- Scoring obsługuje scenariusze `empty`, `one_card`, `three_cards`.
- Raport zawiera pola: `score`, `grade`, `ready_for_session`, `scenario_results`, `operator_messages`, `warnings`, `blocking_issues`.
- `autotune_calibrate` wyzwala scoring i zapisuje `quality_report` do statusu.
- `autotune_start` oraz `autotune_cancel` poprawnie resetują stan raportu.
- Brak aktywnej sesji nie zmienia działania pipeline.
- Wszystkie testy automatyczne i integracyjne przechodzą pomyślnie.
