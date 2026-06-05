# TEST REPORT: TASK-CV-STAGE-6-CALIBRATION-WIZARD-RESAMPLE-GATE-DIAGNOSTIC-001

## Rezultaty testów jednostkowych

Uruchomiono pełny suite testów backendowych poleceniem:
`cmd.exe /c "set PYTHONPATH=app_cv && python -m unittest discover -s app_cv/tests -p \"test_*.py\""`

### Rezultat końcowy
- **Status**: **PASS (OK)**
- **Liczba wykonanych testów**: 423
- **Czas wykonania**: 21.454s

### Przebieg testów jednostkowych bramki i zbierania próbek
- Testy bramki `SnapshotGate` (w tym nowy test `test_re_arms_after_publish_or_reject`) -> PASS (6/6)
- Testy zbierania próbek `test_autotune_pipeline_sample_capture` -> PASS (13/13)

## Rezultaty testów fizycznych (Smoke Test)

Przeprowadzono test dymny na stanowisku deweloperskim z kamerą USB (Commit `dd5433d`):
- **empty**: **PASS** (licznik 3/3, bez fałszywych warningów)
- **one_card**: **PASS** (bramka wyzwala kolejne próby snapshotów przy ruchu ręką, powód odrzucenia - brak detekcji karty/złe oświetlenie - jest poprawnie raportowany i nie powoduje spamu w HUD)
- **HUD / UX**: **PASS** (komunikaty o odrzuceniu próbek ze względu na geometrię wyświetlają się w sekcji NASTĘPNY KROK w panelu kalibracji i są deduplikowane)
