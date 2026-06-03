# NEXT ACTION AFTER ROI DIAGNOSTICS PASSTHROUGH

## Status

**Task 7 remains RED / IN_PROGRESS.**

The latest diagnostic fix was committed and pushed:

`991ba875187103396554354ceb628dd95a2f96dc` — `fix: przepusc diagnostyke roi do pipeline metrics`

This commit does not change card detection, recognition, ORB thresholds, ArUco calibration, empty reference logic, or Studio UI. It only exposes ROI diagnostics already produced by `SnapshotAnalyzer` through the WebSocket metrics payload published by `SnapshotFirstPipeline`.

## Why this handoff exists

Codex ran out of tokens after the diagnostic passthrough fix. The next model must continue from the exact current state without restarting the whole architectural discussion.

## Current known project state

Previous live smoke results:

1. `Pusta mata` is now correct under the new event-first contract:
   - `empty_reference_status=PASS`
   - `background_reference_active=true`
   - `background_reference_validation_warning=0`
   - false positives from the legacy detector are only diagnostics/warnings
   - false positives do not enter Studio layout

2. `1 karta` passed functionally:
   - exactly one card was published
   - no layout contamination from empty false positives
   - some `global_shift` noise was observed but not treated as the current blocker

3. `3 karty` is RED:
   - event-first saw multiple regions of change
   - final layout published only one card
   - this points downstream of change detection: ROI processing, crop validation, ORB recognition, candidate rejection, or final layout composition

Important observed metrics from the RED 3-card smoke:

```text
change_region_count≈3.5
change_added_count≈3.5
change_mask_ratio≈0.311
snapshot_quads_found≈10.111
snapshot_recognition_attempts≈6.222
snapshot_recognition_rejections≈4.778
snapshot_candidate_validation_rejections≈3.889
snapshot_detection_quads_final≈0.444
cards_len=1
```

## Latest diagnostic fix

`991ba87` added passthrough from `SnapshotAnalyzer.diagnostics` to the published pipeline metrics:

```text
roi_count
roi_diagnostics
roi_with_quads_count
roi_with_accepted_card_count
accepted_cards_before_dedup
accepted_cards_after_dedup
```

The regression test confirms that fields from `SnapshotAnalyzer.diagnostics` reach:

```python
status_store.update_cv_state(..., metrics=...)
```

Reported verification:

```text
py_compile snapshot_first.py: PASS
ROI passthrough contract test: PASS
targeted suite: PASS, 55 tests
```

## Immediate next task for the next model

Continue live diagnostic smoke. Do not implement another fix yet.

### Step 0 — verify repo state

The next model should first verify:

```powershell
git fetch origin
git switch task/cv-event-first-plan-001-clarify-autotune-runtime
git pull --ff-only
git log --oneline -5
```

Expected latest relevant commit:

```text
991ba87 fix: przepusc diagnostyke roi do pipeline metrics
```

### Step 1 — verify backend state

Codex reported that backend was still running on local code with the ROI passthrough fix on ports:

```text
8765 / 8766
```

However, after any backend restart the in-memory `empty_reference` is cleared. Do not assume reference persists.

If backend was restarted or if state is uncertain, rebuild `empty_reference` before testing 3 cards.

### Step 2 — operator setup

Ask Michał to prepare the physical scene:

```text
1. Remove all cards from the mat.
2. Ensure 4 ArUco markers are visible.
3. Confirm with: pusta gotowa
```

Do not proceed to 3-card smoke until the operator confirms the mat is empty and markers are visible.

### Step 3 — rebuild empty reference

Send/trigger:

```json
{"type":"autotune_start","scenario":"empty"}
```

Expected result:

```text
progress empty: 3/3
empty_reference_status=PASS
background_reference_active=true
background_reference_validation_warning=0
cards_len=0
detected=false
marker_ids=[10,11,12,13]
table.calibrated=true
```

If `empty` does not pass, do not continue. Report exact metrics and stop.

### Step 4 — run 3-card scenario

Ask Michał to place 3 physical cards on the ArUco table area.

Then wait for motion gate / snapshot cycle and read the WebSocket payload metrics.

Required fields to capture:

```text
cards_len
detected
change_region_count
change_added_count
change_removed_count
change_mask_ratio
snapshot_quads_found
snapshot_recognition_attempts
snapshot_recognition_rejections
snapshot_candidate_validation_rejections
snapshot_detection_quads_final
roi_count
roi_with_quads_count
roi_with_accepted_card_count
accepted_cards_before_dedup
accepted_cards_after_dedup
roi_diagnostics
```

For every item in `roi_diagnostics`, capture:

```text
roi_index
roi_bbox
roi_area
roi_quads_found
roi_candidates_after_validation
roi_validation_rejections
roi_recognition_attempts
roi_recognition_rejections
roi_accepted_cards
roi_reject_reasons
```

### Step 5 — interpret the result

Use this decision table:

#### Case A — ROI problem

```text
roi_count >= 3
roi_with_quads_count < 3
```

Likely problem: ROI size, ROI crop, ROI merge/split, or find_quads within ROI.

Next fix should target ROI padding/sizing or ROI segmentation, not ORB.

#### Case B — candidate validation problem

```text
roi_with_quads_count >= 3
roi_validation_rejections high
roi_candidates_after_validation low
```

Likely problem: candidate crop validation is too strict for warped/multi-card ROI.

Next fix should target crop validation diagnostics or thresholds.

#### Case C — recognition problem

```text
roi_recognition_attempts high
roi_recognition_rejections high
roi_accepted_cards low
```

Likely problem: ORB recognition on ROI crops, crop quality, deck template matching, orientation, or recognition score/margin.

Next fix should target recognition diagnostics/crop quality, not ChangeDetector.

#### Case D — layout/dedup problem

```text
accepted_cards_before_dedup >= 3
accepted_cards_after_dedup < 3
```

Likely problem: deduplication or collapse of recognized cards.

#### Case E — post-analyzer publication problem

```text
accepted_cards_after_dedup >= 3
cards_len < 3
```

Likely problem: `SnapshotFirstPipeline` or layout publication after `SnapshotAnalyzer`.

## Do not do

Do not change these during the diagnostic smoke:

```text
ChangeDetector thresholds
ArUco calibration logic
empty reference logic
ORB thresholds
candidate validation thresholds
Studio UI
frontend
legacy empty-mat detector tuning
```

The next step is observation with the new diagnostics, not another speculative fix.

## Required report after live diagnostic smoke

After running the short live cycle, update:

```text
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md
.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md
```

Report format:

```markdown
## 2026-06-03 Event-first 3-card ROI diagnostic smoke

### Input state
- backend commit:
- table.calibrated:
- marker_ids:
- empty_reference_status:
- background_reference_active:

### 3-card result
- cards_len:
- detected:
- change_region_count:
- change_added_count:
- snapshot_quads_found:
- snapshot_recognition_attempts:
- snapshot_candidate_validation_rejections:
- snapshot_recognition_rejections:
- roi_count:
- roi_with_quads_count:
- roi_with_accepted_card_count:
- accepted_cards_before_dedup:
- accepted_cards_after_dedup:

### ROI diagnostics
Paste/summarize each ROI.

### Interpretation
Choose one:
- ROI sizing/merge issue
- crop validation issue
- recognition issue
- dedup/layout issue
- publication issue
- inconclusive

### Required next action
One small fix-task only, based on the diagnostic result.
```

## Supervisor recommendation

The next model should not repeat the whole smoke from zero except for the minimum required empty reference rebuild after backend restart. The current target is narrow:

```text
Pusta mata 3/3 -> 3 cards -> read roi_diagnostics -> choose one small fix-task.
```
