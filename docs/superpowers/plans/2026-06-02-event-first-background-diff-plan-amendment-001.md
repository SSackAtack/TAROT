# Event-First Background Diff Plan Amendment 001

## Status

**Required before implementation.**

This amendment supersedes the affected parts of:

`docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md`

It fixes two blocking ambiguities found during ChatGPT Supervisor review of commit `c8d0970`:

1. `roi_hints=[]` must not fall back to global card detection.
2. `empty_reference` validation must compare the current empty frame against the reference, not `analysis_frame` against itself.

---

## 1. ROI semantics must be explicit

Add this section to the main plan before `## Projekt Docelowy` or inside `## Safety Rules for Runtime`.

```markdown
## ROI Semantics

`SnapshotAnalyzer.analyze(frame, roi_hints=...)` must distinguish three states:

1. `roi_hints is None`
   - Event-first ROI filtering is unavailable or intentionally disabled.
   - Global detection may run as fallback mode.
   - Studio/CV Explain should make it clear if the system is operating without full event-first calibration.

2. `roi_hints == []`
   - Event-first mode is active and ChangeDetector found no `added_or_moved` region.
   - Analyzer must not run global card detection.
   - Analyzer should return zero candidate quads / zero cards and diagnostics should show `roi_limited=True`, `roi_count=0`.
   - This is the normal safe result for a stable empty mat.

3. `roi_hints == [...]`
   - Event-first mode is active and ChangeDetector found one or more candidate regions.
   - Analyzer must inspect only these regions.
   - Global card detection must not run outside these ROI regions.
```

This rule is mandatory because the core safety contract is:

```text
empty_reference active + no added_or_moved ROI = no global scan and no new cards
```

---

## 2. Replace SnapshotAnalyzer ROI pseudocode

In Task 3, replace the ROI acquisition pseudocode that currently uses `if roi_hints:` with an explicit `is not None` check.

### Required implementation shape

```python
def analyze(self, frame, roi_hints=None):
    diagnostics = {
        # existing diagnostics...
        "roi_limited": roi_hints is not None,
        "roi_count": len(roi_hints or []),
    }

    if roi_hints is not None:
        quads = []
        detection_debug = {"roi_hints": []}
        for bbox in roi_hints:
            x, y, w, h = _clamp_bbox(bbox, frame_width, frame_height)
            if w <= 0 or h <= 0:
                continue
            crop_frame = frame[y:y + h, x:x + w]
            crop_quads = self.find_quads(crop_frame)
            for crop_quad in crop_quads:
                points = _quad_points(crop_quad).copy()
                points[:, 0] += x
                points[:, 1] += y
                quads.append(points)
            detection_debug["roi_hints"].append({"bbox": [x, y, w, h], "quads": len(crop_quads)})
        diagnostics["detection"] = detection_debug
    elif self.find_quads_with_debug is not None:
        detection_result = self.find_quads_with_debug(frame)
        quads = detection_result.quads
        diagnostics["detection"] = detection_result.debug
    else:
        quads = self.find_quads(frame)
```

The important behavior is:

```python
roi_hints=[]      # no global fallback
roi_hints=None    # global fallback allowed
```

---

## 3. Add required SnapshotAnalyzer test

Add this test to Task 3.

```python
def test_analyze_with_empty_roi_hints_does_not_fallback_to_global_detection(self):
    frame = np.zeros((200, 300, 3), dtype=np.uint8)
    calls = []

    def find_quads(_frame):
        calls.append(_frame.shape)
        return [np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32)]

    analyzer = SnapshotAnalyzer(
        find_quads=find_quads,
        recognize_crop=lambda crop: {"name": "Gilded_01", "confidence": 0.9},
        validate_candidate_crop=None,
    )

    result = analyzer.analyze(frame, roi_hints=[])

    self.assertEqual(calls, [])
    self.assertEqual(result.card_count, 0)
    self.assertTrue(result.diagnostics["roi_limited"])
    self.assertEqual(result.diagnostics["roi_count"], 0)
```

This test protects against accidental reintroduction of global scanning on a stable empty mat.

---

## 4. Runtime Pipeline Integration must preserve the same semantics

Task 4 should pass:

```python
roi_hints = None

if event_first_available:
    roi_hints = [
        region.bbox for region in change_result.regions
        if region.kind == "added_or_moved"
    ]
```

If the list is empty, it must still be passed as `[]`, not converted back to `None`.

Correct:

```python
result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints)
```

Incorrect:

```python
result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints or None)
```

The incorrect version would re-enable global detection when no event-first ROI exists.

---

## 5. Empty reference validation correction

Task 5 currently suggests validating reference quality with:

```python
validation = self.change_detector.detect(
    analysis_frame,
    analysis_frame,
    empty_reference=self.background_model,
)
```

This is logically too weak, because comparing a frame to itself always produces no previous/current difference.

Replace it with reference-based validation.

### Required validation shape

After:

```python
self.background_model.capture_many(self.empty_reference_frames)
```

validate the last empty frame against the newly built reference:

```python
validation_ratio = self.background_model.changed_ratio(analysis_frame, threshold=20)
self.runtime_metrics.add("background_reference_validation_ratio", validation_ratio)

if validation_ratio > 0.01:
    self.runtime_metrics.add("background_reference_validation_warning", 1)
else:
    self.runtime_metrics.add("background_reference_validation_warning", 0)
```

Threshold `0.01` is an initial MVP value and may later move to runtime config/autotune profile.

Optional diagnostic extension:

```python
mask = self.background_model.foreground_mask(analysis_frame, threshold=20)
# Count connected components/regions only if needed for CV Explain.
```

---

## 6. Required test for empty reference validation

Add a test to Task 5 ensuring validation uses the reference, not `analysis_frame` vs `analysis_frame`.

Suggested contract test:

```python
def test_empty_reference_validation_uses_background_changed_ratio(self):
    background_model = MagicMock()
    background_model.active = True
    background_model.changed_ratio.return_value = 0.0

    # Arrange pipeline/autotune recorder so empty reference is finalized.
    # Process enough forced empty snapshots to trigger capture_many().

    background_model.capture_many.assert_called_once()
    background_model.changed_ratio.assert_called()
    runtime_metrics.add.assert_any_call("background_reference_validation_ratio", 0.0)
```

The test must not accept a validation path based only on `change_detector.detect(analysis_frame, analysis_frame, ...)`.

---

## 7. Acceptance criteria additions

Add these acceptance criteria to the main plan:

```markdown
- `roi_hints=None` is the only state where global fallback detection may run.
- `roi_hints=[]` means event-first mode is active and there are no added/moved regions; analyzer must not run global detection.
- Stable empty mat after calibration produces `roi_hints=[]`, `card_count=0`, and no global scan.
- Empty reference validation uses `BackgroundModel.changed_ratio(current_empty_frame)` or equivalent reference-vs-current comparison, not `current_frame` vs itself.
```

---

## 8. Documentation update requirement

When applying this amendment to the main plan, update:

- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`
- optionally `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`

Use `PLAN ONLY`; no code tests are required for this amendment because it is documentation-only.
