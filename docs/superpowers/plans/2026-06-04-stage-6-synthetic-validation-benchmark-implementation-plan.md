# Stage 6 Synthetic Validation Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zbudować deterministyczny offline benchmark porównujący ORB i AKAZE na szerszym syntetycznym zestawie Stage 6.

**Architecture:** Osobny generator tworzy próbki w pamięci i manifest reprodukowalności. Osobny runner uruchamia istniejące metody identyfikacji, agreguje wyniki per method/category/orientation i zapisuje raporty oraz ograniczony zestaw debug sheetów. Kod pozostaje poza runtime.

**Tech Stack:** Python 3, OpenCV, NumPy, `unittest`, istniejące `tools/cv_detection_lab/stage6_identification_methods.py`.

---

## File Structure

- Create `tools/cv_detection_lab/stage6_synthetic_dataset.py`: deterministyczny wybór kart i transformacje obrazów.
- Create `tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py`: wykonanie metod, rejection, agregacja i raporty.
- Create `app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py`: testy generatora, metryk i artefaktów.
- Create `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001/{STATE.md,CHANGELOG.md,TEST_REPORT.md}` po wykonaniu benchmarku.
- Modify `.ai/TASKS_INDEX.md` i główny plan Stage 6 po zakończeniu.

### Task 1: Deterministyczny generator datasetu

**Files:**
- Create: `tools/cv_detection_lab/stage6_synthetic_dataset.py`
- Create: `app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py`

- [ ] **Step 1: Write failing tests for deterministic selection and manifest**

Dodaj testy potwierdzające, że dwa przebiegi z tym samym seedem zwracają identyczne `sample_id`, źródła i parametry oraz wybierają dokładnie 24 równomiernie rozłożone karty.

- [ ] **Step 2: Run tests and verify RED**

Run:
`python -m unittest app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v`

Expected: `ModuleNotFoundError` dla `stage6_synthetic_dataset`.

- [ ] **Step 3: Implement dataset models and stable selection**

Zdefiniuj `SyntheticSample` oraz funkcje:

```python
select_evenly_spaced(items, count)
build_validation_samples(gilded_references, wrong_deck_sources, seed=6042026)
render_sample(sample)
```

`sample_id` ma wynikać wyłącznie z deck/card/category/orientation/seed, bez losowych UUID.

- [ ] **Step 4: Implement fixed transform categories**

Dodaj dokładnie:
`upright_clean`, `reversed_clean`, `perspective`, `blur`, `exposure`,
`extra_margin`, `yellow_combined`.

Każdy sample zapisuje komplet parametrów transformacji w manifeście.

- [ ] **Step 5: Test deterministic dataset**

Expected: 168 known samples, 24 wrong-deck samples, identyczny manifest dla tego samego seed.

### Task 2: Runner, wrong-deck rejection i metryki

**Files:**
- Create: `tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py`
- Modify: `app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py`

- [ ] **Step 1: Write failing runner tests**

Testy mają wymagać:

- identycznego sample setu dla ORB i AKAZE,
- jednej macierzowej pozycji per method/sample,
- offline-only threshold w raporcie,
- wrong-deck false-accept rate,
- mean/p50/p95 runtime.

- [ ] **Step 2: Run tests and verify RED**

Expected: brak runnera lub wymaganych pól.

- [ ] **Step 3: Implement benchmark execution**

Runner ładuje pełny Gilded reference deck i wywołuje istniejące
`run_identification_method` wyłącznie dla:

```python
VALIDATION_METHODS = ["orb_bfmatcher_ratio_test", "akaze_bfmatcher"]
```

Wykonaj warm-up przed pomiarem. Zapisz runtime pojedynczego cropu jako local proxy.

- [ ] **Step 4: Implement offline-only rejection**

Dodaj jawny argument CLI `--offline-accept-score-threshold`, domyślnie zapisany
w raporcie. Nie importuj ani nie zapisuj konfiguracji runtime.

Known sample jest zaakceptowany, gdy top-1 score spełnia próg. Wrong-deck
false accept oznacza wrong-deck sample zaakceptowany przez próg.

- [ ] **Step 5: Implement granular aggregation**

Raportuj:

```text
method
method + category
method + category + orientation
```

Każda grupa zawiera count, top1, top3, false-accept rate gdzie dotyczy,
mean gap oraz mean/p50/p95 runtime.

- [ ] **Step 6: Test runner metrics**

Expected: wszystkie testy runnera PASS i brak zależności od runtime config.

### Task 3: Manifest, matrix, raporty i debug sheety

**Files:**
- Modify: `tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py`
- Modify: `app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py`

- [ ] **Step 1: Write failing artifact tests**

Testy wymagają `manifest.json`, `matrix.csv`, `report.json`, `report.md` oraz
co najmniej jednego debug sheetu dla każdej kategorii audytowej:
upright, reversed, `yellow_combined`, wrong-deck.

- [ ] **Step 2: Implement manifest and matrix writers**

`manifest.json` zapisuje seed, konfigurację datasetu i pełne metadane próbek.

`matrix.csv` zawiera co najmniej:

```text
method,sample_id,source_deck,source_card_id,is_known,category,orientation,
predicted_card_id,top1_correct,top3_contains_expected,confidence_score,
confidence_gap,offline_accepted,false_accept,runtime_ms
```

- [ ] **Step 3: Implement report writers**

`report.md` musi jawnie zawierać:

```text
Runtime measurements are a local proxy, not a direct HP EliteBook 830 G6 measurement.
Offline acceptance threshold is validation-only and is not approved for runtime.
```

- [ ] **Step 4: Implement representative debug sheets**

Zapisz ograniczoną liczbę paneli pokazujących obraz próbki, expected/unknown,
prediction, score, gap, category i orientation. Nie zapisuj pełnego datasetu.

- [ ] **Step 5: Run artifact tests**

Expected: komplet artefaktów i brak wygenerowanych pełnych sample images.

### Task 4: Real benchmark i analiza

**Files:**
- Output only: `logs/offline_replay/stage6_validation_benchmark/*`

- [ ] **Step 1: Run the real validation benchmark**

Run:

```powershell
python tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py `
  --gilded-reference-dir biblioteka_talii/gilded/produkcja/wzorce_cv `
  --gilded-deck-profile biblioteka_talii/gilded/deck_profile.json `
  --wrong-deck-dir biblioteka_talii/magic/produkcja/wzorce_cv `
  --wrong-deck-dir biblioteka_talii/marchetti/produkcja/wzorce_cv `
  --output logs/offline_replay/stage6_validation_benchmark `
  --seed 6042026
```

- [ ] **Step 2: Verify artifact counts and manifest reproducibility**

Uruchom benchmark drugi raz do katalogu tymczasowego i porównaj manifesty.
Oczekiwane: identyczne sample metadata; runtime i wyniki mogą różnić się tylko
w polach czasowych.

- [ ] **Step 3: Analyze ORB versus AKAZE**

Zapisz decyzję wyłącznie dla offline validation. Nie zapisuj zgody na runtime.

### Task 5: Dokumentacja i końcowa weryfikacja

**Files:**
- Create: `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001/STATE.md`
- Create: `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001/CHANGELOG.md`
- Create: `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001/TEST_REPORT.md`
- Modify: `.ai/TASKS_INDEX.md`
- Modify: `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

- [ ] **Step 1: Run focused tests and compile**

Run commands listed in task `Tests Required`. Expected: PASS.

- [ ] **Step 2: Run full backend suite**

Run:
`python -m unittest discover -s app_cv/tests -v`

Expected: PASS.

- [ ] **Step 3: Verify forbidden scope**

Run:
`git status --short`

Expected: no modifications under `app_cv/tarotvision/`, `app_cv/main.py` or `app_ar/`.

- [ ] **Step 4: Update task documentation**

Record dataset counts, ORB/AKAZE metrics, wrong-deck false accepts, runtime
proxy limitation, tests and required next action.

- [ ] **Step 5: Commit and push**

```powershell
git add tools/cv_detection_lab/stage6_synthetic_dataset.py `
  tools/cv_detection_lab/stage6_synthetic_validation_benchmark.py `
  app_cv/tests/test_cv_detection_lab_stage6_synthetic_validation.py `
  .ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001 `
  .ai/TASKS_INDEX.md `
  docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md
git commit -m "feat: dodaj syntetyczny benchmark walidacyjny stage6"
git push
```

## Plan Self-Review

- Spec coverage: wszystkie wymagania specyfikacji i uwagi Supervisora mają odpowiadający task.
- Placeholder scan: brak placeholderów i nieokreślonych kroków implementacyjnych.
- Scope: dwa nowe moduły offline lab, jeden plik testowy i dokumentacja.
- Runtime safety: brak zmian runtime, threshold wyłącznie offline-only, runtime jawnie local proxy.
