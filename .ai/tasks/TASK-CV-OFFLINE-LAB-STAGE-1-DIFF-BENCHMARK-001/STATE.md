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

## TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-REFINE-001

### Summary

Doprecyzowano benchmark Stage 1 tak, aby decyzja nie opierała się wyłącznie na prostej zgodności `region_count == expected_region_count`. Benchmark raportuje teraz surowe komponenty, komponenty po filtracji, regiony po prostym merge bliskich bboxów oraz liczniki odrzuceń small/large. `region_count` pozostaje dla kompatybilności, ale oznacza teraz `merged_region_count`, a `verdict_basis` jawnie zapisuje tę semantykę.

### Metrics added

- `raw_region_count`
- `filtered_region_count`
- `merged_region_count`
- `ignored_small_count`
- `ignored_large_count`
- `largest_region_area_ratio`
- `largest_merged_region_area_ratio`
- `verdict_basis`
- `recommendation_status`
- `manual_review_paths`

### Benchmark result

- `recommended_method`: `gray_absdiff_gaussian`
- `recommendation_status`: `PROVISIONAL_RECOMMENDED`
- `rows`: `42`
- output: `logs/offline_replay/stage1_diff`

### Tests

- `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest app_cv.tests.test_cv_detection_lab_stage1 -v` => PASS, 8 testów.
- `python -B -m py_compile tools\cv_detection_lab\methods.py tools\cv_detection_lab\stage1_diff_benchmark.py app_cv\tests\test_cv_detection_lab_stage1.py` => PASS.
- `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python tools\cv_detection_lab\stage1_diff_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage1_diff` => PASS, 42 rows.
- `$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv;.'; python -m unittest discover -s app_cv\tests -v` => PASS, 324 testy.

### Decision

Na tym etapie: `PROVISIONAL_RECOMMENDED: gray_absdiff_gaussian`. Nie oznaczono Stage 1 jako `APPROVED_STAGE_1_METHOD`, bo wymagany jest ręczny review overlay.

### Required next action

Supervisor ma przejrzeć overlay dla `gray_absdiff_gaussian`:

```text
logs/offline_replay/stage1_diff/gray_absdiff_gaussian/empty_to_empty/regions_overlay.png
logs/offline_replay/stage1_diff/gray_absdiff_gaussian/empty_to_one_card/regions_overlay.png
logs/offline_replay/stage1_diff/gray_absdiff_gaussian/empty_to_three_cards/regions_overlay.png
logs/offline_replay/stage1_diff/gray_absdiff_gaussian/one_card_to_three_cards/regions_overlay.png
logs/offline_replay/stage1_diff/gray_absdiff_gaussian/one_card_to_empty/regions_overlay.png
logs/offline_replay/stage1_diff/gray_absdiff_gaussian/three_cards_to_empty/regions_overlay.png
```

Dopiero po tym można zatwierdzić Stage 1 albo zlecić dodatkowy refinement.
