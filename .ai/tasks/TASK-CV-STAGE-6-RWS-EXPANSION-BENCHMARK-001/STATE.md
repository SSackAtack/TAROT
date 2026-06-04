# Stan Prac — TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001

## 1. Status Ogólny
* **Status:** `DONE`
* **Realizator (Owner):** Gemini
* **Gałąź Git:** task/cv-stage-6-rws-expansion-benchmark-001

---

## 2. Wymagane Metadane Zadania

* **Decision:** PENDING_SUPERVISOR_REVIEW
* **Fixture:** stage6_real_camera_fixture_expansion_rws_minimal
* **Fixture status:** APPROVED_RWS_EXPANSION_FIXTURE_OFFLINE_ONLY_BY_CHATGPT_SUPERVISOR
* **Runtime:** NOT_CHANGED
* **Benchmark:** OFFLINE_ONLY
* **Runtime approval:** NO_RUNTIME_INTEGRATION, NO_RUNTIME_THRESHOLD_APPROVAL

---

## 3. Wyniki i Metryki Benchmarku

### Podsumowanie Główne
* **Total samples**: 8
* **Processed samples**: 8
* **ORB Top-1 accuracy (all)**: 50.0%
* **ORB Top-3 accuracy (all)**: 62.5%
* **ORB Top-1 accuracy (accept subset)**: 100.0% (Liczba próbek: 4)
* **ORB Top-3 accuracy (accept subset)**: 100.0%

### Rozkład Decyzji Quality Gate
* **ACCEPT_FOR_IDENTIFICATION**: 4
* **RETRY_CAPTURE**: 3
* **MANUAL_REVIEW**: 1

### Wyniki Szczegółowe wg Kategorii

| Category | Count | ORB Top-1 | Accept | Retry | Manual | Accept Top-1 |
|---|---:|---:|---:|---:|---:|---:|
| rws_bright_clear | 2 | 100.0% | 2 | 0 | 0 | 100.0% |
| rws_bright_glare | 2 | 0.0% | 0 | 1 | 1 | n/a |
| rws_dark_clear | 2 | 100.0% | 2 | 0 | 0 | 100.0% |
| rws_dark_glare | 2 | 0.0% | 0 | 2 | 0 | n/a |

### Podsumowania Grupowe

#### Jasne (Bright) vs Ciemne (Dark)
* **Bright**: 4 próbki, ORB Top-1: 50%, Akceptowane: 2, Retry: 1, Manual: 1
* **Dark**: 4 próbki, ORB Top-1: 50%, Akceptowane: 2, Retry: 2, Manual: 0

#### Bez odblasków (Clear) vs Odblaski (Glare)
* **Clear**: 4 próbki, ORB Top-1: 100%, Akceptowane: 4, Retry: 0, Manual: 0
* **Glare**: 4 próbki, ORB Top-1: 0%, Akceptowane: 0, Retry: 3, Manual: 1

#### Upright vs Reversed
* **Upright**: 4 próbki, ORB Top-1: 50%, Akceptowane: 2, Retry: 2, Manual: 0
* **Reversed**: 4 próbki, ORB Top-1: 50%, Akceptowane: 2, Retry: 1, Manual: 1

### Wydajność (Wątek CV Proxy)
* **Średni czas rozpoznania**: 436.552 ms
* **Mediana (p50)**: 434.272 ms
* **Centyl p95**: 510.426 ms

---

## 4. Co Zostało Zrobione (Completed)
- [x] Naprawiono brakujący import `statistics` w skrypcie benchmarku.
- [x] Uruchomiono offline benchmark na 8 próbkach RWS.
- [x] Wygenerowano raporty: `report.json`, `report.md`, `matrix.csv`.
- [x] Stworzono test jednostkowy `test_cv_detection_lab_stage6_rws_expansion_benchmark.py`.
- [x] Zweryfikowano działanie testów jednostkowych lokalnie.
