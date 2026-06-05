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
- **empty**: **PASS**
- **one_card**: **DIAGNOSTIC_PASS / CALIBRATION_FAIL** (Bramka wyzwala kolejne próby snapshotów przy ruchu ręką. Diagnoza HUD działa poprawnie, lecz sam licznik nie dochodzi do 3/3 z powodu braku wykrywania karty przez detektor geometryczny na nieskalibrowanym stanowisku)
- **three_cards**: **NOT_RUN**
- **HUD/UX**: **PASS** (Deduplikacja działa poprawnie, powód odrzucenia jest precyzyjnie wyświetlany w sekcji NASTĘPNY KROK)
