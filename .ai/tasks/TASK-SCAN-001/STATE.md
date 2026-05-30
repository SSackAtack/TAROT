# Stan Zadania: TASK-SCAN-001

* **Nazwa zadania:** TASK-SCAN-001 — Scanner scan processor hardening
* **Data rozpoczęcia:** 2026-05-30
* **Data zakończenia:** 2026-05-30
* **Status:** `DONE` (W pełni zweryfikowany na fizycznym skanerze, wdrożono poprawki orientacji i proporcji)
* **Realizator (Owner):** Gemini

---

## Postęp
- [x] Detekcja konturów na obrazie roboczym i transformacja na pełnej rozdzielczości
- [x] Algorytm Robust Corner Ordering (brak zniekształceń i losowych obrotów kart)
- [x] Generowanie antyaliasingowej maski alfa dla zaokrąglonych rogów (WebP/PNG)
- [x] Wybór formatu zapisu w PNG, JPG, WebP (600x1032 px)
- [x] Pełna parametryzacja CLI przy użyciu biblioteki `argparse`
- [x] Automatyczna detekcja jasności tła na bazie pikseli brzegowych
- [x] Implementacja trybu dry-run (`--dry-run`) oraz podglądu detekcji (`--debug-overlay`)
- [x] Dodanie opcji wyboru stylu nazywania (`--naming generic|arcana`)
- [x] Weryfikacja syntetyczna dla jasnego i ciemnego tła w różnych formatach (PASS)
- [x] Dodanie generatora skanów testowych `scripts/generate_test_scan.py` do repozytorium w celach reprodukcji testów
- [x] Implementacja dodatkowego kroku skanowania i kadrowania rewersu (koszulki) karty na koniec procesu masowego asystenta
