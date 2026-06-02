# TEST REPORT: EVENT-FIRST PLAN AMENDMENT 001

## 2026-06-02

### Scope

PLAN ONLY. Zmieniono wyłącznie dokumentację planistyczną.

### Files

- `docs/superpowers/plans/2026-06-02-event-first-background-diff-plan-amendment-001.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`

### Verification

Nie uruchamiano testów kodu, ponieważ poprawka nie zmienia plików produkcyjnych.

Ręcznie zweryfikowano, że errata doprecyzowuje dwa blokujące punkty przed implementacją:

1. `roi_hints=None` oznacza fallback globalny, natomiast `roi_hints=[]` oznacza aktywny event-first bez ROI i zakaz globalnego skanowania.
2. Walidacja `empty_reference` ma używać porównania bieżącej pustej klatki z referencją, np. `BackgroundModel.changed_ratio(current_empty_frame)`, a nie porównania `analysis_frame` z samym sobą.

### Result

PASS for documentation-only amendment.

### Next Required Step

Przed implementacją `Task 1: Stable Empty Reference` Gemini/Codex musi traktować `event-first-background-diff-plan-amendment-001.md` jako obowiązkowy dodatek do głównego planu.
