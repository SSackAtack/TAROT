# Wykaz Zmian (Changelog) — TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001

## 1. Pliki Produkcyjne

### `tools/cv_detection_lab/stage6_rws_expansion_benchmark.py`
* Zaimplementowano odporne zachowanie w przypadku błędu `extract_card` — pomijane jest wywołanie ORB oraz statystyki czasu wykonania. Taka próbka uzyskuje status bramki `MANUAL_REVIEW` z powodem `EXTRACTION_FAILED`.
* Dodano nowe kolumny w `matrix.csv` oraz pola w `report.json`: `extraction_error`, `extraction_failed_count`, `orb_attempted`.
* Dodano oddzielne metryki dokładności ORB: `orb_top1_accuracy_extracted_only` oraz `orb_top3_accuracy_extracted_only`.
* Wydzielono logikę obliczania statystyk i metryk do niezależnej, testowalnej funkcji `build_benchmark_summary`.

---

## 2. Pliki Testowe i Konfiguracyjne

### `app_cv/tests/test_cv_detection_lab_stage6_rws_expansion_benchmark.py`
* Dodano test jednostkowy `test_build_benchmark_summary_aggregates_extraction_failures` sprawdzający poprawne zachowanie agregacji przy sztucznych próbkach zawierających błędy ekstrakcji oraz prawidłowe filtrowanie metryk extracted-only i accept_subset.
* Dodano test `test_build_benchmark_summary_handles_empty_runtimes` weryfikujący stabilność działania helpera przy braku zmierzonych czasów wykonania (runtimes).
