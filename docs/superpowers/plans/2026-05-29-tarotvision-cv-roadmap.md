# TarotVision CV Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reliable, production-oriented card recognition pipeline for TarotVision on AnkerWork C310, with a CPU baseline for HP EliteBook 830 G6 and an optional higher-performance path for the Ryzen 7 3700X + RTX 3070 PC.

**Architecture:** Keep the current Python/OpenCV + WebSocket + Three.js proof of concept alive while incrementally replacing continuous whole-frame ORB matching with a state-first table pipeline: identify a new card once, remove it from the available deck pool, track it cheaply by contour/ROI, and reverify only on suspicion or schedule. ArUco mat calibration, perspective correction, crop/deskew recognition, confidence FSM, and operator override remain the production path. Maintain classic CV as the portable baseline, but allow YOLO/ONNX/OpenVINO/CUDA to become the production engine if real benchmarks on the RTX 3070 PC prove better accuracy or stability.

**Tech Stack:** Python, OpenCV, NumPy, websockets, Vite, Three.js, optional ONNX Runtime/OpenVINO/CUDA/Ultralytics for benchmarked performance paths.

---

## Current State

The current project is a working proof of concept:

- `app_cv/main.py` captures camera frames, performs ORB/FLANN feature matching against 22 Rider-Waite-Smith Major Arcana templates, stabilizes detections, and sends JSON over WebSocket.
- `app_ar/main.js` preloads 22 card textures and renders a Three.js AR overlay.
- The AR overlay currently snaps cards to a virtual grid. This is intentional for visual order in YouTube production.
- The current CV layer still works mostly as a whole-frame template matcher. The next architecture should first isolate physical card regions, then recognize normalized card crops.
- The AnkerWork C310 can lock autofocus and autoexposure. Production runs should use locked focus/exposure to avoid frame-to-frame changes in sharpness, brightness, and feature count.
- Development and early testing happen on a stronger PC: AMD Ryzen 7 3700X, 16 GB RAM, RTX 3070. The HP EliteBook 830 G6 remains the portability target, but it is no longer the only production hardware option.
- Runtime metrics are now written to `logs/cv_metrics.jsonl`. The first benchmark showed the original matching loop at about 2.6 FPS with about 357 ms spent in matching. A scheduler optimization reduced stable-state matching to about 10 FPS with about 75-85 ms matching, proving that the main bottleneck is repeated identity matching, not camera read, preprocessing, or ORB feature extraction.
- A later boost-scan test showed that aggressive rescanning can collapse performance back to about 2-3 FPS. The next architecture must therefore avoid treating every small fluctuation as a reason to scan many cards again.

## Revision: State-First CV Direction

The next development phase is now guided by this rule:

```text
identify once -> track cheaply -> reverify only when needed
```

This means:

- the system keeps a durable table state,
- cards already confirmed on the table are removed from the candidate deck pool,
- stable cards are tracked mostly by contour/ROI instead of full identity recognition,
- new card recognition runs primarily when motion/change detection suggests a new card was placed,
- occupied regions are excluded from broad search whenever possible,
- periodic audits verify that locked cards still exist and have not drifted, without constantly proving their identity again.

Detailed implementation for this phase is tracked in:

- `docs/superpowers/plans/2026-05-29-tarotvision-state-first-cv-plan.md`

## Target Architecture

```text
AnkerWork C310 frame
  -> camera settings and optional undistort
  -> motion/change detection
  -> ArUco mat marker detection and table perspective warp
  -> occupied ROI map from tracked cards
  -> free-area card rectangle detection
  -> card crop + deskew for new or suspicious cards
  -> recognition engine against available_cards only
  -> confidence/table state machine
  -> cheap contour tracking for locked cards
  -> scheduled or suspicion-based reverify
  -> operator correction panel
  -> WebSocket JSON
  -> Three.js snap-to-layout overlay
  -> OBS
```

## File Structure

- Create: `app_cv/tarotvision/metrics.py`
  Runtime timing, FPS windows, and CSV/JSON diagnostic output.
- Created: `app_cv/tarotvision/matching_schedule.py`
  Current adaptive scheduler for empty/boost/steady scan modes.
- Create: `app_cv/tarotvision/table_state.py`
  Durable model of cards on the table, available deck pool, locked/suspicious/lost phases, and operator corrections.
- Create: `app_cv/tarotvision/motion.py`
  Frame-difference or background-subtraction triggers for "something changed" without treating motion as card identity.
- Create: `app_cv/tarotvision/roi_map.py`
  Occupied/free table regions, candidate crop filtering, and exclusion of already tracked card areas.
- Create: `app_cv/tarotvision/contour_tracking.py`
  Low-cost tracking of already identified cards by quad/ROI similarity and position drift.
- Create: `app_cv/tarotvision/table_calibration.py`
  ArUco marker configuration, table homography, perspective warp, and calibration status.
- Create: `app_cv/tarotvision/card_detection.py`
  Card rectangle detection in the warped table frame, contour filtering, and crop/deskew.
- Create: `app_cv/tarotvision/card_recognition.py`
  Reference loading, upright/reversed feature cache, crop recognition, and confidence scoring.
- Create: `app_cv/tarotvision/state_machine.py`
  Candidate/confirmed/locked/lost logic per card or per layout slot.
- Create: `app_cv/tarotvision/messages.py`
  Stable WebSocket payload schema for cards, warnings, metrics, and operator state.
- Create: `app_cv/tests/`
  Unit tests for geometry, crop normalization, scoring, and state transitions.
- Modify: `app_cv/main.py`
  Convert from monolithic loop into orchestration over the modules above.
- Modify: `app_ar/main.js`
  Later: consume richer payloads, show confidence/operator warnings, preserve snap-to-layout behavior.
- Modify: `README.md`
  Keep status and roadmap links current.

## Decisions

- Keep snap-to-layout as the default production visualization mode.
- Do not put markers on cards.
- Use markers on the mat for camera/table calibration.
- Use real scans of physically owned decks as the source of truth.
- Keep classic CV as the first portable baseline.
- Use a deck-pool model: `available_cards = all_cards - confirmed_table_cards`, with operator correction able to return a card to the pool.
- Avoid continuous identity rechecking for `LOCKED` cards. Track their contour/ROI and run identity reverify only on interval, motion, contour loss, suspicious drift, or operator request.
- Benchmark YOLO/ONNX/OpenVINO/CUDA after the project has real videos and labeled crops. If the RTX 3070 path is substantially more accurate or stable, it may become the preferred production setup for recordings.
- Record the camera configuration used for every benchmark, especially autofocus lock, exposure lock, resolution, FPS, lighting, and camera distance.

---

### Task 1: Add Runtime Metrics

**Files:**
- Create: `app_cv/tarotvision/metrics.py`
- Create: `app_cv/tests/test_metrics.py`
- Modify: `app_cv/main.py`

- [x] **Step 1: Create the package directory**

Run:

```powershell
New-Item -ItemType Directory -Force -Path app_cv\tarotvision
New-Item -ItemType File -Force -Path app_cv\tarotvision\__init__.py
New-Item -ItemType Directory -Force -Path app_cv\tests
```

Expected: directories and `__init__.py` exist.

- [x] **Step 2: Write unit tests for timing windows**

Create `app_cv/tests/test_metrics.py` using stdlib `unittest` until the project adds pytest explicitly:

```python
import unittest

from tarotvision.metrics import RollingMetric, RuntimeMetrics


class RollingMetricTest(unittest.TestCase):
    def test_keeps_last_values(self):
        metric = RollingMetric(maxlen=3)
        metric.add(10.0)
        metric.add(20.0)
        metric.add(30.0)
        metric.add(40.0)

        self.assertEqual(metric.values, [20.0, 30.0, 40.0])
        self.assertEqual(metric.average, 30.0)

    def test_empty_average_is_zero(self):
        metric = RollingMetric(maxlen=3)

        self.assertEqual(metric.average, 0.0)

    def test_runtime_metrics_snapshots_average_values(self):
        metrics = RuntimeMetrics(maxlen=2)
        metrics.add("frame_ms", 10.0)
        metrics.add("frame_ms", 20.0)
        metrics.add("frame_ms", 30.0)

        self.assertEqual(metrics.snapshot(), {"frame_ms": 25.0})
```

- [x] **Step 3: Run test and verify it fails before implementation**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest discover -s E:\Antigravity\Projekty\TAROT\app_cv\tests -v
```

Expected: import failure because `tarotvision.metrics` does not exist.

- [x] **Step 4: Implement minimal metrics module**

Create `app_cv/tarotvision/metrics.py`:

```python
from collections import deque


class RollingMetric:
    def __init__(self, maxlen=60):
        self._values = deque(maxlen=maxlen)

    @property
    def values(self):
        return list(self._values)

    @property
    def average(self):
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    def add(self, value):
        self._values.append(float(value))
```

- [x] **Step 5: Verify tests pass**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest discover -s E:\Antigravity\Projekty\TAROT\app_cv\tests -v
```

Expected: `3 tests ... OK`.

- [x] **Step 6: Integrate timings in the main loop**

Modify `app_cv/main.py` to measure:

- frame read time,
- preprocessing time,
- feature detection time,
- matching time,
- WebSocket payload update time,
- total frame time.

Expose rolling averages in `current_status["metrics"]`.

- [x] **Step 7: Include hardware and camera mode in metrics**

Add these fields to the diagnostic payload:

```json
{
  "runtime": {
    "profile": "cpu_baseline",
    "camera_focus_locked": true,
    "camera_exposure_locked": true,
    "capture_width": 1280,
    "capture_height": 720
  }
}
```

Use `profile = "cpu_baseline"` for the OpenCV path and reserve `profile = "gpu_experimental"` for later ONNX/CUDA tests.

- [x] **Step 8: Verify syntax**

Run:

```powershell
python -m py_compile app_cv\main.py app_cv\tarotvision\metrics.py
```

Expected: exit code `0`.

---

### Task 2: Add ArUco Table Calibration

**Files:**
- Create: `app_cv/tarotvision/table_calibration.py`
- Create: `app_cv/tests/test_table_calibration.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Define marker layout**

Use four ArUco markers on the mat:

```text
ID 10 = top-left
ID 11 = top-right
ID 12 = bottom-right
ID 13 = bottom-left
```

The markers define the table work area, not the card identities.

- [ ] **Step 2: Write tests for marker completeness**

Create `app_cv/tests/test_table_calibration.py`:

```python
import numpy as np

from tarotvision.table_calibration import has_required_markers


def test_has_required_markers_when_all_ids_present():
    ids = np.array([[10], [11], [12], [13]], dtype=np.int32)

    assert has_required_markers(ids)


def test_has_required_markers_rejects_missing_id():
    ids = np.array([[10], [11], [13]], dtype=np.int32)

    assert not has_required_markers(ids)
```

- [ ] **Step 3: Implement calibration helpers**

Create `app_cv/tarotvision/table_calibration.py`:

```python
import cv2
import numpy as np


REQUIRED_MARKER_IDS = {10, 11, 12, 13}
TABLE_WIDTH = 1280
TABLE_HEIGHT = 720


def has_required_markers(ids):
    if ids is None:
        return False
    present = {int(value) for value in np.asarray(ids).reshape(-1)}
    return REQUIRED_MARKER_IDS.issubset(present)


def detect_aruco_markers(gray_frame):
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    corners, ids, rejected = detector.detectMarkers(gray_frame)
    return corners, ids, rejected
```

- [ ] **Step 4: Verify tests**

Run:

```powershell
python -m pytest app_cv\tests\test_table_calibration.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Integrate calibration status**

Modify `app_cv/main.py` so each frame adds a table status:

```json
{
  "table": {
    "calibrated": true,
    "marker_ids": [10, 11, 12, 13]
  }
}
```

If markers are missing, continue running the current ORB pipeline as fallback.

---

### Task 3: Add Card Rectangle Detection on Warped Table

**Files:**
- Create: `app_cv/tarotvision/card_detection.py`
- Create: `app_cv/tests/test_card_detection.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write tests for aspect filtering**

Create `app_cv/tests/test_card_detection.py`:

```python
from tarotvision.card_detection import is_card_aspect_ratio


def test_accepts_tarot_like_ratio():
    assert is_card_aspect_ratio(width=70, height=120)


def test_rejects_square_ratio():
    assert not is_card_aspect_ratio(width=100, height=100)
```

- [ ] **Step 2: Implement aspect filtering**

Create `app_cv/tarotvision/card_detection.py`:

```python
CARD_ASPECT_RATIO = 1.72
CARD_ASPECT_TOLERANCE = 0.45


def is_card_aspect_ratio(width, height):
    if width <= 0 or height <= 0:
        return False
    ratio = max(width, height) / min(width, height)
    return abs(ratio - CARD_ASPECT_RATIO) <= CARD_ASPECT_TOLERANCE
```

- [ ] **Step 3: Verify tests**

Run:

```powershell
python -m pytest app_cv\tests\test_card_detection.py -q
```

Expected: `2 passed`.

- [ ] **Step 4: Add contour detector**

Extend `card_detection.py` with:

```python
import cv2
import numpy as np


def find_card_quads(warped_bgr):
    gray = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    quads = []
    frame_area = warped_bgr.shape[0] * warped_bgr.shape[1]
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < frame_area * 0.005:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue
        x, y, w, h = cv2.boundingRect(approx)
        if is_card_aspect_ratio(w, h):
            quads.append(approx)
    return quads
```

- [ ] **Step 5: Integrate behind a feature flag**

Add a constant in `app_cv/main.py`:

```python
USE_TABLE_CARD_DETECTION = False
```

When `True`, run card rectangle detection on the warped table. When `False`, keep current whole-frame ORB path.

---

### Task 4: Add Crop and Deskew Recognition

**Files:**
- Create: `app_cv/tarotvision/card_recognition.py`
- Create: `app_cv/tests/test_card_recognition.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Define normalized crop size**

Use:

```python
NORMALIZED_CARD_WIDTH = 300
NORMALIZED_CARD_HEIGHT = 516
```

This keeps the 1.72 tarot aspect ratio while staying small enough for CPU matching.

- [ ] **Step 2: Write test for orientation variants**

Create `app_cv/tests/test_card_recognition.py`:

```python
from tarotvision.card_recognition import build_variant_names


def test_build_variant_names_contains_upright_and_reversed():
    variants = build_variant_names("17_star")

    assert variants == ["17_star:upright", "17_star:reversed"]
```

- [ ] **Step 3: Implement variant naming**

Create `app_cv/tarotvision/card_recognition.py`:

```python
NORMALIZED_CARD_WIDTH = 300
NORMALIZED_CARD_HEIGHT = 516


def build_variant_names(card_name):
    return [f"{card_name}:upright", f"{card_name}:reversed"]
```

- [ ] **Step 4: Verify test**

Run:

```powershell
python -m pytest app_cv\tests\test_card_recognition.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Move ORB reference cache into this module**

Refactor current reference loading from `app_cv/main.py` into:

```python
def load_reference_cards(cv_assets_dir, orb, clahe):
    ...
```

The returned cache must include both upright and 180-degree reversed descriptors.

- [ ] **Step 6: Add crop recognition API**

Expose:

```python
def recognize_card_crop(gray_crop, reference_cards, orb, matcher):
    ...
```

Return:

```python
{
    "name": "17_star",
    "orientation": "upright",
    "confidence": 0.91,
    "match_count": 42,
    "inlier_ratio": 0.68
}
```

---

### Task 5: Add Confidence State Machine

**Files:**
- Create: `app_cv/tarotvision/state_machine.py`
- Create: `app_cv/tests/test_state_machine.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write tests for confirmation threshold**

Create `app_cv/tests/test_state_machine.py`:

```python
from tarotvision.state_machine import CardStateMachine


def test_confirms_after_repeated_high_confidence_frames():
    fsm = CardStateMachine(confirm_frames=3, min_confidence=0.8)

    for _ in range(2):
        state = fsm.update("17_star", 0.91)
        assert state.phase == "candidate"

    state = fsm.update("17_star", 0.91)
    assert state.phase == "confirmed"


def test_resets_when_card_identity_changes():
    fsm = CardStateMachine(confirm_frames=3, min_confidence=0.8)

    fsm.update("17_star", 0.91)
    state = fsm.update("18_moon", 0.91)

    assert state.phase == "candidate"
    assert state.card_id == "18_moon"
```

- [ ] **Step 2: Implement state machine**

Create `app_cv/tarotvision/state_machine.py`:

```python
from dataclasses import dataclass


@dataclass
class CardState:
    card_id: str | None
    phase: str
    frames: int
    confidence: float


class CardStateMachine:
    def __init__(self, confirm_frames=5, min_confidence=0.8):
        self.confirm_frames = confirm_frames
        self.min_confidence = min_confidence
        self.state = CardState(card_id=None, phase="empty", frames=0, confidence=0.0)

    def update(self, card_id, confidence):
        if confidence < self.min_confidence:
            self.state = CardState(card_id=None, phase="empty", frames=0, confidence=confidence)
            return self.state

        if self.state.card_id == card_id:
            frames = self.state.frames + 1
        else:
            frames = 1

        phase = "confirmed" if frames >= self.confirm_frames else "candidate"
        self.state = CardState(card_id=card_id, phase=phase, frames=frames, confidence=confidence)
        return self.state
```

- [ ] **Step 3: Verify tests**

Run:

```powershell
python -m pytest app_cv\tests\test_state_machine.py -q
```

Expected: `2 passed`.

- [ ] **Step 4: Gate WebSocket output**

Modify `app_cv/main.py` so `current_status["cards"]` includes only confirmed or locked cards. Candidate cards go to `current_status["debug"]["candidates"]`.

---

### Task 6: Add Operator and Debug Payload

**Files:**
- Create: `app_cv/tarotvision/messages.py`
- Create: `app_cv/tests/test_messages.py`
- Modify: `app_cv/main.py`
- Modify: `app_ar/main.js`

- [ ] **Step 1: Define stable payload schema**

Create `app_cv/tests/test_messages.py`:

```python
from tarotvision.messages import build_status_payload


def test_payload_contains_required_sections():
    payload = build_status_payload(cards=[], metrics={"fps": 30.0}, warnings=["low_confidence"])

    assert payload["detected"] is False
    assert payload["cards"] == []
    assert payload["metrics"]["fps"] == 30.0
    assert payload["warnings"] == ["low_confidence"]
```

- [ ] **Step 2: Implement payload builder**

Create `app_cv/tarotvision/messages.py`:

```python
def build_status_payload(cards, metrics=None, warnings=None, debug=None):
    return {
        "detected": len(cards) > 0,
        "cards": cards,
        "metrics": metrics or {},
        "warnings": warnings or [],
        "debug": debug or {},
    }
```

- [ ] **Step 3: Verify tests**

Run:

```powershell
python -m pytest app_cv\tests\test_messages.py -q
```

Expected: `1 passed`.

- [ ] **Step 4: Preserve frontend compatibility**

Modify `app_ar/main.js` so it continues using `data.cards || []` and ignores new fields unless an operator panel is visible.

---

### Task 7: Add Offline Benchmark Mode

**Files:**
- Create: `app_cv/benchmark_video.py`
- Create: `docs/benchmarking.md`

- [ ] **Step 1: Add benchmark script**

Create `app_cv/benchmark_video.py` that accepts:

```powershell
python app_cv\benchmark_video.py --video path\to\sample.mp4 --output analizy\benchmark_results.csv
```

It should run the same detection pipeline without `cv2.imshow` and write per-frame metrics.

- [ ] **Step 2: Add benchmarking guide**

Create `docs/benchmarking.md` with:

```markdown
# TarotVision Benchmarking

Record 5-10 short C310 clips under real lighting:

1. one card centered,
2. three-card spread,
3. hand occlusion,
4. glare test,
5. fast placement,
6. low-light test.

Measure:

- frame number,
- detected card,
- expected card,
- confidence,
- processing time,
- false positives,
- missed detections.
- hardware profile,
- focus lock state,
- exposure lock state,
- capture resolution.
```

- [ ] **Step 3: Use benchmark results before adopting YOLO**

Do not add YOLO/ONNX/OpenVINO to the production path until the benchmark shows the classic CV baseline is insufficient.

---

### Task 8: Evaluate YOLO/ONNX/OpenVINO/CUDA as a Performance Path

**Files:**
- Create: `experiments/yolo/README.md`
- Create: `experiments/yolo/dataset_notes.md`

- [ ] **Step 1: Document experiment boundaries**

Create `experiments/yolo/README.md`:

```markdown
# YOLO / ONNX / CUDA Experiment

This is a benchmarked performance path, not an automatic replacement for classic CV.

Evaluate YOLO/ONNX/OpenVINO/CUDA after:

- real deck scans exist,
- real C310 sample videos exist,
- classic CV benchmark results exist,
- license implications are reviewed,
- tests are run on both HP EliteBook 830 G6 and the Ryzen 7 3700X + RTX 3070 PC when possible.
```

- [ ] **Step 2: Define success criteria**

YOLO/ONNX/OpenVINO/CUDA can replace or augment classic CV only if it beats the crop-based baseline on:

- accuracy,
- false positive rate,
- frame time on HP EliteBook 830 G6,
- frame time on Ryzen 7 3700X + RTX 3070,
- stability under hand occlusion,
- maintenance effort.

---

## Acceptance Criteria

- The current PoC still runs.
- README links to this roadmap.
- Card recognition development is guided by measurable benchmark results.
- Snap-to-layout remains the default AR mode.
- The project has a clear path from 22-card PoC to 78-card production deck.
- YOLO/ONNX/OpenVINO/CUDA remains evidence-based and may become production only after benchmarks justify it.

## Self-Review

- Spec coverage: covers current PoC, real scans, ArUco mat, crop/deskew, confidence, operator correction, snap layout, camera focus/exposure lock, CPU baseline, stronger PC option, and YOLO/ONNX/OpenVINO/CUDA benchmarking.
- Placeholder scan: no `TBD` or unspecified implementation steps remain.
- Type consistency: module names and function names are introduced before later tasks reference them.
