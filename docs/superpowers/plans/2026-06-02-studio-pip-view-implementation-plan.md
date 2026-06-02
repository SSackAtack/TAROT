# Studio PiP View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dodac w Studio lokalne tryby widoku `Stol`, `Kamera` i `PiP`, aby operator mogl widziec wirtualny stol, live camera preview albo oba naraz.

**Architecture:** Funkcja jest frontend-only. `studioConsole.js` utrzymuje lokalny preview mode i przelacza klasy/dataset na istniejacym `.studio-preview-overlay`; `studio.css` steruje widocznoscia i polozeniem kamery. Nie zmieniamy backendowego protokolu scen.

**Tech Stack:** Vite, DOM, CSS, Python unittest static audit.

---

## File Structure

- Modify: `app_ar/src/studio/studioConsole.js`
  Dodaje segment `Widok` i funkcje przelaczania preview.
- Modify: `app_ar/studio.css`
  Dodaje style `table`, `camera`, `pip`.
- Modify: `app_cv/tests/test_camera_controls_static.py`
  Dodaje statyczny kontrakt UI.

## Task 1: Studio Preview Modes

- [ ] **Step 1: Write static UI test**

Dodaj test, ktory oczekuje `setStudioPreviewMode`, `data-preview-mode="table"`, `data-preview-mode="camera"` i `data-preview-mode="pip"`.

- [ ] **Step 2: Run static test**

Run:

```bat
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest app_cv.tests.test_camera_controls_static -v"
```

Expected: FAIL przed implementacja.

- [ ] **Step 3: Implement Studio controls**

W `studioConsole.js` dodaj stan preview mode, przyciski `Stol`, `Kamera`, `PiP`, `setStudioPreviewMode(mode)` i klik handlers.

- [ ] **Step 4: Implement CSS modes**

W `studio.css` ukryj duzy preview dla `table`, pokaz duzy preview dla `camera`, pokaz PiP dla `pip`.

- [ ] **Step 5: Verify**

Run:

```bat
cmd /c "set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv&& python -m unittest app_cv.tests.test_camera_controls_static -v"
cmd /c "npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build"
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bat
git add app_ar/src/studio/studioConsole.js app_ar/studio.css app_cv/tests/test_camera_controls_static.py docs/superpowers/specs/2026-06-02-studio-pip-view-design.md docs/superpowers/plans/2026-06-02-studio-pip-view-implementation-plan.md
git commit -m "feat: dodaj tryby widoku stol kamera pip w studio"
```
