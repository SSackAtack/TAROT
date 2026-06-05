# TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001 — RWS Fixture Expansion Offline Benchmark

## 1. Cel i Tło Techniczne

Uruchomienie offline benchmarku rozpoznawania kart (metoda ORB) na zatwierdzonej przez ChatGPT Supervisora 8-próbkowej paczce rozszerzającej Rider-Waite-Smith (RWS) minimal fixture (`logs/live_fixtures/stage6_real_camera_fixture_expansion_rws_minimal`). Benchmark weryfikuje poprawność rozpoznawania oraz decyzje bramki jakościowej (quality gate) w warunkach zróżnicowanego oświetlenia, odblasków (glare) i orientacji kart.

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

### Pliki Dopuszczone do Modyfikacji
* `[NEW]` [stage6_rws_expansion_benchmark.py](tools/cv_detection_lab/stage6_rws_expansion_benchmark.py)
* `[NEW]` [test_cv_detection_lab_stage6_rws_expansion_benchmark.py](app_cv/tests/test_cv_detection_lab_stage6_rws_expansion_benchmark.py)
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001/TASK.md`
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001/STATE.md`
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001/TEST_REPORT.md`
* `[NEW]` `.ai/tasks/TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001/CHANGELOG.md`
* `[MODIFY]` `.ai/TASKS_INDEX.md`

---

## 3. Poza Zakresem (Out of Scope)

* `app_cv/main.py`
* `app_cv/tarotvision/*`
* `app_ar/*`
* Payload WebSocket
* Konfiguracja runtime oraz integracja runtime
* Zmiana zatwierdzonych progów jakościowych (quality gate thresholds)
* Modyfikacja manifestów i ground_truth w fizycznych próbkach.

---

## 4. Kryteria Akceptacji (Acceptation Criteria)

Zadanie uznaje się za ukończone, gdy:
- [x] Przetworzono wszystkie 8 próbek z minimalnego fixture RWS.
- [x] Zaimplementowano skrypt benchmarku i pomyślnie wygenerowano pliki wynikowe: `report.json`, `report.md`, `matrix.csv`.
- [x] Dokonano podziału metryk na jasne/ciemne, jasne/glare, oraz orientację.
- [x] Wszystkie testy jednostkowe Pythona przechodzą bezbłędnie.
- [x] Dokumentacja zadania została w pełni zaktualizowana i zarejestrowana.
