# Stage 6 Real-Camera Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zbudować offline tooling i procedurę operatorską dla audytowalnego Stage 6 real-camera fixture opartego o wiele niezmiennych sesji capture i jeden manifest agregujący.

**Architecture:** Moduł kontraktu danych ładuje manifest i ground truth oraz wylicza stabilne sample IDs. Osobny preflight waliduje strukturę, wymagane kategorie i niezmienność wskazanych sesji. Generator manual review pack działa wyłącznie na zwalidowanym agregacie i nie modyfikuje sesji capture.

**Tech Stack:** Python 3, standard library, OpenCV wyłącznie do generowania debug sheetów, `unittest`, istniejące pliki live fixture capture jako read-only input.

---

## File Structure

- Create `tools/cv_detection_lab/stage6_real_camera_fixture.py`: kontrakt manifestu/ground truth, stable sample ID, loadery i fingerprint sesji.
- Create `tools/cv_detection_lab/stage6_real_camera_preflight.py`: offline walidacja agregatu.
- Create `tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py`: generowanie paczki review.
- Create `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py`: TDD dla kontraktu, preflightu i packa.
- Create `docs/operator/stage6_real_camera_fixture_capture.md`: instrukcja operatorska.
- Create task reports after implementation and capture.

## Task 1: Kontrakt agregującego manifestu i ground truth

**Files:**
- Create: `tools/cv_detection_lab/stage6_real_camera_fixture.py`
- Create: `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py`

- [ ] **Step 1: Write failing tests for stable sample IDs**

Testy definiują API:

```python
stable_sample_id(session_id, scenario, category)
load_aggregate(manifest_path, ground_truth_path)
```

Wymagaj identycznego ID dla identycznych danych oraz innego ID po zmianie
któregokolwiek składnika.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v
```

Expected: brak modułu `stage6_real_camera_fixture`.

- [ ] **Step 3: Implement manifest and ground-truth models**

Modele muszą przechowywać wszystkie pola ze specyfikacji. Loader nie może
zapisywać ani poprawiać wejściowych JSON-ów.

- [ ] **Step 4: Implement session fingerprint**

Dodaj deterministyczny fingerprint listy plików sesji oparty o względną
ścieżkę, rozmiar i SHA-256 zawartości. Fingerprint służy wyłącznie do wykrycia
modyfikacji podczas działania narzędzia.

- [ ] **Step 5: Verify GREEN**

Expected: testy kontraktu i fingerprintu PASS.

## Task 2: Offline preflight agregatu

**Files:**
- Create: `tools/cv_detection_lab/stage6_real_camera_preflight.py`
- Modify: `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py`

- [ ] **Step 1: Write failing tests for blocking conditions**

Dodaj osobne testy wymagające `PROVISIONAL_BLOCKED` dla:

- duplicate `sample_id`,
- więcej niż jedna próbka wskazująca tę samą sesję,
- brakująca sesja lub wymagany plik,
- manifest/ground-truth mismatch,
- wrong-deck bez `expected_behavior: reject`,
- reversed bez `expected_orientation: reversed`,
- brak `manual_confirmed`,
- brak wymaganej kategorii lub minimalnej liczby próbek.

- [ ] **Step 2: Write immutability test**

Test uruchamia preflight i porównuje fingerprint sesji przed/po. Wymagaj
identyczności oraz braku jakichkolwiek plików utworzonych wewnątrz sesji.

- [ ] **Step 3: Run tests and verify RED**

Expected: brak preflightu lub brak wymaganych błędów.

- [ ] **Step 4: Implement preflight**

Preflight zwraca:

```text
PASS
WARNING
PROVISIONAL_BLOCKED
```

oraz listę stabilnych kodów błędów i ostrzeżeń. Preflight może zapisywać
raporty wyłącznie do wskazanego output dir poza sesjami capture.

- [ ] **Step 5: Add CLI and report writers**

CLI:

```powershell
python tools/cv_detection_lab/stage6_real_camera_preflight.py `
  --manifest logs/live_fixtures/stage6_real_camera_validation/manifest.json `
  --ground-truth logs/live_fixtures/stage6_real_camera_validation/ground_truth.json `
  --output logs/offline_replay/stage6_real_camera_validation
```

- [ ] **Step 6: Verify GREEN**

Expected: poprawny minimalny agregat daje `PASS`; każdy przypadek blokujący
zwraca właściwy kod.

## Task 3: Generator manual review pack

**Files:**
- Create: `tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py`
- Modify: `app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py`

- [ ] **Step 1: Write failing pack tests**

Testy wymagają:

- odmowy generowania packa, gdy preflight nie jest `PASS`,
- jednej planszy per `sample_id`,
- `README_FOR_SUPERVISOR.md`,
- kopii manifestu, ground truth i preflight report,
- indeksu kategorii,
- indeksu similarity groups,
- braku zmian wewnątrz sesji.

- [ ] **Step 2: Run tests and verify RED**

Expected: brak generatora packa.

- [ ] **Step 3: Implement pack generator**

Generator czyta `analysis_frame_<count>.png`, `payload.json`, `metrics.json`
i ground truth. Tworzy planszę z obrazem oraz expected deck/card/orientation/
behavior, category, quality expectation i similarity group.

- [ ] **Step 4: Implement CLI**

```powershell
python tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py `
  --manifest logs/live_fixtures/stage6_real_camera_validation/manifest.json `
  --ground-truth logs/live_fixtures/stage6_real_camera_validation/ground_truth.json `
  --preflight logs/offline_replay/stage6_real_camera_validation/preflight_report.json `
  --output logs/offline_replay/stage6_real_camera_validation/manual_review_pack
```

- [ ] **Step 5: Verify GREEN**

Expected: kompletny pack i niezmienione fingerprinty sesji.

## Task 4: Dokumentacja operatorska i szablony agregatu

**Files:**
- Create: `docs/operator/stage6_real_camera_fixture_capture.md`
- Output locally: `logs/live_fixtures/stage6_real_camera_validation/manifest.json`
- Output locally: `logs/live_fixtures/stage6_real_camera_validation/ground_truth.json`
- Output locally: `logs/live_fixtures/stage6_real_camera_validation/README_FOR_SUPERVISOR.md`

- [ ] **Step 1: Document capture procedure**

Instrukcja musi zawierać:

- naming session IDs,
- ustawienie istniejących env flags live capture,
- przygotowanie każdej kategorii,
- wizualne potwierdzenie sesji,
- zasadę read-only po dodaniu do manifestu,
- procedurę zastąpienia błędnej sesji nową,
- sposób ręcznego potwierdzenia ground truth.

- [ ] **Step 2: Add aggregate templates**

Utwórz lokalne szablony manifestu i ground truth zgodne z kontraktem. Nie
oznaczaj brakujących 28 sesji jako gotowych ani `manual_confirmed`.

- [ ] **Step 3: Verify templates with preflight**

Oczekiwany status przed fizycznym capture: `PROVISIONAL_BLOCKED` z jasną listą
brakujących sesji/próbek. To jest poprawny wynik etapu tooling.

## Task 5: Operator-assisted capture and manual confirmation

**Files:**
- Local ignored data under: `logs/live_fixtures/stage6_real_*`
- Modify local aggregate: `logs/live_fixtures/stage6_real_camera_validation/manifest.json`
- Modify local aggregate: `logs/live_fixtures/stage6_real_camera_validation/ground_truth.json`

- [ ] **Step 1: Capture 6 Gilded upright sessions**

Każda sesja ma unikalny ID i jedną próbkę agregatu.

- [ ] **Step 2: Capture the same 6 cards reversed**

Ground truth jawnie używa `expected_orientation: reversed`.

- [ ] **Step 3: Capture 4 Magic and 4 Marchetti wrong-deck sessions**

Ground truth używa `expected_behavior: reject`, `expected_card_id: null`,
`expected_orientation: not_applicable`.

- [ ] **Step 4: Capture 4 difficult real YELLOW samples**

Stage 5 output musi potwierdzić status `YELLOW`; próbki niespełniające warunku
nie trafiają do tej kategorii.

- [ ] **Step 5: Capture two visually similar Gilded groups**

Każda grupa ma co najmniej dwie różne karty i wspólny `similarity_group`.

- [ ] **Step 6: Manually confirm all ground truth labels**

Każda pozycja otrzymuje `label_status: manual_confirmed`.

- [ ] **Step 7: Run preflight and generate manual review pack**

Expected: `PASS` oraz kompletna paczka dla minimum 28 próbek.

## Task 6: Verification, reports and handoff

**Files:**
- Create: `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001/STATE.md`
- Create: `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001/CHANGELOG.md`
- Create: `.ai/tasks/TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001/TEST_REPORT.md`
- Modify: `.ai/TASKS_INDEX.md`
- Modify: `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

- [ ] **Step 1: Run focused tests**

```powershell
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v
```

- [ ] **Step 2: Run compile and full backend suite**

```powershell
python -B -m py_compile tools/cv_detection_lab/stage6_real_camera_fixture.py tools/cv_detection_lab/stage6_real_camera_preflight.py tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py
python -m unittest discover -s app_cv/tests -v
```

- [ ] **Step 3: Verify forbidden scope**

`git diff --name-only` nie może zawierać `app_cv/main.py`,
`app_cv/tarotvision/*` ani `app_ar/*`.

- [ ] **Step 4: Record status accurately**

Jeśli tooling jest gotowy, ale 28 realnych sesji nie zostało jeszcze zebranych,
status taska musi pozostać `PROVISIONAL_BLOCKED` i wskazywać działania
operatorskie. Nie wolno raportować `PASS` bez realnego capture.

- [ ] **Step 5: Commit and push**

Commit tooling i dokumentację dopiero po testach. Dane w ignorowanych
`logs/` pozostają lokalne i są przekazywane przez manual review pack.

## Plan Self-Review

- Spec coverage: plan obejmuje manifest, ground truth, preflight, manual review pack i capture minimum 28 próbek.
- Collision safety: preflight blokuje duplicate `sample_id` oraz więcej niż jedną próbkę na sesję.
- Scope safety: brak zmian mechanizmu capture i runtime.
- Status safety: tooling bez fizycznego capture pozostaje `PROVISIONAL_BLOCKED`.
