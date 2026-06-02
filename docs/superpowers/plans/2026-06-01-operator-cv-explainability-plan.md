# Operator CV Explainability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dodac w Studio panel `CV Explain`, ktory pokazuje uporzadkowana przyczyne problemu CV i jeden konkretny nastepny krok operatora.

**Architecture:** Backend generuje maly obiekt `operator.explainability` z istniejacych danych `cards`, `metrics`, `runtime`, `layout`, `operator` i `warnings`. Frontend Studio renderuje ten obiekt pod `CV Health`, z fallbackiem na payload bez explainability.

**Tech Stack:** Python unittest, OpenCV runtime payload, Vite frontend, plain JavaScript DOM rendering, CSS Studio.

---

## Status ogolny

DONE. Implementacja zostala wykonana inline przez Codex na branchu `codex/operator-cv-explainability`.

## File Structure

- Create: `app_cv/tarotvision/operator_explainability.py` — czysty builder diagnostyki bez zaleznosci od kamery.
- Create: `app_cv/tests/test_operator_explainability.py` — testy jednostkowe buildera.
- Modify: `app_cv/main.py` — dolaczenie explainability do `build_operator_snapshot()`.
- Modify: `app_cv/tests/test_status_store.py` — potwierdzenie, ze `operator.explainability` przechodzi przez status store.
- Modify: `app_ar/src/studio/studioConsole.js` — panel `CV Explain` i renderowanie krokow.
- Modify: `app_ar/studio.css` — zwarte style panelu.
- Modify: `app_cv/tests/test_camera_controls_static.py` — statyczna kontrola obecnosci panelu i next action.
- Create: `.ai/tasks/TASK-STUDIO-CV-EXPLAIN-001/{TASK.md,STATE.md,CHANGELOG.md,TEST_REPORT.md}` — dokumentacja taska.
- Modify: `.ai/TASKS_INDEX.md` — wpis taska.

## Task 1: Backend Builder TDD

- [ ] **Step 1: Write failing backend tests**

Add `app_cv/tests/test_operator_explainability.py` with tests for:

```python
from tarotvision.operator_explainability import build_cv_explainability

def test_requires_active_deck():
    result = build_cv_explainability(cards=[], metrics={}, runtime={}, layout={}, operator={"active_decks": []}, warnings=[])
    assert result["severity"] == "error"
    assert result["next_action"] == "Wybierz 1-3 talie w Studio."

def test_no_camera_points_to_camera_check():
    result = build_cv_explainability(cards=[], metrics={}, runtime={}, layout={"state": "no_camera"}, operator={"active_decks": ["gilded"]}, warnings=[])
    assert result["severity"] == "error"
    assert result["next_action"] == "Sprawdz kamere i launcher CV."

def test_settling_snapshot_requests_still_table():
    result = build_cv_explainability(cards=[], metrics={}, runtime={"aruco_calibrated": True, "aruco_markers": 4}, layout={"state": "settling"}, operator={"active_decks": ["gilded"]}, warnings=[])
    assert result["severity"] == "warn"
    assert result["next_action"] == "Zostaw mate nieruchomo przez kilka sekund."

def test_detected_cards_are_ok():
    result = build_cv_explainability(cards=[{"id": "card-1"}], metrics={}, runtime={"aruco_calibrated": True, "aruco_markers": 4}, layout={"state": "holding_last_good"}, operator={"active_decks": ["gilded"]}, warnings=[])
    assert result["severity"] == "ok"
    assert result["next_action"] == "Mozna prowadzic sesje."
```

- [ ] **Step 2: Run test to verify RED**

Run: `python -m unittest app_cv.tests.test_operator_explainability -v`

Expected: FAIL with `ModuleNotFoundError` or missing `build_cv_explainability`.

- [ ] **Step 3: Implement minimal builder**

Create `app_cv/tarotvision/operator_explainability.py` with `build_cv_explainability(cards, metrics, runtime, layout, operator, warnings)`.

- [ ] **Step 4: Run backend builder test to verify GREEN**

Run: `python -m unittest app_cv.tests.test_operator_explainability -v`

Expected: PASS.

## Task 2: Payload Integration TDD

- [ ] **Step 1: Write failing status/payload tests**

Extend `app_cv/tests/test_status_store.py` with an assertion that `operator.explainability` is preserved after `update_cv_state`.

- [ ] **Step 2: Run targeted tests to verify RED/GREEN boundary**

Run: `python -m unittest app_cv.tests.test_status_store app_cv.tests.test_operator_explainability -v`

Expected before integration may pass for status store alone, then backend integration must be checked by static/import test.

- [ ] **Step 3: Wire builder into `main.py`**

Import `build_cv_explainability` and add an `explainability` key inside `build_operator_snapshot()`.

- [ ] **Step 4: Run targeted backend tests**

Run: `python -m unittest app_cv.tests.test_status_store app_cv.tests.test_operator_explainability app_cv.tests.test_main_static_audit -v`

Expected: PASS.

## Task 3: Studio Panel TDD

- [ ] **Step 1: Write failing static frontend test**

Extend `app_cv/tests/test_camera_controls_static.py` to assert `studioConsole.js` contains `CV Explain`, `studio-cv-explain-next`, `renderCvExplainability`, and `operator.explainability`.

- [ ] **Step 2: Run static test to verify RED**

Run: `python -m unittest app_cv.tests.test_camera_controls_static -v`

Expected: FAIL before frontend implementation.

- [ ] **Step 3: Implement panel DOM and renderer**

Modify `app_ar/src/studio/studioConsole.js`:

- Add `renderCvExplainability(data)` helper.
- Add panel markup below `CV Health`.
- Call renderer in `updateStudioConsole(data)`.
- Use fallback if `data.operator?.explainability` is missing.

- [ ] **Step 4: Add CSS styles**

Modify `app_ar/studio.css` for `.studio-cv-explain-*` classes.

- [ ] **Step 5: Run static frontend test**

Run: `python -m unittest app_cv.tests.test_camera_controls_static -v`

Expected: PASS.

## Task 4: Documentation, Verification, Commit

- [ ] **Step 1: Create task docs**

Create `.ai/tasks/TASK-STUDIO-CV-EXPLAIN-001/` with `TASK.md`, `STATE.md`, `CHANGELOG.md`, `TEST_REPORT.md`.

- [ ] **Step 2: Update task index**

Add `TASK-STUDIO-CV-EXPLAIN-001` to `.ai/TASKS_INDEX.md` as `DONE` on branch `codex/operator-cv-explainability`.

- [ ] **Step 3: Run full verification**

Run:

```text
python -m unittest discover -s app_cv\tests -v
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: backend PASS, frontend build PASS.

- [ ] **Step 4: Commit and push**

Commit message:

```text
feat: dodaj cv explainability w studio
```

Push branch `codex/operator-cv-explainability`.

## Session Status (2026-06-01)

Plan utworzony po akceptacji wariantu B przez Michala w visual companion. Implementacja zakonczona: backend publikuje `operator.explainability`, Studio renderuje panel `CV Explain`, testy backendowe i build frontendu przechodza.

## Kolejne kroki

1. Review zmian na branchu `codex/operator-cv-explainability`.
2. Lokalny smoke test Studio z uruchomionym backendiem CV.
3. Po akceptacji merge do `master`.
