# Stan Prac — TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001

## 1. Status Ogólny

* **Status:** `DONE`
* **Realizator (Owner):** Codex
* **Gałąź Git:** `task/cv-event-first-plan-001-clarify-autotune-runtime`

---

## 2. Co Zostało Zrobione

- [x] Utworzono izolowany pakiet `tools/cv_detection_lab/`.
- [x] Dodano metody Stage 1 `TEST_NOW` bez nowych zależności.
- [x] Dodano CLI `stage1_diff_benchmark.py`.
- [x] Dodano testy jednostkowe dla fixture, raportowania i baseline no-change.
- [x] Uruchomiono benchmark na realnych fixture.

---

## 3. Co Pozostało do Zrobienia

- [ ] Supervisor powinien przejrzeć debug overlay dla zwycięskich metod.
- [ ] Po decyzji Stage Gate można zaplanować Stage 2 Region Segmentation albo mały refinement Stage 1.

## Session Status (2026-06-03 Codex)

Stan aktualny: offline benchmark Stage 1 działa i wygenerował pierwszą macierz wyników na zatwierdzonych fixture.

Co zostało zrobione: `gray_absdiff_gaussian` został wskazany przez benchmark jako rekomendowana metoda, bo uzyskał `PASS` na wszystkich 6 parach przy niskim runtime. `gray_absdiff_median`, `lab_absdiff_weighted` i `hsv_absdiff_weighted` też uzyskały komplet `PASS`, ale są wolniejsze albo bardziej kosztowne.

Kolejne kroki: Supervisor powinien zatwierdzić metodę Stage 1 po obejrzeniu debug obrazów w `logs/offline_replay/stage1_diff/`.
