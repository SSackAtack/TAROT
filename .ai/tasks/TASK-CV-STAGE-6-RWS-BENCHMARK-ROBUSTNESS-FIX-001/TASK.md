# TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001 — Robustness and Reporting Fix for RWS Offline Benchmark

## 1. Cel i Tło Techniczne
Zadanie to ma na celu poprawienie niezawodności i testowalności offline runnera benchmarku RWS. Poprzednia wersja w przypadku błędu ekstrakcji (`extract_card()`) niepotrzebnie próbowała uruchomić metodę ORB i oceniać jakość na czarnym obrazie (dummy crop). Ponadto, metryki dokładności ORB na całym zestawie były zniekształcone przez próbki, w których ekstrakcja w ogóle się nie powiodła. Niniejsze zadanie oddziela te zachowania i tworzy testowalny helper agregacji metryk.

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)
* `[MODIFY]` [stage6_rws_expansion_benchmark.py](tools/cv_detection_lab/stage6_rws_expansion_benchmark.py)
* `[MODIFY]` [test_cv_detection_lab_stage6_rws_expansion_benchmark.py](app_cv/tests/test_cv_detection_lab_stage6_rws_expansion_benchmark.py)
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001/TASK.md`
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001/STATE.md`
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001/TEST_REPORT.md`
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001/CHANGELOG.md`
* `[MODIFY]` `.ai/TASKS_INDEX.md`

---

## 3. Poza Zakresem (Out of Scope)
* Zmiana thresholdów bramki jakościowej (quality gate).
* Tunowanie metody ORB.
* Zmiany w plikach runtime (`app_cv/main.py`, `app_cv/tarotvision/*`, `app_ar/*`, WebSocket).
* Modyfikacja fizycznych próbek i manifestów.

---

## 4. Kryteria Akceptacji (Acceptation Criteria)
Zadanie uznaje się za ukończone, gdy:
- [x] W przypadku błędu `extract_card` proces nie próbuje uruchomić ORB ani nie uwzględnia próbki w czasach trwania ORB. Wynik bramki jakości to `MANUAL_REVIEW` z powodem `EXTRACTION_FAILED`.
- [x] Dodano nowe kolumny do `matrix.csv` oraz raportu `report.json`: `extraction_error`, `extraction_failed_count`, `orb_attempted`.
- [x] Wdrożono oddzielne metryki ORB: `orb_top1_accuracy_extracted_only` oraz `orb_top3_accuracy_extracted_only`.
- [x] Logika agregacji metryk została wydzielona do funkcji `build_benchmark_summary`.
- [x] Dodano testy jednostkowe w `test_cv_detection_lab_stage6_rws_expansion_benchmark.py` sprawdzające zachowanie summary dla syntetycznych próbek i błędów ekstrakcji.
- [x] Ponowny bieg offline benchmarku na minimalnym zestawie RWS przyniósł spójne wyniki.
