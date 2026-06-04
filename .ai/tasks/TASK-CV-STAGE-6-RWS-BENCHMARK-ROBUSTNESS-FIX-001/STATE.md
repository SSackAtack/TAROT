# Stan Prac — TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001

## 1. Status Ogólny
* **Status:** `APPROVED`
* **Realizator (Owner):** Gemini
* **Gałąź Git:** task/cv-stage-6-rws-expansion-benchmark-001

---

## 2. Metadane Zadania

* **Decision:** APPROVED_OFFLINE_RWS_BENCHMARK_ROBUSTNESS_FIX_ONLY
* **Supervisor status:** RWS_BENCHMARK_ROBUSTNESS_FIX_APPROVED_OFFLINE_ONLY
* **Runtime:** NOT_CHANGED
* **Benchmark:** OFFLINE_ONLY
* **Fixture:** stage6_real_camera_fixture_expansion_rws_minimal
* **Fixture status:** APPROVED_RWS_EXPANSION_FIXTURE_OFFLINE_ONLY_BY_CHATGPT_SUPERVISOR
* **Runtime approval:** NO_RUNTIME_INTEGRATION, NO_RUNTIME_THRESHOLD_APPROVAL

---

## 3. Wyniki i Metryki Benchmarku (Rerun)

### Główne statystyki i dokładność ORB
* **sample_count:** 8
* **processed_count:** 8
* **extraction_failed_count:** 0
* **orb_attempted_count:** 8
* **ORB Top-1 all:** 50.0%
* **ORB Top-3 all:** 62.5%
* **ORB Top-1 extracted-only:** 50.0%
* **ORB Top-3 extracted-only:** 62.5%
* **ORB Top-1 ACCEPT subset:** 100.0%
* **ORB Top-3 ACCEPT subset:** 100.0%

### Rozkład Decyzji Quality Gate
* **ACCEPT_FOR_IDENTIFICATION:** 4
* **RETRY_CAPTURE:** 3
* **MANUAL_REVIEW:** 1
* **EXTRACTION_FAILED:** 0

### Wydajność (Runtime Proxy)
* **Średni czas rozpoznania**: 436.552 ms
* **Mediana (p50)**: 434.272 ms
* **Centyl p95**: 510.426 ms
