# TASK-CV-STAGE-6-CALIBRATION-WIZARD-RESAMPLE-GATE-DIAGNOSTIC-001 — Calibration Wizard Resample Gate Diagnostics

## Cel

Zdiagnozować i naprawić problem ponownego zbierania próbek w kreatorze kalibracji scenariuszy `one_card` i `three_cards`. Wprowadzić szczegółową diagnostykę odrzucania próbek, aby operator wiedział, dlaczego system odrzuca dany snapshot.

## Kontekst

Po ostatnim fixie kalibracja `one_card` nie blokuje się już na rozpoznaniu, ale w realnym działaniu pobiera tylko jeden snapshot / jedną próbkę. Mimo kolejnych ruchów przed kamerą licznik nie idzie dalej do 3/3. Pusta mata działa poprawnie.

Prawdopodobną przyczyną jest to, że na uniezależnionym od rozpoznania (nieskalibrowanym) stanowisku, detekcja geometryczna często wykrywa 0 lub np. 2 karty (np. przez odbicia, cień dłoni lub brak dostrojonych progów). Powoduje to ciche odrzucenie snapshotu przez warunek `detected_count != expected_count` w `record_autotune_sample_from_snapshot(...)` bez żadnego komunikatu w logach ani HUD, przez co operator odnosi wrażenie, że system nie reaguje na ruch.

## Zakres

- Modyfikacja `app_cv/main.py`:
  - Dodać szczegółową i czytelną diagnostykę logów (zarówno do konsoli operatorskiej/HUD za pomocą `add_operator_warning`, jak i logu `cv_runtime.log` przez `log_event`) dla każdego odrzuconego i zebranego snapshotu w kreatorze kalibracji.
  - Raportować dokładnie: scenariusz, wykrytą liczbę geometryczną, oczekiwaną liczbę oraz powód odrzucenia/akceptacji próbki.
- Modyfikacja `app_cv/tests/test_snapshot_gate.py`:
  - Dodać testy sprawdzające poprawne przejścia stanu i re-armowanie bramki `SnapshotGate` po publikacji oraz odrzuceniu.
- Aktualizacja `app_cv/tests/test_autotune_pipeline_sample_capture.py` w celu dostosowania asercji do nowo zalogowanych warningów/logów.

## Kryteria akceptacji

- Każda próba rejestracji próbki kalibracji (nawet odrzucona) generuje jasny komunikat diagnostyczny w logach i HUD konsoli operatorskiej.
- Testy bramki `SnapshotGate` potwierdzają poprawne re-armowanie stanu.
- Wszystkie testy jednostkowe (w tym testy integracyjne) przechodzą pomyślnie.
