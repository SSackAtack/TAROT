# State-First Diff MVP Smoke

Branch: `codex/project-mvp-recovery-audit-2026-06-05`
HEAD: `a193283`
Pipeline mode: `state_first_diff`
Physical deck: Gilded
Active deck: `gilded`

Status: `PHYSICAL_SMOKE_NOT_RUN`
Decision: `KEEP_SNAPSHOT_FIRST_DEFAULT_FOR_MVP`

Verification before physical smoke:

- Backend full tests: PASS, `python -m unittest discover -s app_cv\tests -v`, 463 tests.
- Frontend build: PASS, `npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build`.
- Physical smoke: NOT_RUN.

## Preconditions

- Run backend with `TAROTVISION_PIPELINE=state_first_diff`.
- Keep `app_ar/public/active_decks.json` unstaged; local Operator config may stay on `gilded`.
- Use the Studio section `Sesja state-first`.
- Do not run autotune during this smoke.

## Offline Evidence Before Physical Smoke

Command:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python tools\cv_detection_lab\runtime_state_first_smoke.py
```

Result after runtime-effective ROI gating: `PASS`.

- `empty->empty`: PASS, actual 0 / expected 0
- `empty->one_card`: PASS, actual 1 / expected 1
- `empty->three_cards`: PASS at analysis ROI level, raw detector regions 2 / expected raw 3
- `one_card->three_cards`: PASS at analysis ROI level, raw detector regions 4 / expected raw 2
- `one_card->empty`: PASS, actual 1 / expected 1
- `three_cards->empty`: PASS at analysis ROI level, raw detector regions 2 / expected raw 3

Interpretation: state-first should gate on runtime-effective analysis ROI and TableState updates, not raw contour region count. Raw detector count remains diagnostic.

## Physical Smoke Checklist

### 1. Start Session

- session state:
- empty reference locked:
- backend layout.session.active:
- backend layout.session.ready_for_diff:
- notes:

### 2. EMPTY -> EMPTY

- ROI count:
- false positives:
- result: PASS / FAIL
- notes:

### 3. EMPTY -> ONE_CARD

- change kind:
- detected ROI:
- accepted card:
- TableState:
- result: PASS / FAIL
- notes:

### 4. ONE_CARD -> THREE_CARDS

- added ROI count:
- existing card preserved:
- new cards accepted:
- result: PASS / FAIL
- notes:

### 5. THREE_CARDS -> ONE_CARD

- removed ROI count:
- removed card:
- remaining cards preserved:
- result: PASS / FAIL
- notes:

### 6. RESYNC

- full snapshot fallback:
- result: PASS / FAIL
- notes:

## Rollout Decision

Allowed outcomes:

- `READY_TO_MAKE_STATE_FIRST_DEFAULT`
- `STATE_FIRST_BRANCH_FIX_REQUIRED`
- `KEEP_SNAPSHOT_FIRST_DEFAULT_FOR_MVP`

Current decision before physical smoke: `KEEP_SNAPSHOT_FIRST_DEFAULT_FOR_MVP`.

Reason: offline smoke now passes at runtime-effective ROI level, but physical Gilded smoke has not been run. Keep `snapshot_first` as default until Operator camera validation passes.

## Runtime Telemetry

`StateFirstDiffPipeline` publishes `layout.session`:

- `active`
- `empty_reference_locked`
- `empty_reference`
- `previous_snapshot`
- `current_snapshot`
- `ready_for_diff`

Studio uses these fields in the `Sesja state-first` panel instead of inferring locked empty reference only from `layout.state`.
