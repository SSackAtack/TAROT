# TarotVision State-First CV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace repeated whole-frame identity matching with a state-first pipeline: identify new cards once, remove confirmed cards from the available deck pool, track locked cards cheaply, and reverify only on suspicion or schedule.

**Architecture:** Keep the current monolithic `app_cv/main.py` running while adding focused modules around it. The first phase is deliberately conservative: introduce table state, motion triggers, ROI filtering, contour tracking, and audit policy as testable helpers before replacing the current ORB loop. The target runtime behavior is `empty_scan -> candidate identification -> locked contour tracking -> scheduled/suspicious reverify`.

**Tech Stack:** Python stdlib `unittest`, OpenCV, NumPy, existing WebSocket JSON payload, existing Vite/Three.js frontend.

---

## Evidence Behind This Plan

Runtime logs from `logs/cv_metrics.jsonl` showed:

- original repeated matching: about `2.6 FPS`, about `357 ms` in `matching_ms`,
- scheduler optimization in stable state: about `10 FPS`, about `75-85 ms` in `matching_ms`,
- over-aggressive boost scan: back to about `2-3 FPS`, because `boost_scan` stayed active too long.

Conclusion: the bottleneck is not the camera, preprocessing, or ORB feature extraction. The bottleneck is repeated identity matching against too many templates. The next system should identify only when needed and track cheaply most of the time.

## File Structure

- Create: `app_cv/tarotvision/table_state.py`
  Durable table model, available deck pool, locked/suspicious/lost states, and operator corrections.
- Create: `app_cv/tests/test_table_state.py`
  Unit tests for deck-pool behavior and state transitions.
- Create: `app_cv/tarotvision/motion.py`
  Motion/change detection used only as a trigger for scanning, not as proof of a new card.
- Create: `app_cv/tests/test_motion.py`
  Synthetic frame tests for motion and settled-frame behavior.
- Create: `app_cv/tarotvision/roi_map.py`
  Occupied/free region helpers to avoid scanning areas already containing locked cards.
- Create: `app_cv/tests/test_roi_map.py`
  Synthetic geometry tests for filtering candidates against occupied boxes.
- Create: `app_cv/tarotvision/contour_tracking.py`
  Cheap locked-card tracking by bbox/quad similarity.
- Create: `app_cv/tests/test_contour_tracking.py`
  Tests for assigning detected contours to known tracked cards.
- Create: `app_cv/tarotvision/audit_policy.py`
  Scheduled and suspicion-based reverify decisions.
- Create: `app_cv/tests/test_audit_policy.py`
  Tests for periodic and suspicious reverify triggers.
- Modify: `app_cv/main.py`
  Integrate these helpers gradually behind the current working loop.
- Modify: `README.md`
  Keep current architecture notes and log interpretation aligned.

---

### Task 1: Add Durable Table State and Deck Pool

**Files:**
- Create: `app_cv/tarotvision/table_state.py`
- Create: `app_cv/tests/test_table_state.py`

- [x] **Step 1: Write failing table state tests**

Create `app_cv/tests/test_table_state.py`:

```python
import unittest

from tarotvision.table_state import TableState


class TableStateTest(unittest.TestCase):
    def test_available_cards_excludes_locked_cards(self):
        state = TableState(["00_fool", "01_magician", "02_priestess"])

        state.upsert_locked(
            card_id="00_fool",
            x=1.0,
            y=2.0,
            angle=0.1,
            confidence=0.92,
            frame_index=10,
        )

        self.assertEqual(state.available_card_ids, ["01_magician", "02_priestess"])

    def test_removed_card_returns_to_available_pool(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)

        state.remove_card("00_fool")

        self.assertEqual(state.available_card_ids, ["00_fool", "01_magician"])

    def test_needs_reverify_does_not_return_card_to_pool(self):
        state = TableState(["00_fool", "01_magician"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)

        state.mark_needs_reverify("00_fool", "contour_drift")

        self.assertEqual(state.cards["00_fool"].phase, "needs_reverify")
        self.assertEqual(state.available_card_ids, ["01_magician"])

    def test_operator_correction_swaps_card_identity(self):
        state = TableState(["00_fool", "01_magician", "02_priestess"])
        state.upsert_locked("00_fool", 1.0, 2.0, 0.1, 0.92, 10)

        state.correct_card_id("00_fool", "02_priestess")

        self.assertNotIn("00_fool", state.cards)
        self.assertIn("02_priestess", state.cards)
        self.assertEqual(state.available_card_ids, ["00_fool", "01_magician"])


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and verify failure**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_table_state.py -v
```

Expected: import failure because `tarotvision.table_state` does not exist.

- [x] **Step 3: Implement table state**

Create `app_cv/tarotvision/table_state.py`:

```python
from dataclasses import dataclass


PHASE_LOCKED = "locked_tracking"
PHASE_NEEDS_REVERIFY = "needs_reverify"


@dataclass
class TrackedCard:
    card_id: str
    phase: str
    x: float
    y: float
    angle: float
    confidence: float
    last_seen_frame: int
    reverify_reason: str | None = None


class TableState:
    def __init__(self, all_card_ids):
        self.all_card_ids = list(all_card_ids)
        self.cards = {}

    @property
    def available_card_ids(self):
        locked_ids = set(self.cards.keys())
        return [card_id for card_id in self.all_card_ids if card_id not in locked_ids]

    def upsert_locked(self, card_id, x, y, angle, confidence, frame_index):
        if card_id not in self.all_card_ids:
            raise ValueError(f"Unknown card id: {card_id}")
        self.cards[card_id] = TrackedCard(
            card_id=card_id,
            phase=PHASE_LOCKED,
            x=float(x),
            y=float(y),
            angle=float(angle),
            confidence=float(confidence),
            last_seen_frame=int(frame_index),
        )

    def mark_needs_reverify(self, card_id, reason):
        if card_id not in self.cards:
            return
        card = self.cards[card_id]
        card.phase = PHASE_NEEDS_REVERIFY
        card.reverify_reason = reason

    def remove_card(self, card_id):
        self.cards.pop(card_id, None)

    def correct_card_id(self, old_card_id, new_card_id):
        if new_card_id not in self.all_card_ids:
            raise ValueError(f"Unknown card id: {new_card_id}")
        if old_card_id not in self.cards:
            return
        old = self.cards.pop(old_card_id)
        self.cards[new_card_id] = TrackedCard(
            card_id=new_card_id,
            phase=old.phase,
            x=old.x,
            y=old.y,
            angle=old.angle,
            confidence=old.confidence,
            last_seen_frame=old.last_seen_frame,
            reverify_reason=old.reverify_reason,
        )
```

- [x] **Step 4: Verify table state tests pass**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_table_state.py -v
```

Expected: `4 tests ... OK`.

---

### Task 2: Use Table State as the Candidate Deck Pool

**Files:**
- Modify: `app_cv/main.py`

- [x] **Step 1: Instantiate table state after references load**

In `app_cv/main.py`, after `reference_cards` is loaded, add:

```python
from tarotvision.table_state import TableState

table_state = TableState(reference_cards.keys())
```

- [x] **Step 2: Sync confirmed cards into table state**

After `active_detected_cards` is built, add:

```python
for card in active_detected_cards:
    table_state.upsert_locked(
        card_id=card["name"],
        x=card["x"],
        y=card["y"],
        angle=card["angle"],
        confidence=1.0,
        frame_index=frame_counter,
    )
```

This is intentionally conservative: it mirrors the existing debounced output first, without replacing the current state machine yet.

- [x] **Step 3: Use available cards for new-card search**

Before calling `choose_cards_to_match`, compute:

```python
candidate_card_names = table_state.available_card_ids
all_card_names = list(reference_cards.keys())
```

Then keep current active-card refresh behavior, but use `candidate_card_names` for inactive/new-card search. The intended effect is:

```text
already confirmed cards are not treated as new-card candidates
```

- [x] **Step 4: Add payload debug fields**

Add to `runtime_snapshot`:

```python
"available_card_count": len(table_state.available_card_ids),
"tracked_card_count": len(table_state.cards),
```

- [x] **Step 5: Verify behavior**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest discover -s E:\Antigravity\Projekty\TAROT\app_cv\tests -v
python -m py_compile E:\Antigravity\Projekty\TAROT\app_cv\main.py
```

Expected: tests OK and `py_compile` exit code `0`.

---

### Task 3: Add Motion Trigger Without Treating Motion as Identity

**Files:**
- Create: `app_cv/tarotvision/motion.py`
- Create: `app_cv/tests/test_motion.py`
- Modify: `app_cv/main.py`

- [x] **Step 1: Write motion tests**

Create `app_cv/tests/test_motion.py`:

```python
import unittest

import numpy as np

from tarotvision.motion import MotionDetector


class MotionDetectorTest(unittest.TestCase):
    def test_no_motion_for_identical_frames(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        frame = np.zeros((20, 20), dtype=np.uint8)

        detector.update(frame)
        result = detector.update(frame.copy())

        self.assertFalse(result.motion_detected)

    def test_motion_when_enough_pixels_change(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        first = np.zeros((20, 20), dtype=np.uint8)
        second = first.copy()
        second[0:10, 0:10] = 255

        detector.update(first)
        result = detector.update(second)

        self.assertTrue(result.motion_detected)

    def test_settled_after_motion_stops(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        first = np.zeros((20, 20), dtype=np.uint8)
        moving = first.copy()
        moving[0:10, 0:10] = 255

        detector.update(first)
        detector.update(moving)
        detector.update(moving.copy())
        result = detector.update(moving.copy())

        self.assertTrue(result.scene_settled)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Implement motion detector**

Create `app_cv/tarotvision/motion.py`:

```python
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class MotionResult:
    motion_detected: bool
    scene_settled: bool
    changed_ratio: float


class MotionDetector:
    def __init__(self, min_changed_ratio=0.02, pixel_threshold=25, settle_frames=3):
        self.min_changed_ratio = min_changed_ratio
        self.pixel_threshold = pixel_threshold
        self.settle_frames = settle_frames
        self.previous_gray = None
        self.still_frames = 0
        self.had_motion = False

    def update(self, gray_frame):
        gray = np.asarray(gray_frame)
        if self.previous_gray is None:
            self.previous_gray = gray.copy()
            return MotionResult(False, False, 0.0)

        diff = cv2.absdiff(self.previous_gray, gray)
        changed = diff > self.pixel_threshold
        changed_ratio = float(np.count_nonzero(changed)) / float(changed.size)
        motion_detected = changed_ratio >= self.min_changed_ratio

        if motion_detected:
            self.had_motion = True
            self.still_frames = 0
        else:
            self.still_frames += 1

        scene_settled = self.had_motion and self.still_frames >= self.settle_frames
        if scene_settled:
            self.had_motion = False

        self.previous_gray = gray.copy()
        return MotionResult(motion_detected, scene_settled, changed_ratio)
```

- [x] **Step 3: Verify motion tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_motion.py -v
```

Expected: `3 tests ... OK`.

- [x] **Step 4: Integrate as a scan trigger**

In `app_cv/main.py`, update motion each frame after `gray_frame` exists:

```python
motion_result = motion_detector.update(gray_frame)
runtime_metrics.add("motion_changed_ratio", motion_result.changed_ratio)
```

Use motion only as a trigger:

```python
if motion_result.scene_settled:
    boost_frames_remaining = max(boost_frames_remaining, BOOST_AFTER_LAYOUT_CHANGE_FRAMES)
```

Do not create or identify a card from motion alone.

---

### Task 4: Add ROI Map for Occupied and Free Table Areas

**Files:**
- Create: `app_cv/tarotvision/roi_map.py`
- Create: `app_cv/tests/test_roi_map.py`

- [x] **Step 1: Write ROI tests**

Create `app_cv/tests/test_roi_map.py`:

```python
import unittest

from tarotvision.roi_map import filter_boxes_outside_occupied, inflate_box


class RoiMapTest(unittest.TestCase):
    def test_inflate_box_expands_each_side(self):
        self.assertEqual(inflate_box((10, 20, 30, 40), 5), (5, 15, 40, 50))

    def test_filters_candidate_overlapping_occupied_box(self):
        candidates = [(0, 0, 10, 10), (100, 100, 20, 20)]
        occupied = [(0, 0, 12, 12)]

        result = filter_boxes_outside_occupied(candidates, occupied, max_iou=0.1)

        self.assertEqual(result, [(100, 100, 20, 20)])


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Implement ROI helpers**

Create `app_cv/tarotvision/roi_map.py`:

```python
def inflate_box(box, margin):
    x, y, w, h = box
    return (x - margin, y - margin, w + 2 * margin, h + 2 * margin)


def box_iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh

    ix1 = max(ax, bx)
    iy1 = max(ay, by)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    intersection = iw * ih
    union = aw * ah + bw * bh - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def filter_boxes_outside_occupied(candidate_boxes, occupied_boxes, max_iou=0.1):
    result = []
    for candidate in candidate_boxes:
        overlaps = any(box_iou(candidate, occupied) > max_iou for occupied in occupied_boxes)
        if not overlaps:
            result.append(candidate)
    return result
```

- [x] **Step 3: Verify ROI tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_roi_map.py -v
```

Expected: `2 tests ... OK`.

---

### Task 5: Add Cheap Contour Tracking for Locked Cards

**Files:**
- Create: `app_cv/tarotvision/contour_tracking.py`
- Create: `app_cv/tests/test_contour_tracking.py`

- [x] **Step 1: Write tracking assignment tests**

Create `app_cv/tests/test_contour_tracking.py`:

```python
import unittest

from tarotvision.contour_tracking import assign_boxes_to_cards


class ContourTrackingTest(unittest.TestCase):
    def test_assigns_candidate_to_best_overlapping_card(self):
        tracked = {
            "00_fool": (10, 10, 50, 80),
            "01_magician": (200, 10, 50, 80),
        }
        candidates = [(12, 12, 50, 80)]

        assignments = assign_boxes_to_cards(tracked, candidates, min_iou=0.5)

        self.assertEqual(assignments, {"00_fool": (12, 12, 50, 80)})

    def test_ignores_candidate_with_low_overlap(self):
        tracked = {"00_fool": (10, 10, 50, 80)}
        candidates = [(200, 200, 50, 80)]

        assignments = assign_boxes_to_cards(tracked, candidates, min_iou=0.5)

        self.assertEqual(assignments, {})


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Implement assignment**

Create `app_cv/tarotvision/contour_tracking.py`:

```python
from tarotvision.roi_map import box_iou


def assign_boxes_to_cards(tracked_boxes, candidate_boxes, min_iou=0.5):
    assignments = {}
    used_candidates = set()

    for card_id, tracked_box in tracked_boxes.items():
        best_index = None
        best_iou = 0.0
        for index, candidate in enumerate(candidate_boxes):
            if index in used_candidates:
                continue
            overlap = box_iou(tracked_box, candidate)
            if overlap > best_iou:
                best_iou = overlap
                best_index = index

        if best_index is not None and best_iou >= min_iou:
            assignments[card_id] = candidate_boxes[best_index]
            used_candidates.add(best_index)

    return assignments
```

- [x] **Step 3: Verify tracking tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_contour_tracking.py -v
```

Expected: `2 tests ... OK`.

---

### Task 6: Add Reverify/Audit Policy

**Files:**
- Create: `app_cv/tarotvision/audit_policy.py`
- Create: `app_cv/tests/test_audit_policy.py`

- [x] **Step 1: Write audit policy tests**

Create `app_cv/tests/test_audit_policy.py`:

```python
import unittest

from tarotvision.audit_policy import should_reverify


class AuditPolicyTest(unittest.TestCase):
    def test_reverifies_when_suspicious(self):
        self.assertTrue(
            should_reverify(
                frame_index=100,
                last_verified_frame=95,
                interval_frames=120,
                suspicious=True,
            )
        )

    def test_reverifies_on_interval(self):
        self.assertTrue(
            should_reverify(
                frame_index=240,
                last_verified_frame=100,
                interval_frames=120,
                suspicious=False,
            )
        )

    def test_skips_when_recent_and_not_suspicious(self):
        self.assertFalse(
            should_reverify(
                frame_index=150,
                last_verified_frame=100,
                interval_frames=120,
                suspicious=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Implement audit policy**

Create `app_cv/tarotvision/audit_policy.py`:

```python
def should_reverify(frame_index, last_verified_frame, interval_frames, suspicious):
    if suspicious:
        return True
    return frame_index - last_verified_frame >= interval_frames
```

- [x] **Step 3: Verify audit tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_audit_policy.py -v
```

Expected: `3 tests ... OK`.

---

### Task 7: Integrate State-First Runtime Metrics

**Files:**
- Modify: `app_cv/main.py`
- Modify: `README.md`

- [x] **Step 1: Add state-first metrics**

Extend runtime metrics and diagnostics with:

```python
runtime_metrics.add("available_card_count", len(table_state.available_card_ids))
runtime_metrics.add("tracked_card_count", len(table_state.cards))
runtime_metrics.add("motion_changed_ratio", motion_result.changed_ratio)
```

Add to `runtime_snapshot`:

```python
"available_card_count": len(table_state.available_card_ids),
"tracked_card_count": len(table_state.cards),
"schedule_mode": schedule_mode_name,
"boost_frames_remaining": boost_frames_remaining,
```

- [x] **Step 2: Update README diagnostic section**

Document that `cv_metrics.jsonl` should be used to compare:

```text
fps
matching_ms
cards_checked
available_card_count
tracked_card_count
motion_changed_ratio
schedule_mode
boost_frames_remaining
```

- [x] **Step 3: Verify full local checks**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest discover -s E:\Antigravity\Projekty\TAROT\app_cv\tests -v
python -m py_compile E:\Antigravity\Projekty\TAROT\app_cv\main.py
```

Expected: all tests OK and `py_compile` exit code `0`.

---

### Task 8: Benchmark the New State-First Loop

**Files:**
- No new files required if launcher logs are enough.
- Optional later: `app_cv/benchmark_video.py`

- [ ] **Step 1: Run live test scenario**

Use `start_tarotvision.bat`, then:

```text
1. Start with empty table for 10 seconds.
2. Place 2-3 cards and wait for LOCKED/stable behavior.
3. Add one new card.
4. Move one existing card slightly.
5. Remove one card.
6. Stop after 2-3 minutes.
```

- [ ] **Step 2: Analyze logs**

Use:

```powershell
python -X utf8 -c "import json, statistics as st; p=r'E:\Antigravity\Projekty\TAROT\logs\cv_metrics.jsonl'; rows=[json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]; print(len(rows)); print(rows[0]['timestamp'], rows[-1]['timestamp']); print(st.mean(r['metrics']['fps'] for r in rows if 'fps' in r['metrics'])); print(st.mean(r['metrics']['matching_ms'] for r in rows if 'matching_ms' in r['metrics']))"
```

Expected target after this phase:

```text
steady_scan with 3-6 locked cards: >= 8 FPS on development PC
boost_scan duration: short and visible in logs
cards_checked in steady state: near 1-2
new card identification: no obvious multi-second delay under normal lighting
```

---

## Acceptance Criteria

- Existing PoC still launches via `start_tarotvision.bat`.
- Unit tests pass with stdlib `unittest`.
- `cv_metrics.jsonl` exposes enough data to distinguish empty scan, boost scan, steady scan, and reverify behavior.
- Confirmed cards are excluded from new-card candidate matching.
- Locked cards can be tracked without proving identity every frame.
- Motion is only a trigger, never card identity.
- Suspicious or missing contours trigger reverify instead of silently trusting stale state.

## Session Status (2026-05-29)

Completed in this session:

- Task 1: `table_state` module + tests.
- Task 2: candidate deck pool integration in `main.py`.
- Task 3: motion trigger module + integration.
- Task 4: ROI helpers + tests.
- Task 5: contour-tracking helpers + tests.
- Task 6: audit policy + tests.
- Task 7: state-first runtime metrics, including:
  - `available_card_count`,
  - `tracked_card_count`,
  - `motion_changed_ratio`,
  - `reverify_due_count`,
  - `tracked_assignments`,
  - `unoccupied_observed_boxes`,
  - `tracking_reverify_count`.

Remaining high-impact work:

- Execute Task 8 live benchmark scenario and compare logs against the targets.
- Use `reverify_due_count` / `tracking_reverify_count` to reduce identity matching for stable `LOCKED` cards even further.
- Introduce selective re-recognition for `needs_reverify` cards only, instead of broad periodic rescans.

## Immediate Next Action

Execute **Task 8: Benchmark the New State-First Loop** on real camera footage, then tune matching schedule thresholds using the new tracking and reverify metrics.
