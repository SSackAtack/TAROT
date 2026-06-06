# State-First Diff Runtime Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for inline execution or `superpowers:subagent-driven-development` for task-by-task implementation with review checkpoints. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zbudować główny runtime CV oparty o stabilne snapshoty sesji: locked empty reference, rolling previous/current snapshots, diff w ROI, recognition tylko dla zmian oraz aktualizację `TableState`.

**Architecture:** Nowy pipeline ma działać jako `state-first diff`: Operator najpierw wymusza pustą matę jako nieusuwalną referencję sesji, potem backend porównuje tylko dwa ostatnie stabilne snapshoty i używa pustej maty do klasyfikacji ROI jako `added`, `removed`, `moved_or_replaced` albo `noise`. Obecny `SnapshotFirstPipeline` zostaje fallbackiem/resync, a nie głównym kierunkiem rozwoju.

**Tech Stack:** Python 3.13, OpenCV, NumPy, stdlib `unittest`, istniejące `StatusStore`, WebSocket payload v1, Vite/JavaScript Studio tylko dla minimalnych kontrolek operatorskich.

---

## Status ogólny

### Stan aktualny

- Produkcyjny backend używa obecnie `SnapshotFirstPipeline`.
- `BackgroundModel` porównuje `empty_reference` z bieżącą klatką, ale jest opcjonalny i może zostać wyczyszczony komendą `background_clear`.
- Aktualny runtime nie ma trwałego modelu `empty_reference + previous_snapshot + current_snapshot`.
- Offline lab state-first ma zatwierdzone elementy Stage 1-6, ale nie zostały one włączone do runtime.
- Stara gałąź `origin/task/cv-stage-6-rws-expansion-benchmark-001` zawiera zalążek `ChangeDetector` i `previous_stable_snapshot`, ale bez pełnej polityki sesji snapshotów.
- `app_ar/public/active_decks.json` pozostaje lokalną konfiguracją operatora i nie jest częścią tego planu.

### Co zostało rozstrzygnięte

- Pusta mata nie jest jednorazowym testem. To stały baseline sesji.
- Głównym detektorem zdarzenia ma być `previous_snapshot vs current_snapshot`.
- Pusta mata ma być używana w tym samym ROI jako klasyfikator: dodano, usunięto, przesunięto/zastąpiono, szum.
- W pamięci runtime mają istnieć najwyżej trzy obrazy logiczne: `empty_reference`, `previous_snapshot`, `current_snapshot`.
- Stare snapshoty po rotacji mają być kasowane z pamięci przez nadpisanie referencji, a nie zapisywane jako rosnąca historia.
- Autotune/Calibration Wizard nie jest głównym pipeline; może zostać preflightem i diagnostyką.

### Decyzja ryzyka

To jest **Yellow/Red Lane architecture change**. Plan można implementować na branchu roboczym, ale przełączenie tego pipeline na domyślny runtime oraz merge do `master` wymaga decyzji Michała.

---

## Docelowy workflow

```text
Operator starts session
  -> capture locked empty reference
  -> seed previous_snapshot from empty reference
  -> watch motion lightly
  -> wait for stable current snapshot
  -> diff previous vs current
  -> classify each ROI using previous/current/empty
  -> crop only changed ROI
  -> recognize added or changed cards
  -> update TableState
  -> publish full layout
  -> rotate previous = current, clear current
```

## Reguły klasyfikacji ROI

W każdym ROI wykrytym przez `previous_snapshot vs current_snapshot` liczymy:

```text
previous_empty_ratio = difference(previous_roi, empty_roi)
current_empty_ratio  = difference(current_roi, empty_roi)
```

Decyzja:

| previous vs empty | current vs empty | Znaczenie |
|---:|---:|---|
| low | low | `noise_or_lighting` |
| low | high | `added` |
| high | low | `removed` |
| high | high | `moved_or_replaced` |

Progi startowe:

```text
roi_foreground_threshold = 0.10
global_shift_ratio = 0.45
min_area_ratio = 0.002
max_area_ratio = 0.35
padding_px = 16
```

Te progi są parametrami runtime, ale nie uruchamiamy nowego autotuningu jako pierwszej odpowiedzi. Najpierw wdrażamy poprawny kontrakt i testy syntetyczne.

---

## File Structure

### New files

- `app_cv/tarotvision/snapshot_session_store.py`
  - Odpowiada za sesję snapshotów: `empty_reference`, `previous_snapshot`, `current_snapshot`, locked state, rotację i reset tylko po zakończeniu sesji.
- `app_cv/tests/test_snapshot_session_store.py`
  - Testy cyklu życia snapshotów i blokad sesji.
- `app_cv/tarotvision/change_detection.py`
  - Runtime detector zmian na bazie `previous/current`, klasyfikujący ROI przez porównanie z empty reference.
- `app_cv/tests/test_change_detection.py`
  - Testy syntetyczne: added, removed, moved/replaced, noise, global shift.
- `app_cv/tarotvision/pipelines/state_first_diff.py`
  - Nowy pipeline runtime łączący gate, session store, change detector, analyzer i table state.
- `app_cv/tests/test_state_first_diff_pipeline.py`
  - Testy pipeline na mockach, bez kamery.
- `docs/operator/state_first_diff_mvp_smoke.md`
  - Minimalny smoke test operatora po wdrożeniu.

### Modified files

- `app_cv/tarotvision/background_model.py`
  - Dodać `capture_many()`, `changed_ratio()` i `roi_foreground_ratio()`.
- `app_cv/tarotvision/snapshot_analyzer.py`
  - Dodać nieinwazyjne `roi_hints=None`; global analysis zostaje kompatybilny.
- `app_cv/tarotvision/table_state.py`
  - Dodać metody aktualizacji przez zdarzenia ROI.
- `app_cv/tarotvision/pipelines/__init__.py`
  - Eksportować `StateFirstDiffPipeline` bez usuwania `SnapshotFirstPipeline`.
- `app_cv/tarotvision/tuning_protocol.py`
  - Dodać komendy sesji: `session_start`, `session_capture_empty_reference`, `session_end`, `session_resync_table`.
- `app_cv/main.py`
  - Podłączyć nowy pipeline za flagą `TAROTVISION_PIPELINE=state_first_diff`.
- `app_ar/src/studio/studioConsole.js`
  - Minimalnie pokazać status locked empty reference i przycisk sesji, jeśli payload go zawiera.

---

## Task 1: Snapshot Session Store

**Lane:** Green
**Cel:** stworzyć niezawodny model pamięci snapshotów przed integracją detekcji.

**Files:**

- Create: `app_cv/tarotvision/snapshot_session_store.py`
- Create: `app_cv/tests/test_snapshot_session_store.py`

- [ ] **Step 1: Write failing lifecycle tests**

Create `app_cv/tests/test_snapshot_session_store.py`:

```python
import unittest

import numpy as np

from tarotvision.snapshot_session_store import SnapshotSessionStore


class SnapshotSessionStoreTest(unittest.TestCase):
    def frame(self, value):
        return np.full((20, 30, 3), value, dtype=np.uint8)

    def test_requires_empty_reference_before_current_snapshot(self):
        store = SnapshotSessionStore()

        with self.assertRaises(RuntimeError):
            store.set_current_snapshot(self.frame(10))

    def test_capture_empty_reference_locks_active_session(self):
        store = SnapshotSessionStore()
        empty = self.frame(5)

        store.start_session()
        store.capture_empty_reference(empty)

        self.assertTrue(store.session_active)
        self.assertTrue(store.empty_reference_locked)
        self.assertIsNotNone(store.empty_reference)
        self.assertIsNotNone(store.previous_snapshot)

    def test_cannot_clear_empty_reference_during_active_session(self):
        store = SnapshotSessionStore()
        store.start_session()
        store.capture_empty_reference(self.frame(5))

        with self.assertRaises(RuntimeError):
            store.clear_empty_reference()

    def test_commit_rotates_current_into_previous_and_drops_current(self):
        store = SnapshotSessionStore()
        store.start_session()
        store.capture_empty_reference(self.frame(5))
        current = self.frame(40)

        store.set_current_snapshot(current)
        store.commit_current_snapshot()

        self.assertIsNone(store.current_snapshot)
        self.assertTrue(np.array_equal(store.previous_snapshot.image, current))

    def test_discard_keeps_previous_snapshot(self):
        store = SnapshotSessionStore()
        store.start_session()
        empty = self.frame(5)
        store.capture_empty_reference(empty)
        previous_before = store.previous_snapshot.image.copy()

        store.set_current_snapshot(self.frame(80))
        store.discard_current_snapshot()

        self.assertIsNone(store.current_snapshot)
        self.assertTrue(np.array_equal(store.previous_snapshot.image, previous_before))

    def test_end_session_allows_reference_clear(self):
        store = SnapshotSessionStore()
        store.start_session()
        store.capture_empty_reference(self.frame(5))

        store.end_session()
        store.clear_empty_reference()

        self.assertFalse(store.session_active)
        self.assertFalse(store.empty_reference_locked)
        self.assertIsNone(store.empty_reference)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_snapshot_session_store -v
```

Expected: FAIL because `tarotvision.snapshot_session_store` does not exist.

- [ ] **Step 3: Implement store**

Create `app_cv/tarotvision/snapshot_session_store.py`:

```python
from dataclasses import dataclass
import time

import numpy as np


@dataclass
class SnapshotFrame:
    image: np.ndarray
    timestamp_ms: int
    role: str


class SnapshotSessionStore:
    def __init__(self, clock_ms=None):
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self.session_active = False
        self.empty_reference_locked = False
        self.empty_reference = None
        self.previous_snapshot = None
        self.current_snapshot = None

    def start_session(self):
        self.session_active = True
        self.current_snapshot = None

    def end_session(self):
        self.session_active = False
        self.empty_reference_locked = False
        self.current_snapshot = None

    def capture_empty_reference(self, frame):
        if not self.session_active:
            raise RuntimeError("session must be active before empty reference capture")
        snapshot = self._snapshot(frame, "empty_reference")
        self.empty_reference = snapshot
        self.previous_snapshot = self._snapshot(frame, "previous_snapshot")
        self.current_snapshot = None
        self.empty_reference_locked = True

    def clear_empty_reference(self):
        if self.session_active and self.empty_reference_locked:
            raise RuntimeError("empty reference is locked during active session")
        self.empty_reference = None
        self.previous_snapshot = None
        self.current_snapshot = None
        self.empty_reference_locked = False

    def set_current_snapshot(self, frame):
        if not self.session_active:
            raise RuntimeError("session is not active")
        if self.empty_reference is None:
            raise RuntimeError("empty reference is required before current snapshot")
        self.current_snapshot = self._snapshot(frame, "current_snapshot")

    def commit_current_snapshot(self):
        if self.current_snapshot is None:
            raise RuntimeError("current snapshot is missing")
        self.previous_snapshot = self._snapshot(self.current_snapshot.image, "previous_snapshot")
        self.current_snapshot = None

    def discard_current_snapshot(self):
        self.current_snapshot = None

    def ready_for_diff(self):
        return (
            self.session_active
            and self.empty_reference is not None
            and self.previous_snapshot is not None
            and self.current_snapshot is not None
        )

    def _snapshot(self, frame, role):
        if frame is None:
            raise ValueError("snapshot frame cannot be None")
        return SnapshotFrame(
            image=np.asarray(frame).copy(),
            timestamp_ms=self._clock_ms(),
            role=role,
        )
```

- [ ] **Step 4: Run tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_snapshot_session_store -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add app_cv/tarotvision/snapshot_session_store.py app_cv/tests/test_snapshot_session_store.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: add snapshot session store"
```

---

## Task 2: Background Model ROI Semantics

**Lane:** Green
**Cel:** zmienić pustą matę z pomocniczego foreground mask na stały baseline ROI.

**Files:**

- Modify: `app_cv/tarotvision/background_model.py`
- Modify: `app_cv/tests/test_background_model.py`

- [ ] **Step 1: Add failing tests**

Append to `app_cv/tests/test_background_model.py`:

```python
    def test_capture_many_uses_median_reference(self):
        model = BackgroundModel()
        frames = [
            np.full((10, 10, 3), 10, dtype=np.uint8),
            np.full((10, 10, 3), 20, dtype=np.uint8),
            np.full((10, 10, 3), 30, dtype=np.uint8),
        ]

        model.capture_many(frames)

        self.assertTrue(model.active)
        mask = model.foreground_mask(np.full((10, 10, 3), 20, dtype=np.uint8), threshold=5)
        self.assertEqual(float(np.count_nonzero(mask)), 0.0)

    def test_roi_foreground_ratio_uses_same_roi_against_empty_reference(self):
        empty = np.zeros((100, 140, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        frame = empty.copy()
        cv2.rectangle(frame, (45, 20), (95, 80), (80, 90, 85), -1)

        model = BackgroundModel()
        model.capture(empty)

        card_ratio = model.roi_foreground_ratio(frame, (45, 20, 50, 60), threshold=20)
        empty_ratio = model.roi_foreground_ratio(frame, (0, 0, 20, 20), threshold=20)

        self.assertGreater(card_ratio, 0.8)
        self.assertLess(empty_ratio, 0.05)
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_background_model -v
```

Expected: FAIL because `capture_many` and `roi_foreground_ratio` do not exist.

- [ ] **Step 3: Implement methods**

Modify `app_cv/tarotvision/background_model.py` to add:

```python
    def capture_many(self, frames):
        gray_frames = []
        for frame in frames:
            if frame is None:
                continue
            arr = np.asarray(frame)
            gray = arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            gray_frames.append(gray)
        if not gray_frames:
            self.clear()
            return
        shape = gray_frames[0].shape
        aligned = [frame for frame in gray_frames if frame.shape == shape]
        if not aligned:
            self.clear()
            return
        self._gray_background = np.median(np.stack(aligned, axis=0), axis=0).astype(np.uint8)

    def changed_ratio(self, frame, threshold=18):
        mask = self.foreground_mask(frame, threshold=threshold)
        if mask is None or mask.size == 0:
            return 0.0
        return float(np.count_nonzero(mask)) / float(mask.size)

    def roi_foreground_ratio(self, frame, bbox, threshold=18):
        mask = self.foreground_mask(frame, threshold=threshold)
        if mask is None:
            return 0.0
        x, y, w, h = [int(v) for v in bbox]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(mask.shape[1], x + w)
        y2 = min(mask.shape[0], y + h)
        roi = mask[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0
        return float(np.count_nonzero(roi)) / float(roi.size)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_background_model -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add app_cv/tarotvision/background_model.py app_cv/tests/test_background_model.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: add empty reference roi semantics"
```

---

## Task 3: Runtime Change Detector

**Lane:** Green
**Cel:** przenieść zatwierdzoną ideę Stage 1/2 do runtime w małym, testowalnym module.

**Files:**

- Create: `app_cv/tarotvision/change_detection.py`
- Create: `app_cv/tests/test_change_detection.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_change_detection.py`:

```python
import unittest

import cv2
import numpy as np

from tarotvision.background_model import BackgroundModel
from tarotvision.change_detection import ChangeDetector, ChangeDetectorConfig


class ChangeDetectorTest(unittest.TestCase):
    def empty(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        frame[:, :] = (20, 55, 35)
        return frame

    def with_card(self, frame, color=(90, 90, 85)):
        result = frame.copy()
        cv2.rectangle(result, (120, 50), (180, 150), color, -1)
        return result

    def model(self, empty):
        background = BackgroundModel()
        background.capture(empty)
        return background

    def test_classifies_added_region_using_empty_roi(self):
        empty = self.empty()
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(empty, self.with_card(empty), empty_reference=self.model(empty))

        self.assertFalse(result.global_shift)
        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "added")

    def test_classifies_removed_region_using_previous_and_current_empty_roi(self):
        empty = self.empty()
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(self.with_card(empty), empty, empty_reference=self.model(empty))

        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "removed")

    def test_classifies_moved_or_replaced_when_both_rois_are_foreground(self):
        empty = self.empty()
        previous = self.with_card(empty, color=(90, 90, 85))
        current = self.with_card(empty, color=(140, 130, 120))
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(previous, current, empty_reference=self.model(empty))

        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "moved_or_replaced")

    def test_ignores_tiny_noise(self):
        empty = self.empty()
        current = empty.copy()
        cv2.circle(current, (20, 20), 3, (255, 255, 255), -1)
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03))

        result = detector.detect(empty, current, empty_reference=self.model(empty))

        self.assertEqual(result.regions, [])
        self.assertGreaterEqual(result.ignored_small_count, 1)

    def test_flags_global_shift(self):
        previous = np.zeros((200, 300, 3), dtype=np.uint8)
        current = np.full((200, 300, 3), 80, dtype=np.uint8)
        detector = ChangeDetector(ChangeDetectorConfig(global_shift_ratio=0.45))

        result = detector.detect(previous, current)

        self.assertTrue(result.global_shift)
        self.assertEqual(result.regions, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_change_detection -v
```

Expected: FAIL because `change_detection.py` does not exist.

- [ ] **Step 3: Implement detector**

Implement `app_cv/tarotvision/change_detection.py` using the old branch as baseline, but classify every ROI with both previous and current foreground ratios:

```python
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ChangeDetectorConfig:
    threshold: int = 20
    min_area_ratio: float = 0.002
    max_area_ratio: float = 0.35
    global_shift_ratio: float = 0.45
    padding_px: int = 16
    roi_foreground_threshold: float = 0.10


@dataclass(frozen=True)
class ChangeRegion:
    bbox: tuple[int, int, int, int]
    area_ratio: float
    kind: str
    previous_empty_ratio: float
    current_empty_ratio: float


@dataclass(frozen=True)
class ChangeDetectionResult:
    regions: list[ChangeRegion]
    mask_nonzero_ratio: float
    global_shift: bool
    ignored_small_count: int
    ignored_large_count: int


class ChangeDetector:
    def __init__(self, config=None):
        self.config = config or ChangeDetectorConfig()

    def detect(self, previous_frame, current_frame, empty_reference=None):
        previous_gray = _to_gray(previous_frame)
        current_gray = _to_gray(current_frame)
        if previous_gray.shape != current_gray.shape:
            return ChangeDetectionResult([], 0.0, True, 0, 0)

        mask = _difference_mask(previous_gray, current_gray, self.config.threshold)
        mask_ratio = _mask_ratio(mask)
        if mask_ratio >= self.config.global_shift_ratio:
            return ChangeDetectionResult([], mask_ratio, True, 0, 0)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        frame_area = float(mask.shape[0] * mask.shape[1])
        regions = []
        ignored_small = 0
        ignored_large = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area_ratio = float(w * h) / frame_area
            if area_ratio < self.config.min_area_ratio:
                ignored_small += 1
                continue
            if area_ratio > self.config.max_area_ratio:
                ignored_large += 1
                continue
            bbox = _pad_bbox((x, y, w, h), mask.shape[1], mask.shape[0], self.config.padding_px)
            previous_ratio, current_ratio = _empty_ratios(previous_frame, current_frame, bbox, empty_reference)
            regions.append(ChangeRegion(
                bbox=bbox,
                area_ratio=area_ratio,
                kind=_classify(previous_ratio, current_ratio, self.config.roi_foreground_threshold),
                previous_empty_ratio=previous_ratio,
                current_empty_ratio=current_ratio,
            ))
        regions.sort(key=lambda region: region.area_ratio, reverse=True)
        return ChangeDetectionResult(regions, mask_ratio, False, ignored_small, ignored_large)


def _to_gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def _difference_mask(previous_gray, current_gray, threshold):
    diff = cv2.absdiff(previous_gray, current_gray)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)
    _, mask = cv2.threshold(diff, int(threshold), 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def _mask_ratio(mask):
    if mask is None or mask.size == 0:
        return 0.0
    return float(np.count_nonzero(mask)) / float(mask.size)


def _pad_bbox(bbox, width, height, padding):
    x, y, w, h = bbox
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(width, x + w + padding)
    y2 = min(height, y + h + padding)
    return (x1, y1, x2 - x1, y2 - y1)


def _empty_ratios(previous_frame, current_frame, bbox, empty_reference):
    if empty_reference is None or not getattr(empty_reference, "active", False):
        return 1.0, 1.0
    return (
        empty_reference.roi_foreground_ratio(previous_frame, bbox),
        empty_reference.roi_foreground_ratio(current_frame, bbox),
    )


def _classify(previous_ratio, current_ratio, threshold):
    previous_has_card = previous_ratio >= threshold
    current_has_card = current_ratio >= threshold
    if not previous_has_card and current_has_card:
        return "added"
    if previous_has_card and not current_has_card:
        return "removed"
    if previous_has_card and current_has_card:
        return "moved_or_replaced"
    return "noise_or_lighting"
```

- [ ] **Step 4: Run tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add app_cv/tarotvision/change_detection.py app_cv/tests/test_change_detection.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: add state-first change detector"
```

---

## Task 4: Snapshot Analyzer ROI Mode

**Lane:** Yellow
**Cel:** pozwolić analyzerowi analizować tylko regiony zmian, zachowując kompatybilność obecnego full-frame path.

**Files:**

- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Modify: `app_cv/tests/test_snapshot_analyzer.py`

- [ ] **Step 1: Add ROI contract tests**

Add tests that call:

```python
result = analyzer.analyze(frame, roi_hints=[(40, 30, 80, 120)])
```

Expected:

- only ROI crop is passed to detector,
- diagnostics include `roi_count`,
- global full-frame path still works when `roi_hints=None`,
- empty `roi_hints=[]` returns no cards and does not run global fallback.

- [ ] **Step 2: Implement non-breaking signature**

Change analyzer signature to:

```python
def analyze(self, frame, roi_hints=None):
```

Implementation rule:

- `roi_hints is None`: existing full-frame behavior.
- `roi_hints == []`: return zero cards with ROI diagnostics.
- non-empty `roi_hints`: crop each ROI, analyze locally, translate card coordinates back to table coordinates.

- [ ] **Step 3: Run targeted tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```powershell
git add app_cv/tarotvision/snapshot_analyzer.py app_cv/tests/test_snapshot_analyzer.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: support roi snapshot analysis"
```

---

## Task 5: TableState Event Updates

**Lane:** Green
**Cel:** rozpoznanie ma aktualizować stan stołu, a nie zastępować cały layout od zera.

**Files:**

- Modify: `app_cv/tarotvision/table_state.py`
- Modify: `app_cv/tests/test_table_state.py`

- [ ] **Step 1: Add tests**

Add tests for:

```python
state.upsert_locked("Gilded_01", x=0.2, y=0.4, angle=0.0, confidence=0.91, frame_index=1)
state.remove_cards_intersecting_bbox((100, 100, 80, 120), coordinate_space="image")
state.mark_cards_intersecting_bbox_needs_reverify((100, 100, 80, 120), reason="moved_or_replaced")
state.to_layout_cards()
```

Expected:

- known card can be removed by ROI if its stored image bbox overlaps,
- moved/replaced card is not silently deleted,
- `to_layout_cards()` returns cards compatible with current payload shape.

- [ ] **Step 2: Implement event methods**

Extend `TrackedCard` with optional `bbox`:

```python
bbox: tuple[int, int, int, int] | None = None
```

Add:

```python
def upsert_locked(..., bbox=None):
    ...

def remove_cards_intersecting_bbox(self, bbox, min_iou=0.10):
    ...

def mark_cards_intersecting_bbox_needs_reverify(self, bbox, reason, min_iou=0.10):
    ...

def to_layout_cards(self):
    ...
```

- [ ] **Step 3: Run tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_table_state -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```powershell
git add app_cv/tarotvision/table_state.py app_cv/tests/test_table_state.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: update table state from change events"
```

---

## Task 6: StateFirstDiffPipeline Skeleton

**Lane:** Yellow
**Cel:** zbudować nowy pipeline na mockach bez zmiany domyślnego runtime.

**Files:**

- Create: `app_cv/tarotvision/pipelines/state_first_diff.py`
- Create: `app_cv/tests/test_state_first_diff_pipeline.py`
- Modify: `app_cv/tarotvision/pipelines/__init__.py`

- [x] **Step 1: Add pipeline tests**

Create tests for these cases:

```text
no empty reference -> status says waiting_for_empty_reference, no analyzer call
empty reference seeded -> first stable current can be diffed
added ROI -> analyzer receives only added ROI
removed ROI -> table state removes matching card, analyzer not required
noise_or_lighting -> keep previous state, discard current
global_shift -> keep previous state, discard current, resync recommended
```

- [x] **Step 2: Implement minimal pipeline**

The pipeline constructor must accept:

```python
SnapshotSessionStore
ChangeDetector
SnapshotAnalyzer
TableState
SnapshotGate
StatusStore
TableCalibration
RuntimeMetrics
```

Processing rule:

```text
motion gate says stable -> choose best current snapshot -> warp if possible -> store current
if not ready_for_diff -> hold
detect changes
if global_shift -> discard current
if added/moved -> analyze ROI
if removed -> update TableState
publish TableState full layout
commit current only after accepted state update
```

- [x] **Step 3: Export pipeline**

Modify `app_cv/tarotvision/pipelines/__init__.py`:

```python
from tarotvision.pipelines.state_first_diff import StateFirstDiffPipeline

__all__ = [
    "VisionPipeline",
    "SnapshotFirstPipeline",
    "StateFirstDiffPipeline",
]
```

- [x] **Step 4: Run tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_state_first_diff_pipeline app_cv.tests.test_pipelines_contract -v
```

Expected: PASS.

- [x] **Step 5: Commit**

Run:

```powershell
git add app_cv/tarotvision/pipelines/state_first_diff.py app_cv/tarotvision/pipelines/__init__.py app_cv/tests/test_state_first_diff_pipeline.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: add state-first diff pipeline skeleton"
```

---

## Task 7: Session Commands and Runtime Wiring

**Lane:** Yellow
**Cel:** podłączyć pipeline tylko za flagą, bez usuwania obecnego `SnapshotFirstPipeline`.

**Files:**

- Modify: `app_cv/tarotvision/tuning_protocol.py`
- Modify: `app_cv/tests/test_tuning_protocol.py`
- Modify: `app_cv/main.py`
- Modify: `app_cv/tests/test_main_static_audit.py` if needed

- [x] **Step 1: Add protocol tests**

Add commands:

```json
{"type":"session_start"}
{"type":"session_capture_empty_reference"}
{"type":"session_end"}
{"type":"session_resync_table"}
```

Expected parser result:

```python
ControlMessage(type="session_start")
```

- [x] **Step 2: Wire runtime flag**

In `main.py`, use:

```python
PIPELINE_MODE = os.environ.get("TAROTVISION_PIPELINE", "snapshot_first")
```

Instantiate:

```python
if PIPELINE_MODE == "state_first_diff":
    vision_pipeline = StateFirstDiffPipeline(...)
else:
    vision_pipeline = snapshot_pipeline
```

Keep default as `snapshot_first` until physical smoke approves state-first.

- [x] **Step 3: Lock empty reference commands**

Rules:

```text
session_start -> activates SnapshotSessionStore
session_capture_empty_reference -> captures warped frame and locks reference
background_clear during active session -> warning, no clear
session_end -> unlocks session and allows reset
session_resync_table -> one-time SnapshotFirstPipeline full analysis or explicit current state rebuild
```

- [x] **Step 4: Run tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_tuning_protocol app_cv.tests.test_main_static_audit -v
python -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\state_first_diff.py
```

Expected: PASS.

- [x] **Step 5: Commit**

Run:

```powershell
git add app_cv/main.py app_cv/tarotvision/tuning_protocol.py app_cv/tests/test_tuning_protocol.py app_cv/tests/test_main_static_audit.py
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: wire state-first diff pipeline flag"
```

---

## Task 8: Studio Minimal Session Controls

**Lane:** Yellow
**Cel:** Operator ma jasne sterowanie sesją i widzi, czy pusta mata jest zablokowana.

**Files:**

- Modify: `app_ar/src/studio/studioConsole.js`
- Modify: `app_ar/src/studio/studioState.js` if needed
- Modify: `app_ar/src/transport/messageNormalizer.js` if needed

- [x] **Step 1: Add UI state fields**

Display:

```text
Session: inactive / waiting_empty / active / resync_required
Empty reference: missing / locked
Pipeline: snapshot_first / state_first_diff
```

- [x] **Step 2: Add buttons**

Commands:

```text
Start Session -> session_start
Capture Empty -> session_capture_empty_reference
Resync Table -> session_resync_table
End Session -> session_end
```

Disable `Capture Empty` after locked reference unless session is ended.

- [x] **Step 3: Build frontend**

Run:

```powershell
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: PASS.

- [x] **Step 4: Commit**

Run:

```powershell
git add app_ar/src/studio/studioConsole.js app_ar/src/studio/studioState.js app_ar/src/transport/messageNormalizer.js
git restore --staged app_ar/public/active_decks.json
git commit -m "feat: add state-first session controls"
```

---

## Task 9: Offline Fixture Verification

**Lane:** Green
**Cel:** sprawdzić nowy runtime detector na istniejących fixture bez kamery.

**Files:**

- Create: `tools/cv_detection_lab/runtime_state_first_smoke.py`
- Create: `app_cv/tests/test_runtime_state_first_fixture_contract.py`

- [x] **Step 1: Build smoke script**

Script inputs:

```text
empty analysis frame
one_card analysis frame
three_cards analysis frame
```

Pairs:

```text
empty -> empty
empty -> one_card
empty -> three_cards
one_card -> three_cards
one_card -> empty
three_cards -> empty
```

Expected counts:

```text
0, 1, 3, 2, 1, 3
```

- [x] **Step 2: Run script**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python tools/cv_detection_lab/runtime_state_first_smoke.py
```

Expected: PASS or a report naming the exact pair and count mismatch.

- [ ] **Step 3: Commit**

Run:

```powershell
git add tools/cv_detection_lab/runtime_state_first_smoke.py app_cv/tests/test_runtime_state_first_fixture_contract.py
git restore --staged app_ar/public/active_decks.json
git commit -m "test: add runtime state-first fixture smoke"
```

---

## Task 10: Physical Smoke and Rollout Decision

**Lane:** Red for default switch, Yellow for branch smoke
**Cel:** udowodnić, że nowy pipeline działa na Gilded przed przełączeniem domyślnego runtime.

**Files:**

- Create: `docs/operator/state_first_diff_mvp_smoke.md`
- Modify: `.ai/PROJECT_STATE.md` only after smoke result

- [x] **Step 1: Write smoke checklist**

Create `docs/operator/state_first_diff_mvp_smoke.md` with:

```markdown
# State-First Diff MVP Smoke

Branch:
HEAD:
Pipeline mode: state_first_diff
Physical deck: Gilded
Active deck: gilded

1. Start session
- session state:
- empty reference locked:

2. EMPTY -> EMPTY
- ROI count:
- false positives:
- result:

3. EMPTY -> ONE_CARD
- change kind:
- detected ROI:
- accepted card:
- TableState:
- result:

4. ONE_CARD -> THREE_CARDS
- added ROI count:
- existing card preserved:
- new cards accepted:
- result:

5. THREE_CARDS -> ONE_CARD
- removed ROI count:
- removed card:
- remaining cards preserved:
- result:

6. RESYNC
- full snapshot fallback:
- result:
```

- [x] **Step 2: Run backend tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest discover -s app_cv\tests -v
```

Expected: PASS.

- [x] **Step 3: Run frontend build**

Run:

```powershell
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: PASS.

- [ ] **Step 4: Physical smoke**

Status: `PHYSICAL_SMOKE_NOT_RUN` in this Codex run. Requires Operator camera session.

Run with:

```powershell
$env:TAROTVISION_PIPELINE="state_first_diff"
```

Expected:

- empty reference can be locked,
- no false cards on empty,
- adding one card creates one `added` ROI,
- removing a card creates one `removed` ROI,
- existing cards remain stable when unrelated regions change,
- no endless autotune loop is needed.

- [ ] **Step 5: Decision**

Current pre-smoke decision: `KEEP_SNAPSHOT_FIRST_DEFAULT_FOR_MVP`.

Possible outcomes:

```text
READY_TO_MAKE_STATE_FIRST_DEFAULT
STATE_FIRST_BRANCH_FIX_REQUIRED
KEEP_SNAPSHOT_FIRST_DEFAULT_FOR_MVP
```

- [x] **Step 6: Commit smoke docs**

Run:

```powershell
git add docs/operator/state_first_diff_mvp_smoke.md .ai/PROJECT_STATE.md
git restore --staged app_ar/public/active_decks.json
git commit -m "docs: record state-first diff smoke decision"
```

---

## Integration Rules

- Do not delete `SnapshotFirstPipeline` during this plan.
- Do not make `state_first_diff` default until physical smoke passes.
- Do not stage `app_ar/public/active_decks.json`.
- Do not extend autotune before the new session/diff contract exists.
- Do not add new dependencies.
- Do not recognize all cards on every stable snapshot unless running explicit resync.
- Do not clear locked empty reference during active recording session.

## Verification Matrix

Minimum before PR:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest app_cv.tests.test_snapshot_session_store app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_state_first_diff_pipeline -v
python -m unittest discover -s app_cv\tests -v
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
git diff -- app_ar/public/active_decks.json
```

Expected:

- targeted tests PASS,
- full backend tests PASS,
- frontend build PASS if Studio changed,
- `active_decks.json` remains unstaged local operator config.

## Final Acceptance Criteria

- Operator cannot enter active state-first session without locked empty reference.
- Runtime keeps at most `empty_reference`, `previous_snapshot`, `current_snapshot` in memory.
- Old current snapshot is dropped after commit/discard.
- `previous/current` diff finds ROI before any recognition.
- Empty reference is compared inside the same ROI to classify add/remove/move.
- Removed cards are not dependent on recognition from current frame.
- Existing unchanged cards are preserved from `TableState`.
- Full-table snapshot recognition is fallback/resync, not normal loop.
- MVP physical smoke Gilded documents PASS/FAIL for add and remove workflows.

## Session Status (2026-06-06, Codex)

Plan prepared from the clarified product direction:

- state-first diff is the intended main workflow,
- empty mat is a locked session reference,
- previous/current snapshots rotate continuously,
- empty reference is reused in the same ROI to classify removals,
- autotune is not the center of this implementation.

No production code was changed in this planning step.

Task 6 completed:

- added `StateFirstDiffPipeline` skeleton without changing default runtime wiring,
- added mock-based tests for empty-reference wait, added ROI analysis, removed ROI state update, noise discard and global-shift resync,
- exported `StateFirstDiffPipeline` while keeping `SnapshotFirstPipeline`.

Verification:

- `python -m unittest app_cv.tests.test_state_first_diff_pipeline app_cv.tests.test_pipelines_contract -v` => PASS.

Task 7 completed:

- added session control messages: `session_start`, `session_capture_empty_reference`, `session_end`, `session_resync_table`,
- wired `TAROTVISION_PIPELINE=state_first_diff` as an opt-in runtime flag while keeping `snapshot_first` as default,
- connected `SnapshotSessionStore` empty-reference locking and protected `background_clear` during active state-first sessions.

Verification:

- `python -m unittest app_cv.tests.test_tuning_protocol app_cv.tests.test_main_static_audit -v` => PASS,
- `python -m unittest app_cv.tests.test_state_first_diff_pipeline app_cv.tests.test_pipelines_contract -v` => PASS,
- `python -m py_compile app_cv\main.py app_cv\tarotvision\tuning_protocol.py app_cv\tarotvision\pipelines\state_first_diff.py app_cv\tests\test_tuning_protocol.py app_cv\tests\test_main_static_audit.py` => PASS,
- `TAROTVISION_TEST_MODE=1 python -c "import main; ..."` => PASS for default `SnapshotFirstPipeline`,
- `TAROTVISION_TEST_MODE=1 TAROTVISION_PIPELINE=state_first_diff python -c "import main; ..."` => PASS for `StateFirstDiffPipeline`.

Task 8 completed:

- added a Studio sidebar section for `state_first_diff` session status,
- added Operator buttons for `session_start`, `session_capture_empty_reference`, `session_resync_table`, `session_end`,
- reused existing `layout.source/state` payload fields; `studioState.js` and `messageNormalizer.js` did not need changes in this step.

Verification:

- `npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build` => PASS.

Task 9 completed:

- added `tools/cv_detection_lab/runtime_state_first_smoke.py`,
- added `app_cv/tests/test_runtime_state_first_fixture_contract.py`,
- smoke target: `logs/live_fixtures/event_first_current_debug_verified`.

Verification:

- `python -m unittest app_cv.tests.test_runtime_state_first_fixture_contract -v` => PASS,
- `python -m py_compile tools\cv_detection_lab\runtime_state_first_smoke.py app_cv\tests\test_runtime_state_first_fixture_contract.py` => PASS,
- `python tools\cv_detection_lab\runtime_state_first_smoke.py` => diagnostic report `FAIL`.

Current detector result on real fixture:

- `empty->empty`: PASS, actual 0 / expected 0,
- `empty->one_card`: PASS, actual 1 / expected 1,
- `empty->three_cards`: FAIL, actual 2 / expected 3,
- `one_card->three_cards`: FAIL, actual 4 / expected 2,
- `one_card->empty`: PASS, actual 1 / expected 1,
- `three_cards->empty`: FAIL, actual 2 / expected 3.

Conclusion: state-first diff is useful for add/remove one-card workflows, but multi-card ROI grouping still needs a follow-up before using three-card counts as an MVP gate.

Task 10 prepared:

- added `docs/operator/state_first_diff_mvp_smoke.md`,
- physical smoke was not run in this Codex environment,
- rollout decision remains `KEEP_SNAPSHOT_FIRST_DEFAULT_FOR_MVP` before Operator camera validation.

Verification:

- `python -m unittest discover -s app_cv\tests -v` => PASS, 463 tests,
- `npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build` => PASS.

Follow-up implementation (2026-06-06, Codex):

- added per-card `bbox` to `SnapshotAnalyzer` accepted card payloads,
- verified `StateFirstDiffPipeline` stores individual card bboxes when one compound ROI contains multiple accepted cards,
- this supports later remove/update events even when the diff detector returns a broad changed region.

Verification:

- `python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_state_first_diff_pipeline -v` => PASS,
- `python -m py_compile app_cv\tarotvision\snapshot_analyzer.py app_cv\tests\test_snapshot_analyzer.py app_cv\tests\test_state_first_diff_pipeline.py` => PASS,
- `python tools\cv_detection_lab\runtime_state_first_smoke.py` => still diagnostic `FAIL` for multi-card ROI counts.

Follow-up implementation (2026-06-06, Codex):

- changed `StateFirstDiffPipeline` so `added` regions take priority over `moved_or_replaced` slivers when both are present,
- `moved_or_replaced` regions now mark intersecting existing cards as `needs_reverify` instead of spamming the analyzer during card-add workflows,
- updated runtime smoke to report both raw detector region count and runtime-effective analysis ROI count.

Verification:

- `python -m unittest app_cv.tests.test_runtime_state_first_fixture_contract app_cv.tests.test_state_first_diff_pipeline -v` => PASS,
- `python -m py_compile tools\cv_detection_lab\runtime_state_first_smoke.py app_cv\tests\test_runtime_state_first_fixture_contract.py app_cv\tarotvision\pipelines\state_first_diff.py` => PASS,
- `python tools\cv_detection_lab\runtime_state_first_smoke.py` => PASS at runtime-effective ROI level.

Remaining blocker:

- raw `ChangeDetector` region counts still show merged/split diagnostics on `three_cards` fixture pairs, but runtime-effective ROI gating is now PASS. Do not make `state_first_diff` default until physical Gilded smoke validates add/remove behavior through Studio.
