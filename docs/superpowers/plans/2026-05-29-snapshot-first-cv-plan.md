# Snapshot-First CV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automatic snapshot-first CV mode that waits for a stable tarot layout, analyzes one good static frame, and publishes a full table state to the AR frontend.

**Architecture:** Keep the existing video loop alive, but split the new behavior into testable helpers before touching `main.py`. A lightweight gate detects motion and stability, a quality module scores snapshot samples, a snapshot analyzer reuses existing card detection/recognition helpers, and the frontend keeps the last approved layout until a new approved layout arrives.

**Tech Stack:** Python stdlib `unittest`, OpenCV, NumPy, existing `websockets` JSON payloads, Vite/Three.js frontend.

---

## Stan aktualny

- `app_cv/main.py` wykonuje ciagle rozpoznawanie i tracking w petli kamery.
- `app_cv/tarotvision/motion.py` juz potrafi wykryc ruch i "settled" po liczbie spokojnych klatek, ale nie modeluje snapshot-first gate.
- `app_cv/tarotvision/card_detection.py` i `card_recognition.py` sa gotowe do uzycia na pojedynczej klatce.
- `app_cv/tarotvision/messages.py` buduje kompatybilny payload, ale nie ma jeszcze sekcji snapshot layout.
- `app_ar/main.js` aktualizuje karty z `data.cards`, wiec trzeba zachowac kompatybilnosc i nie czyscic overlayu podczas stanów watchera.

## Co zostalo zrobione

- Uzgodniono nowy kierunek: stabilnosc i precyzja sa wazniejsze niz niski lag.
- Zapisano spec: `docs/superpowers/specs/2026-05-29-snapshot-first-cv-design.md`.
- Przyjeto startowe parametry: `settle_seconds = 3.0`, `sample_count = 3`, `sample_interval_ms = 250`, `publish_only_if_changed = true`.

## Kolejne kroki

Wykonac taski ponizej w kolejnosci. Kazdy task powinien byc osobnym, latwym do review commitem.

## File Structure

- Create: `app_cv/tarotvision/snapshot_gate.py`
  - Pure-Python state machine for motion -> settling -> sampling -> analyzing -> publish/hold.
- Create: `app_cv/tests/test_snapshot_gate.py`
  - Unit tests for automatic ready-layout detection without camera dependencies.
- Create: `app_cv/tarotvision/snapshot_quality.py`
  - Deterministic scoring for blur, brightness, contrast, and sample consistency.
- Create: `app_cv/tests/test_snapshot_quality.py`
  - Synthetic NumPy tests for quality scoring and sample selection.
- Create: `app_cv/tarotvision/snapshot_analyzer.py`
  - One-frame analyzer that finds card quads, deskews crops, recognizes cards, and returns layout cards.
- Create: `app_cv/tests/test_snapshot_analyzer.py`
  - Tests with mocked detector/recognizer functions so the orchestration is stable without real assets.
- Modify: `app_cv/tarotvision/messages.py`
  - Add optional `layout` / snapshot metadata while preserving `cards`.
- Modify: `app_cv/tests/test_messages.py`
  - Assert snapshot metadata is preserved and backward compatible.
- Modify: `app_cv/main.py`
  - Integrate snapshot mode behind a feature flag, keep old pipeline available.
- Modify: `app_ar/main.js`
  - Keep last good layout during watcher states; accept snapshot metadata for operator diagnostics.
- Modify: `README.md`
  - Document snapshot-first mode after implementation is verified.

---

### Task 1: Add Snapshot Gate State Machine

**Files:**
- Create: `app_cv/tarotvision/snapshot_gate.py`
- Create: `app_cv/tests/test_snapshot_gate.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_snapshot_gate.py`:

```python
import unittest

from tarotvision.snapshot_gate import SnapshotGate, SnapshotGateConfig


class SnapshotGateTest(unittest.TestCase):
    def test_starts_holding_last_good(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        self.assertEqual(gate.state, "holding_last_good")
        self.assertEqual(gate.stable_for_ms, 0)

    def test_motion_enters_settling_without_requesting_analysis(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        decision = gate.update(now_ms=1000, motion_detected=True, changed_ratio=0.20)

        self.assertEqual(decision.state, "settling")
        self.assertFalse(decision.should_sample)
        self.assertFalse(decision.should_analyze)

    def test_requests_sampling_after_three_seconds_of_quiet(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        gate.update(now_ms=1000, motion_detected=True, changed_ratio=0.20)
        gate.update(now_ms=2000, motion_detected=False, changed_ratio=0.001)
        gate.update(now_ms=3500, motion_detected=False, changed_ratio=0.001)
        decision = gate.update(now_ms=5000, motion_detected=False, changed_ratio=0.001)

        self.assertEqual(decision.state, "sampling_snapshots")
        self.assertTrue(decision.should_sample)
        self.assertEqual(decision.stable_for_ms, 3000)

    def test_new_motion_resets_stable_timer(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        gate.update(now_ms=1000, motion_detected=True, changed_ratio=0.20)
        gate.update(now_ms=2500, motion_detected=False, changed_ratio=0.001)
        gate.update(now_ms=3000, motion_detected=True, changed_ratio=0.15)
        decision = gate.update(now_ms=5000, motion_detected=False, changed_ratio=0.001)

        self.assertEqual(decision.state, "settling")
        self.assertFalse(decision.should_sample)
        self.assertEqual(decision.stable_for_ms, 2000)

    def test_publish_returns_to_holding_last_good(self):
        gate = SnapshotGate(SnapshotGateConfig(settle_seconds=3.0))

        gate.mark_published(layout_id=4, now_ms=6000)

        self.assertEqual(gate.state, "holding_last_good")
        self.assertEqual(gate.last_published_layout_id, 4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m unittest app_cv.tests.test_snapshot_gate -v
```

Expected: fail with `ModuleNotFoundError: No module named 'tarotvision.snapshot_gate'`.

- [ ] **Step 3: Implement snapshot gate**

Create `app_cv/tarotvision/snapshot_gate.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SnapshotGateConfig:
    settle_seconds: float = 3.0
    sample_count: int = 3
    sample_interval_ms: int = 250

    @property
    def settle_ms(self):
        return int(self.settle_seconds * 1000)


@dataclass(frozen=True)
class SnapshotGateDecision:
    state: str
    should_sample: bool
    should_analyze: bool
    stable_for_ms: int
    changed_ratio: float


class SnapshotGate:
    def __init__(self, config=None):
        self.config = config or SnapshotGateConfig()
        self.state = "holding_last_good"
        self.motion_started_ms = None
        self.quiet_started_ms = None
        self.stable_for_ms = 0
        self.last_published_layout_id = None

    def update(self, now_ms, motion_detected, changed_ratio):
        if motion_detected:
            self.state = "settling"
            self.motion_started_ms = now_ms
            self.quiet_started_ms = None
            self.stable_for_ms = 0
            return self._decision(False, False, changed_ratio)

        if self.state == "settling":
            if self.quiet_started_ms is None:
                self.quiet_started_ms = now_ms
            self.stable_for_ms = now_ms - self.quiet_started_ms
            if self.stable_for_ms >= self.config.settle_ms:
                self.state = "sampling_snapshots"
                return self._decision(True, False, changed_ratio)

        return self._decision(False, False, changed_ratio)

    def mark_analyzing(self):
        self.state = "analyzing_snapshot"

    def mark_published(self, layout_id, now_ms):
        self.state = "holding_last_good"
        self.last_published_layout_id = layout_id
        self.motion_started_ms = None
        self.quiet_started_ms = None
        self.stable_for_ms = 0

    def mark_rejected(self):
        self.state = "holding_last_good"
        self.motion_started_ms = None
        self.quiet_started_ms = None
        self.stable_for_ms = 0

    def _decision(self, should_sample, should_analyze, changed_ratio):
        return SnapshotGateDecision(
            state=self.state,
            should_sample=should_sample,
            should_analyze=should_analyze,
            stable_for_ms=self.stable_for_ms,
            changed_ratio=changed_ratio,
        )
```

- [ ] **Step 4: Verify tests pass**

Run:

```powershell
python -m unittest app_cv.tests.test_snapshot_gate -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/snapshot_gate.py app_cv/tests/test_snapshot_gate.py
git commit -m "feat: dodaj gate stabilnego snapshotu"
```

---

### Task 2: Add Snapshot Quality Scoring

**Files:**
- Create: `app_cv/tarotvision/snapshot_quality.py`
- Create: `app_cv/tests/test_snapshot_quality.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_snapshot_quality.py`:

```python
import unittest

import numpy as np

from tarotvision.snapshot_quality import score_snapshot, choose_best_snapshot


class SnapshotQualityTest(unittest.TestCase):
    def test_rejects_too_dark_frame(self):
        frame = np.zeros((40, 40), dtype=np.uint8)

        result = score_snapshot(frame)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reject_reason, "too_dark")

    def test_accepts_high_contrast_readable_frame(self):
        frame = np.zeros((40, 40), dtype=np.uint8)
        frame[10:30, 10:30] = 255

        result = score_snapshot(frame, min_blur_score=10.0)

        self.assertTrue(result.accepted)
        self.assertGreater(result.quality_score, 0.0)

    def test_choose_best_snapshot_ignores_rejected_frames(self):
        dark = np.zeros((40, 40), dtype=np.uint8)
        readable = np.zeros((40, 40), dtype=np.uint8)
        readable[10:30, 10:30] = 255

        selected = choose_best_snapshot([dark, readable], min_blur_score=10.0)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.index, 1)
        self.assertTrue(selected.quality.accepted)

    def test_choose_best_snapshot_returns_none_when_all_rejected(self):
        dark = np.zeros((40, 40), dtype=np.uint8)

        selected = choose_best_snapshot([dark])

        self.assertIsNone(selected)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

```powershell
python -m unittest app_cv.tests.test_snapshot_quality -v
```

Expected: fail with missing module.

- [ ] **Step 3: Implement quality scorer**

Create `app_cv/tarotvision/snapshot_quality.py`:

```python
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class SnapshotQuality:
    accepted: bool
    quality_score: float
    blur_score: float
    brightness: float
    contrast: float
    reject_reason: str = None


@dataclass(frozen=True)
class SelectedSnapshot:
    index: int
    frame: object
    quality: SnapshotQuality


def _to_gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def score_snapshot(frame, min_blur_score=20.0,
                   min_brightness=15.0, max_brightness=245.0,
                   min_contrast=10.0):
    gray = _to_gray(frame)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if brightness < min_brightness:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "too_dark")
    if brightness > max_brightness:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "too_bright")
    if contrast < min_contrast:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "low_contrast")
    if blur_score < min_blur_score:
        return SnapshotQuality(False, 0.0, blur_score, brightness, contrast, "blurry")

    quality_score = min(1.0, (blur_score / 200.0) * 0.5 + (contrast / 80.0) * 0.5)
    return SnapshotQuality(True, quality_score, blur_score, brightness, contrast)


def choose_best_snapshot(frames, **score_kwargs):
    best = None
    for index, frame in enumerate(frames):
        quality = score_snapshot(frame, **score_kwargs)
        if not quality.accepted:
            continue
        candidate = SelectedSnapshot(index, frame, quality)
        if best is None or candidate.quality.quality_score > best.quality.quality_score:
            best = candidate
    return best
```

- [ ] **Step 4: Verify tests pass**

```powershell
python -m unittest app_cv.tests.test_snapshot_quality -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/snapshot_quality.py app_cv/tests/test_snapshot_quality.py
git commit -m "feat: oceniaj jakosc snapshotow"
```

---

### Task 3: Add Snapshot Payload Metadata

**Files:**
- Modify: `app_cv/tarotvision/messages.py`
- Modify: `app_cv/tests/test_messages.py`

- [ ] **Step 1: Add failing payload test**

Append to `StatusPayloadTest` in `app_cv/tests/test_messages.py`:

```python
    def test_snapshot_layout_metadata_preserved(self):
        layout = {
            "layout_id": 7,
            "source": "snapshot",
            "state": "holding_last_good",
            "stable_for_ms": 3040,
            "quality_score": 0.82,
        }

        payload = build_status_payload(cards=[], layout=layout)

        self.assertEqual(payload["layout"]["layout_id"], 7)
        self.assertEqual(payload["layout"]["source"], "snapshot")
        self.assertEqual(payload["layout"]["state"], "holding_last_good")
```

- [ ] **Step 2: Run test and verify failure**

```powershell
python -m unittest app_cv.tests.test_messages -v
```

Expected: fail with `TypeError: build_status_payload() got an unexpected keyword argument 'layout'`.

- [ ] **Step 3: Extend payload builder**

Change signature in `app_cv/tarotvision/messages.py`:

```python
def build_status_payload(cards, metrics=None, warnings=None,
                         debug=None, runtime=None, operator=None,
                         table=None, layout=None):
```

Add `"layout": layout or {},` to the returned dict:

```python
    return {
        "detected": len(cards) > 0,
        "cards": cards,
        "metrics": metrics or {},
        "warnings": warnings or [],
        "debug": debug or {},
        "runtime": runtime or {},
        "operator": operator or {},
        "table": table or {},
        "layout": layout or {},
    }
```

- [ ] **Step 4: Verify messages tests**

```powershell
python -m unittest app_cv.tests.test_messages -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/messages.py app_cv/tests/test_messages.py
git commit -m "feat: dodaj metadata snapshot layout do payloadu"
```

---

### Task 4: Add One-Frame Snapshot Analyzer

**Files:**
- Create: `app_cv/tarotvision/snapshot_analyzer.py`
- Create: `app_cv/tests/test_snapshot_analyzer.py`

- [ ] **Step 1: Write failing orchestration tests**

Create `app_cv/tests/test_snapshot_analyzer.py`:

```python
import unittest

import numpy as np

from tarotvision.snapshot_analyzer import SnapshotAnalyzer


class SnapshotAnalyzerTest(unittest.TestCase):
    def test_returns_empty_layout_when_no_quads(self):
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [],
            crop_card=lambda frame, quad: None,
            recognize_crop=lambda crop: None,
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.cards, [])
        self.assertEqual(result.card_count, 0)

    def test_converts_recognized_quads_to_layout_cards(self):
        quad = np.array([[[10, 10]], [[10, 30]], [[20, 30]], [[20, 10]]], dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            find_quads=lambda frame: [quad],
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {
                "name": "17_star",
                "confidence": 0.91,
                "orientation": "upright",
            },
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.card_count, 1)
        self.assertEqual(result.cards[0]["name"], "17_star")
        self.assertAlmostEqual(result.cards[0]["x"], 15.0)
        self.assertAlmostEqual(result.cards[0]["y"], 20.0)
        self.assertEqual(result.cards[0]["confidence"], 0.91)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

```powershell
python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: fail with missing module.

- [ ] **Step 3: Implement analyzer**

Create `app_cv/tarotvision/snapshot_analyzer.py`:

```python
from dataclasses import dataclass

import numpy as np

from tarotvision.card_detection import find_card_quads
from tarotvision.card_recognition import deskew_card_crop


@dataclass(frozen=True)
class SnapshotAnalysisResult:
    cards: list
    card_count: int


class SnapshotAnalyzer:
    def __init__(self, find_quads=None, crop_card=None, recognize_crop=None):
        self.find_quads = find_quads or find_card_quads
        self.crop_card = crop_card or deskew_card_crop
        self.recognize_crop = recognize_crop

    def analyze(self, frame):
        cards = []
        for quad in self.find_quads(frame):
            crop = self.crop_card(frame, quad)
            recognition = self.recognize_crop(crop) if self.recognize_crop else None
            if not recognition:
                continue
            center_x, center_y = _quad_center(quad)
            cards.append({
                "name": recognition["name"],
                "x": center_x,
                "y": center_y,
                "angle": _quad_angle(quad),
                "confidence": recognition.get("confidence", 0.0),
                "orientation": recognition.get("orientation", "unknown"),
            })
        return SnapshotAnalysisResult(cards=cards, card_count=len(cards))


def _quad_points(quad):
    return np.asarray(quad, dtype=np.float32).reshape(4, 2)


def _quad_center(quad):
    points = _quad_points(quad)
    center = np.mean(points, axis=0)
    return float(center[0]), float(center[1])


def _quad_angle(quad):
    points = _quad_points(quad)
    vector = points[3] - points[0]
    return float(np.arctan2(vector[1], vector[0]))
```

- [ ] **Step 4: Verify tests pass**

```powershell
python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/snapshot_analyzer.py app_cv/tests/test_snapshot_analyzer.py
git commit -m "feat: analizuj pojedynczy snapshot ukladu"
```

---

### Task 5: Integrate Snapshot Mode in `main.py` Behind a Flag

**Files:**
- Modify: `app_cv/main.py`
- Test: existing `app_cv/tests`

- [ ] **Step 1: Add imports and feature flag**

In `app_cv/main.py`, add imports near other `tarotvision` imports:

```python
from tarotvision.snapshot_gate import SnapshotGate, SnapshotGateConfig
from tarotvision.snapshot_quality import choose_best_snapshot
from tarotvision.snapshot_analyzer import SnapshotAnalyzer
```

Add constants near runtime constants:

```python
USE_SNAPSHOT_FIRST_CV = os.environ.get("TAROTVISION_SNAPSHOT_FIRST", "0") == "1"
SNAPSHOT_SETTLE_SECONDS = 3.0
SNAPSHOT_SAMPLE_COUNT = 3
SNAPSHOT_SAMPLE_INTERVAL_MS = 250
```

- [ ] **Step 2: Instantiate snapshot helpers**

After existing runtime helper initialization, add:

```python
snapshot_gate = SnapshotGate(SnapshotGateConfig(
    settle_seconds=SNAPSHOT_SETTLE_SECONDS,
    sample_count=SNAPSHOT_SAMPLE_COUNT,
    sample_interval_ms=SNAPSHOT_SAMPLE_INTERVAL_MS,
))
snapshot_analyzer = SnapshotAnalyzer()
last_snapshot_cards = []
layout_id = 0
```

- [ ] **Step 3: Add local recognition adapter**

Near the reference/matcher setup in `main.py`, add an adapter function:

```python
def recognize_snapshot_crop(gray_crop):
    result = recognize_card_crop(gray_crop, reference_cards, orb, flann)
    if result is None:
        return None
    return {
        "name": result["card_name"],
        "confidence": result.get("confidence", 0.0),
        "orientation": result.get("orientation", "unknown"),
    }
```

Then instantiate analyzer after `reference_cards`, `orb`, and `flann` exist:

```python
snapshot_analyzer = SnapshotAnalyzer(recognize_crop=recognize_snapshot_crop)
```

If `recognize_card_crop` returns different keys in the actual code, adjust the adapter only, not `SnapshotAnalyzer`.

- [ ] **Step 4: Add snapshot branch in frame loop**

At the top of the per-frame loop after `gray` is available and `motion_result` is computed, add a guarded branch:

```python
if USE_SNAPSHOT_FIRST_CV:
    now_ms = int(time.time() * 1000)
    gate_decision = snapshot_gate.update(
        now_ms=now_ms,
        motion_detected=motion_result.motion_detected,
        changed_ratio=motion_result.changed_ratio,
    )
    layout_snapshot = {
        "layout_id": layout_id,
        "source": "snapshot",
        "state": gate_decision.state,
        "stable_for_ms": gate_decision.stable_for_ms,
    }

    if gate_decision.should_sample:
        samples = [frame.copy()]
        for _ in range(SNAPSHOT_SAMPLE_COUNT - 1):
            time.sleep(SNAPSHOT_SAMPLE_INTERVAL_MS / 1000.0)
            ok, sample_frame = cap.read()
            if ok:
                samples.append(sample_frame.copy())
        selected = choose_best_snapshot(samples)
        if selected is None:
            snapshot_gate.mark_rejected()
            layout_snapshot["snapshot_reject_reason"] = "all_samples_rejected"
        else:
            snapshot_gate.mark_analyzing()
            analysis_start = time.time()
            result = snapshot_analyzer.analyze(selected.frame)
            analysis_ms = (time.time() - analysis_start) * 1000.0
            if result.card_count > 0:
                layout_id += 1
                last_snapshot_cards = result.cards
                snapshot_gate.mark_published(layout_id=layout_id, now_ms=int(time.time() * 1000))
            else:
                snapshot_gate.mark_rejected()
                layout_snapshot["snapshot_reject_reason"] = "no_cards"
            layout_snapshot.update({
                "layout_id": layout_id,
                "state": snapshot_gate.state,
                "analysis_ms": analysis_ms,
                "quality_score": selected.quality.quality_score,
            })

    payload = build_status_payload(
        cards=last_snapshot_cards,
        metrics=runtime_metrics.snapshot(),
        warnings=operator_warnings,
        debug={},
        runtime=runtime_snapshot,
        operator=build_operator_snapshot(),
        table=table_calibration.status_snapshot(),
        layout=layout_snapshot,
    )
    current_status.update(payload)
    continue
```

Important: fit this branch to the real loop structure. The branch must not run the old continuous matching when `USE_SNAPSHOT_FIRST_CV` is true.

- [ ] **Step 5: Verify syntax and tests**

Run:

```powershell
python -m py_compile app_cv/main.py app_cv/tarotvision/snapshot_gate.py app_cv/tarotvision/snapshot_quality.py app_cv/tarotvision/snapshot_analyzer.py
python -m unittest discover -s app_cv/tests -v
```

Expected: compile OK and unit tests OK.

- [ ] **Step 6: Commit**

```powershell
git add app_cv/main.py app_cv/tarotvision app_cv/tests
git commit -m "feat: dodaj tryb snapshot-first w backendzie CV"
```

---

### Task 6: Keep Frontend Layout Sticky During Watcher States

**Files:**
- Modify: `app_ar/main.js`

- [ ] **Step 1: Preserve current card handling**

Confirm `handleCardData(detectedCards)` still receives normal `cards`. Do not remove backward compatibility with old payloads.

- [ ] **Step 2: Add layout metadata capture**

In WebSocket message handling, after JSON parse and before `handleCardData`, add:

```javascript
const layout = data.layout || {}
latestStatus = data
```

Ensure existing operator panel update continues to receive `latestStatus`.

- [ ] **Step 3: Do not clear cards during settling**

Modify the condition that passes cards to `handleCardData` so watcher-only messages keep the previous visual state:

```javascript
const layoutState = layout.state || ''
const isWatcherOnlyState = ['settling', 'sampling_snapshots', 'analyzing_snapshot'].includes(layoutState)

if (!isWatcherOnlyState) {
  handleCardData(data.cards || [])
}
```

This means cards only change when backend publishes approved `cards`.

- [ ] **Step 4: Show snapshot diagnostics in operator panel**

Add these optional labels to `operatorMetricNames` / `metricLabels` or the existing status area:

```javascript
snapshot_gate_state
stable_for_ms
snapshot_quality_score
snapshot_analysis_ms
time_from_motion_to_publish_ms
```

If metrics are not present, UI should simply omit them.

- [ ] **Step 5: Verify frontend build**

Run:

```powershell
npm --prefix app_ar run build
```

Expected: build OK. Existing Vite chunk-size warning is acceptable.

- [ ] **Step 6: Commit**

```powershell
git add app_ar/main.js
git commit -m "feat: utrzymuj ostatni layout podczas stabilizacji"
```

---

### Task 7: Add Documentation and Live Verification Notes

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-05-29-snapshot-first-cv-plan.md`

- [ ] **Step 1: Update README after code works**

Add a short section under runtime/diagnostics:

~~~markdown
### Tryb snapshot-first CV

Eksperymentalny tryb snapshot-first uruchamia lekki watcher ruchu, czeka na stabilny uklad kart i analizuje pojedyncza dobra klatke zamiast stale rozpoznawac tozsamosc kart w kazdej klatce.

```powershell
$env:TAROTVISION_SNAPSHOT_FIRST="1"
python app_cv/main.py
```

Startowe parametry sa konserwatywne: okolo 3 sekund stabilnosci, 3 snapshoty kontrolne i publikacja tylko zatwierdzonego ukladu. Overlay w przegladarce trzyma ostatni dobry wynik podczas ruchu lub odrzucenia snapshotu.
~~~

- [ ] **Step 2: Add Session Status**

Append a concrete `Session Status` section to this plan. The section must list only work that actually completed in the implementation session and exact verification command results. Use this structure and replace the example task names with the real completed scope before committing:

```markdown
## Session Status (2026-05-29, Codex — snapshot-first implementation)

Wykonano:

- Task 1: Add Snapshot Gate State Machine.

Weryfikacja:

- `python -m unittest discover -s app_cv/tests -v` -> 44 tests, OK.
- `npm --prefix app_ar run build` -> OK, existing Vite chunk-size warning.

Pozostalo:

- Live test z kamera i ukladem 3-5 kart.
```

- [ ] **Step 3: Run full verification**

Run:

```powershell
python -m unittest discover -s app_cv/tests -v
python -m py_compile app_cv/main.py app_cv/tarotvision/*.py
npm --prefix app_ar run build
```

Expected: Python tests OK, compile OK, frontend build OK.

- [ ] **Step 4: Commit**

```powershell
git add README.md docs/superpowers/plans/2026-05-29-snapshot-first-cv-plan.md
git commit -m "docs: opisz uruchamianie snapshot-first CV"
```

---

## Acceptance Criteria

- Snapshot-first mode is disabled by default and enabled by `TAROTVISION_SNAPSHOT_FIRST=1`.
- After motion, backend waits about 3 seconds of quiet before snapshot analysis.
- Backend samples 3 frames and rejects obviously poor samples.
- Frontend keeps the last approved layout during movement, settling, sampling, and rejected snapshots.
- Payload remains backward compatible: existing `cards` consumers still work.
- Diagnostics include the snapshot gate state and time-to-publish style metrics.
- Existing unit tests continue to pass.
- README documents how to run the experimental mode.

## Verification Commands

Use these before declaring implementation complete:

```powershell
python -m unittest discover -s app_cv/tests -v
python -m py_compile app_cv/main.py app_cv/tarotvision/*.py
npm --prefix app_ar run build
```

Live verification with camera:

```powershell
$env:TAROTVISION_SNAPSHOT_FIRST="1"
python app_cv/main.py
```

Then open:

```text
http://localhost:5173/?operator=1
```

Test with 3-5 cards:

- place/move a card,
- wait for about 3 seconds of stillness,
- confirm AR updates once,
- wave a hand over the table and confirm AR keeps the last good layout,
- check `logs/cv_metrics.jsonl` for snapshot gate metrics.

## Plan Self-Review

- Spec coverage: gate, quality scoring, one-frame analysis, payload, sticky frontend, metrics, docs and live verification are covered.
- Filler scan: no unresolved filler entries remain; code snippets define concrete APIs.
- Type consistency: plan uses `SnapshotGateConfig`, `SnapshotGateDecision`, `SnapshotQuality`, `SelectedSnapshot`, and `SnapshotAnalyzer` consistently across tasks.
