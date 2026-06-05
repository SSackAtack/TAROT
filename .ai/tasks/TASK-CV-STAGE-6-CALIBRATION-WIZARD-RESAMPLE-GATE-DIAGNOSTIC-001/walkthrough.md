# Walkthrough — TASK-CV-STAGE-6-CALIBRATION-WIZARD-RESAMPLE-GATE-DIAGNOSTIC-001

Zdiagnozowano i wdrożono szczegółową diagnostykę dla Kreatora Kalibracji, która w pełni wyjaśnia proces zbierania i odrzucania próbek na unikalnych stanowiskach operatorskich.

## Przyczyna problemu i diagnoza
Logi wykazały, że kreator zbierał próbki pomyślnie, ale ze znacznym opóźnieniem (np. 4 minuty między próbką 1 a 2). Wynikało to z faktu, że na nieskalibrowanym stanowisku detekcja geometryczna często wykrywała 0 lub 2 karty zamiast oczekiwanej 1.
Próbki te były odrzucane cicho w kodzie `record_autotune_sample_from_snapshot(...)` ze względu na warunek `detected_count != expected_count`, co sprawiało wrażenie braku reakcji na ruch dłoni (brak re-armowania).

## Dokonane Zmiany

### Backend CV (`app_cv/main.py`)
- Rozbudowano funkcję `record_autotune_sample_from_snapshot`:
  - Dodano szczegółowe logowanie prób `[WIZARD DIAG]` do `cv_runtime.log`.
  - Wdrożono wywołania `add_operator_warning` przy każdym odrzuceniu ze względu na nieprawidłową geometrię. Operator od razu widzi w HUD informację: `"Wizard: Odrzucono snapshot dla one_card (wykryto 0 zamiast 1 kart)"`. Dzięki temu operator wie, że system zareagował na ruch, ale odrzucił próbkę z powodu błędnego ułożenia lub oświetlenia.

### Testy bramki Snapshotów (`app_cv/tests/test_snapshot_gate.py`)
- Dodano test `test_re_arms_after_publish_or_reject` potwierdzający, że po zakończeniu przetwarzania (zarówno publikacją `mark_published` jak i odrzuceniem `mark_rejected`) stan `SnapshotGate` poprawnie wraca do `holding_last_good` i re-armuje się na kolejny ruch dłoni.

### Testy zbierania próbki (`app_cv/tests/test_autotune_pipeline_sample_capture.py`)
- Dodano asercje weryfikujące, że warningi o odrzuceniu snapshotu są prawidłowo generowane w `operator_warnings`.
- Dodano nowy test: `test_does_not_collect_accepted_cards_on_empty_scenario` w celu weryfikacji generowania ostrzeżeń na pustej macie.

## Weryfikacja

### Testy automatyczne
Uruchomiono pełny pakiet 423 testów jednostkowych backendu:
- Rezultat: **PASS (100% zielono)**
- Czas wykonania: **21.45 s**
- Wszystkie 13 testów zbierania próbek i 6 testów bramki przeszło pomyślnie.
