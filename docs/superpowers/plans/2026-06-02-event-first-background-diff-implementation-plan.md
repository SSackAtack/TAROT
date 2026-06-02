# Event-First Background Diff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Przebudowac snapshot-first CV tak, aby po kalibracji pustej maty wykrywac zdarzenia zmian (`added`, `removed`, `moved`) przez porownanie `current_snapshot` z `empty_reference` i `previous_stable_snapshot`, a dopiero potem uruchamiac kosztowne wykrywanie i rozpoznawanie kart na ograniczonych ROI.

**Architecture:** System ma przejsc z globalnego "szukaj kart wszedzie" na hybryde: `empty_reference` jako baza absolutna, `previous_stable_snapshot` jako baza zdarzen po ruchu oraz `card_state_map` jako pamiec logiczna ukladu. `BackgroundModel` zostanie rozbudowany do modelu referencyjnego, nowy modul `ChangeDetector` bedzie produkowal regiony zmian, a `SnapshotAnalyzer` bedzie mogl przyjmowac ROI hints i ograniczac detekcje do sensownych obszarow.

**Tech Stack:** Python 3.13, OpenCV, NumPy, unittest, istniejący `SnapshotFirstPipeline`, `SnapshotAnalyzer`, `BackgroundModel`, WebSocket Studio commands.

---

## Stan Aktualny

- `app_cv/tarotvision/background_model.py` przechowuje pojedynczy obraz szary i potrafi zwrocic maske roznic przez `foreground_mask(frame, threshold=18)`.
- `app_cv/tarotvision/card_detection_profiles.py` ma profil `background_diff`, ale nadal detekcja jest glownie globalna i profil tła nie jest zdarzeniowym filtrem ROI.
- `app_cv/tarotvision/pipelines/snapshot_first.py` po stabilizacji pobiera snapshot, ewentualnie warpuje go przez ArUco, a potem wywoluje `snapshot_analyzer.analyze(analysis_frame)`.
- `app_cv/tarotvision/snapshot_analyzer.py` szuka quadow na calym obrazie przez `find_quads_with_debug(frame)`.
- Auto Tune po ostatnich poprawkach potrafi wymusic `3/3` probek i zapisac `sample_collected` oraz `stage_completed`.
- Live obserwacja: etap `Pusta mata` zakonczyl sie `FAIL`, bo system wykryl false positives: `candidate_count` 1-2, `accepted_count` 1.

## Projekt Docelowy

### Referencje

1. `empty_reference`
   - Zapisany po etapie `Pusta mata`.
   - Najlepiej w przestrzeni sprostowanej przez ArUco (`warped_frame`), bo wtedy piksele sa porownywalne miedzy snapshotami.
   - Sluzy do odpowiedzi: "co nie jest mata?".

2. `previous_stable_snapshot`
   - Ostatni zaakceptowany stabilny snapshot po analizie.
   - Aktualizowany dopiero po zakonczeniu analizy i publikacji stanu.
   - Sluzy do odpowiedzi: "co zmienilo sie od ostatniego stabilnego stanu?".

3. `card_state_map`
   - Istniejaca pamiec logiczna to obecnie `last_snapshot_cards`.
   - W tej iteracji nie budujemy nowego trackera. Rozszerzamy tylko diagnostyke i ROI. Pelny tracker mozna zaplanowac pozniej.

### Zdarzenia

`ChangeDetector` ma klasyfikowac regiony zmian:

- `added_or_moved`: region zmienil sie wzgledem poprzedniego snapshotu i teraz rozni sie od pustej maty.
- `removed`: region zmienil sie wzgledem poprzedniego snapshotu i teraz jest podobny do pustej maty.
- `ignored_small`: obszar za maly, np. kurz, palec poza strefa, drobny refleks.
- `ignored_global_shift`: za duza czesc obrazu zmieniona, prawdopodobnie autoekspozycja, poruszenie kamery albo blad warp.

### Zasada Bezpieczenstwa

ROI hints maja ograniczac i priorytetyzowac detekcje, ale w pierwszej iteracji nie moga bezwarunkowo kasowac wszystkich kart ze stanu. Jesli detektor zmian zwroci `ignored_global_shift` albo brak wiarygodnych ROI przy istniejacych kartach, pipeline powinien zachowac poprzedni stan i dodac ostrzezenie operatora.

---

## Struktura Plikow

### Tworzone

- `app_cv/tarotvision/change_detection.py`
  - Nowe dataclassy: `ChangeRegion`, `ChangeDetectionResult`, `ChangeDetectorConfig`.
  - Funkcje: maska roznic, morfologia, kontury, filtr wielkosci, klasyfikacja `added_or_moved` vs `removed`.

- `app_cv/tests/test_change_detection.py`
  - Testy jednostkowe syntetycznych scen: karta dodana, karta zabrana, mala zmiana ignorowana, globalna zmiana jasnosci.

### Modyfikowane

- `app_cv/tarotvision/background_model.py`
  - Rozszerzenie modelu o `capture_many()`, `difference_mask()`, `changed_ratio()`, opcjonalne przechowywanie BGR/gray.

- `app_cv/tarotvision/snapshot_analyzer.py`
  - Dodanie parametru `roi_hints=None` w `analyze()`.
  - Ograniczenie detekcji do ROI przez crop + przesuniecie quadow do wspolrzednych pelnego obrazu.
  - Diagnostyka ROI: liczba ROI, rozmiary, tryb `roi_limited`.

- `app_cv/tarotvision/pipelines/snapshot_first.py`
  - Utrzymanie `previous_stable_snapshot`.
  - Po wybraniu `analysis_frame`: uruchomienie `ChangeDetector`.
  - Przekazanie ROI do `SnapshotAnalyzer`.
  - Aktualizacja `previous_stable_snapshot` tylko po zakonczonej analizie.
  - Dodanie metryk runtime: `change_region_count`, `change_mask_ratio`, `change_global_shift`, `change_removed_count`, `change_added_count`.

- `app_cv/main.py`
  - Utworzenie `ChangeDetector`.
  - Podlaczenie go do `SnapshotFirstPipeline`.
  - Przy `background_capture` / etapie `Pusta mata` zapis pustej maty jako referencji.

- `app_cv/tests/test_background_model.py`
  - Testy multi-frame empty reference i mask roznic.

- `app_cv/tests/test_snapshot_analyzer.py`
  - Testy detekcji ograniczonej do ROI.

- `app_cv/tests/test_pipelines_contract.py`
  - Testy integracyjne pipeline: ROI po zmianie, brak ROI przy pustym obrazie, update previous stable.

- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`
  - Aktualizacja po wykonaniu.

---

## Task 1: Rozszerz BackgroundModel o stabilna referencje pustej maty

**Files:**
- Modify: `app_cv/tarotvision/background_model.py`
- Test: `app_cv/tests/test_background_model.py`

- [ ] **Step 1: Write failing tests**

Dodaj do `app_cv/tests/test_background_model.py`:

```python
    def test_capture_many_uses_median_reference(self):
        base = np.zeros((40, 60, 3), dtype=np.uint8)
        base[:, :] = (20, 55, 35)
        noisy = base.copy()
        noisy[5, 5] = (255, 255, 255)
        darker = base.copy()
        darker[:, :] = (18, 53, 33)

        model = BackgroundModel()
        model.capture_many([base, noisy, darker])

        mask = model.foreground_mask(base, threshold=20)
        self.assertEqual(int(np.count_nonzero(mask)), 0)

    def test_changed_ratio_reports_foreground_fraction(self):
        empty = np.zeros((100, 100, 3), dtype=np.uint8)
        frame = empty.copy()
        cv2.rectangle(frame, (30, 20), (70, 80), (255, 255, 255), -1)

        model = BackgroundModel()
        model.capture(empty)

        ratio = model.changed_ratio(frame, threshold=20)

        self.assertGreater(ratio, 0.20)
        self.assertLess(ratio, 0.30)
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model -v
```

Expected: FAIL because `capture_many` and `changed_ratio` do not exist.

- [ ] **Step 3: Implement minimal code**

Update `app_cv/tarotvision/background_model.py`:

```python
class BackgroundModel:
    def __init__(self):
        self._gray_background = None

    @property
    def active(self):
        return self._gray_background is not None

    def capture(self, frame):
        self._gray_background = _to_gray(frame).copy()

    def capture_many(self, frames):
        gray_frames = [_to_gray(frame) for frame in frames if frame is not None]
        if not gray_frames:
            self.clear()
            return
        shape = gray_frames[0].shape
        aligned = [frame for frame in gray_frames if frame.shape == shape]
        if not aligned:
            self.clear()
            return
        stacked = np.stack(aligned, axis=0)
        self._gray_background = np.median(stacked, axis=0).astype(np.uint8)

    def clear(self):
        self._gray_background = None

    def foreground_mask(self, frame, threshold=18):
        if self._gray_background is None:
            return None
        gray = _to_gray(frame)
        if gray.shape != self._gray_background.shape:
            return None
        diff = cv2.absdiff(self._gray_background, gray)
        _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return mask

    def changed_ratio(self, frame, threshold=18):
        mask = self.foreground_mask(frame, threshold=threshold)
        if mask is None or mask.size == 0:
            return 0.0
        return float(np.count_nonzero(mask)) / float(mask.size)


def _to_gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/background_model.py app_cv/tests/test_background_model.py
git commit -m "feat: ustabilizuj model pustej maty"
```

---

## Task 2: Dodaj ChangeDetector dla roznic miedzy snapshotami

**Files:**
- Create: `app_cv/tarotvision/change_detection.py`
- Test: `app_cv/tests/test_change_detection.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_change_detection.py`:

```python
import unittest

import cv2
import numpy as np

from tarotvision.background_model import BackgroundModel
from tarotvision.change_detection import ChangeDetector, ChangeDetectorConfig


class ChangeDetectorTest(unittest.TestCase):
    def test_detects_added_card_sized_region(self):
        empty = np.zeros((200, 300, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        previous = empty.copy()
        current = empty.copy()
        cv2.rectangle(current, (120, 50), (180, 150), (90, 90, 85), -1)

        background = BackgroundModel()
        background.capture(empty)
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(previous, current, empty_reference=background)

        self.assertFalse(result.global_shift)
        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "added_or_moved")

    def test_detects_removed_card_sized_region(self):
        empty = np.zeros((200, 300, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        previous = empty.copy()
        cv2.rectangle(previous, (120, 50), (180, 150), (90, 90, 85), -1)
        current = empty.copy()

        background = BackgroundModel()
        background.capture(empty)
        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03, max_area_ratio=0.25))

        result = detector.detect(previous, current, empty_reference=background)

        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.regions[0].kind, "removed")

    def test_ignores_tiny_change(self):
        empty = np.zeros((200, 300, 3), dtype=np.uint8)
        previous = empty.copy()
        current = empty.copy()
        cv2.circle(current, (20, 20), 3, (255, 255, 255), -1)

        detector = ChangeDetector(ChangeDetectorConfig(min_area_ratio=0.03))

        result = detector.detect(previous, current)

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

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_change_detection -v
```

Expected: FAIL because `tarotvision.change_detection` does not exist.

- [ ] **Step 3: Implement ChangeDetector**

Create `app_cv/tarotvision/change_detection.py`:

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


@dataclass(frozen=True)
class ChangeRegion:
    bbox: tuple[int, int, int, int]
    area_ratio: float
    kind: str


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

        raw_mask = _difference_mask(previous_gray, current_gray, self.config.threshold)
        mask_ratio = _mask_ratio(raw_mask)
        if mask_ratio >= self.config.global_shift_ratio:
            return ChangeDetectionResult([], mask_ratio, True, 0, 0)

        contours, _ = cv2.findContours(raw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        frame_area = float(raw_mask.shape[0] * raw_mask.shape[1])
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
            bbox = _pad_bbox((x, y, w, h), raw_mask.shape[1], raw_mask.shape[0], self.config.padding_px)
            regions.append(ChangeRegion(
                bbox=bbox,
                area_ratio=area_ratio,
                kind=_classify_region(current_frame, bbox, empty_reference),
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
    _, mask = cv2.threshold(diff, int(threshold), 255, cv2.THRESH_BINARY)
    kernel = np.ones((7, 7), dtype=np.uint8)
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


def _classify_region(current_frame, bbox, empty_reference):
    if empty_reference is None or not getattr(empty_reference, "active", False):
        return "added_or_moved"
    x, y, w, h = bbox
    mask = empty_reference.foreground_mask(current_frame)
    if mask is None:
        return "added_or_moved"
    roi = mask[y:y + h, x:x + w]
    if roi.size == 0:
        return "added_or_moved"
    foreground_ratio = float(np.count_nonzero(roi)) / float(roi.size)
    return "added_or_moved" if foreground_ratio >= 0.10 else "removed"
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_change_detection -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/change_detection.py app_cv/tests/test_change_detection.py
git commit -m "feat: dodaj detekcje zmian miedzy snapshotami"
```

---

## Task 3: Dodaj ROI hints do SnapshotAnalyzer

**Files:**
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Test: `app_cv/tests/test_snapshot_analyzer.py`

- [ ] **Step 1: Write failing test**

Add to `app_cv/tests/test_snapshot_analyzer.py`:

```python
    def test_analyze_limits_detection_to_roi_hints(self):
        frame = np.zeros((200, 300, 3), dtype=np.uint8)
        cv2.rectangle(frame, (20, 40), (80, 140), (255, 255, 255), -1)
        cv2.rectangle(frame, (190, 40), (250, 140), (255, 255, 255), -1)

        def find_quads(crop):
            return [np.array([[10, 10], [50, 10], [50, 90], [10, 90]], dtype=np.float32)]

        analyzer = SnapshotAnalyzer(
            find_quads=find_quads,
            recognize_crop=lambda crop: {"name": "Gilded_01", "confidence": 0.9},
            validate_candidate_crop=None,
        )

        result = analyzer.analyze(frame, roi_hints=[(180, 30, 90, 130)])

        self.assertEqual(result.card_count, 1)
        self.assertGreater(result.cards[0]["x"], 0)
        self.assertTrue(result.diagnostics["roi_limited"])
        self.assertEqual(result.diagnostics["roi_count"], 1)
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: FAIL because `analyze()` does not accept `roi_hints`.

- [ ] **Step 3: Implement ROI support**

Modify `SnapshotAnalyzer.analyze` signature:

```python
    def analyze(self, frame, roi_hints=None):
```

Add diagnostics:

```python
            "roi_limited": bool(roi_hints),
            "roi_count": len(roi_hints or []),
```

Replace quad acquisition block with:

```python
        if roi_hints:
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

Add helper:

```python
def _clamp_bbox(bbox, frame_width, frame_height):
    x, y, w, h = [int(v) for v in bbox]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(frame_width, x + max(0, w))
    y2 = min(frame_height, y + max(0, h))
    return x1, y1, max(0, x2 - x1), max(0, y2 - y1)
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/snapshot_analyzer.py app_cv/tests/test_snapshot_analyzer.py
git commit -m "feat: ogranicz analize snapshotu do regionow zmian"
```

---

## Task 4: Podlacz ChangeDetector do SnapshotFirstPipeline

**Files:**
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Test: `app_cv/tests/test_pipelines_contract.py`

- [ ] **Step 1: Write failing test**

Add to `app_cv/tests/test_pipelines_contract.py`:

```python
    def test_snapshot_pipeline_passes_change_rois_to_analyzer(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        analyzed = MagicMock()
        analyzed.card_count = 0
        analyzed.cards = []
        analyzed.diagnostics = {}
        snapshot_analyzer.analyze.return_value = analyzed

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        change_detector = MagicMock()
        change_region = MagicMock()
        change_region.kind = "added_or_moved"
        change_region.bbox = (40, 30, 80, 120)
        change_detector.detect.return_value.regions = [change_region]
        change_detector.detect.return_value.mask_nonzero_ratio = 0.08
        change_detector.detect.return_value.global_shift = False
        change_detector.detect.return_value.ignored_small_count = 0
        change_detector.detect.return_value.ignored_large_count = 0

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            change_detector=change_detector,
        )
        pipeline.previous_stable_snapshot = self._readable_frame()[0:200, 0:300]

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame()[0:200, 0:300],
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_called_once()
        self.assertEqual(snapshot_analyzer.analyze.call_args.kwargs["roi_hints"], [(40, 30, 80, 120)])
        runtime_metrics.add.assert_any_call("change_region_count", 1)
        runtime_metrics.add.assert_any_call("change_mask_ratio", 0.08)
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_passes_change_rois_to_analyzer -v
```

Expected: FAIL because `SnapshotFirstPipeline.__init__` does not accept `change_detector`.

- [ ] **Step 3: Implement pipeline wiring**

Modify `SnapshotFirstPipeline.__init__`:

```python
        change_detector=None,
        background_model=None,
```

Store:

```python
        self.change_detector = change_detector
        self.background_model = background_model
        self.previous_stable_snapshot = None
```

Before analyzer call in `process_frame`, after `analysis_frame` is prepared:

```python
                roi_hints = None
                change_result = None
                if self.change_detector is not None and self.previous_stable_snapshot is not None:
                    change_result = self.change_detector.detect(
                        self.previous_stable_snapshot,
                        analysis_frame,
                        empty_reference=self.background_model,
                    )
                    self.runtime_metrics.add("change_region_count", len(change_result.regions))
                    self.runtime_metrics.add("change_mask_ratio", change_result.mask_nonzero_ratio)
                    self.runtime_metrics.add("change_global_shift", 1 if change_result.global_shift else 0)
                    self.runtime_metrics.add(
                        "change_added_count",
                        sum(1 for region in change_result.regions if region.kind == "added_or_moved"),
                    )
                    self.runtime_metrics.add(
                        "change_removed_count",
                        sum(1 for region in change_result.regions if region.kind == "removed"),
                    )
                    if not change_result.global_shift:
                        roi_hints = [
                            region.bbox for region in change_result.regions
                            if region.kind == "added_or_moved"
                        ]
```

Replace:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame)
```

with:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints)
```

After `layout_snapshot.update(...)`, update previous stable:

```python
                self.previous_stable_snapshot = analysis_frame.copy()
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_pipelines_contract.py
git commit -m "feat: uzyj regionow zmian w snapshot-first"
```

---

## Task 5: Podlacz ChangeDetector w main.py i publikuj metryki operatora

**Files:**
- Modify: `app_cv/main.py`
- Test: `app_cv/tests/test_main_static_audit.py`

- [ ] **Step 1: Write failing static test**

Add to `app_cv/tests/test_main_static_audit.py`:

```python
    def test_main_wires_change_detector_into_snapshot_pipeline(self):
        source = self._read_main_source()

        self.assertIn("from tarotvision.change_detection import ChangeDetector", source)
        self.assertIn("change_detector = ChangeDetector", source)
        self.assertIn("change_detector=change_detector", source)
        self.assertIn("background_model=background_model", source)
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit.TestMainStaticAudit.test_main_wires_change_detector_into_snapshot_pipeline -v
```

Expected: FAIL because `ChangeDetector` is not imported/wired.

- [ ] **Step 3: Implement main.py wiring**

In `app_cv/main.py`, add import:

```python
from tarotvision.change_detection import ChangeDetector
```

Near `background_model = BackgroundModel()` add:

```python
change_detector = ChangeDetector()
```

In `SnapshotFirstPipeline(...)` constructor call add:

```python
    change_detector=change_detector,
    background_model=background_model,
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/main.py app_cv/tests/test_main_static_audit.py
git commit -m "feat: podlacz detektor zmian do glownego pipeline"
```

---

## Task 6: Uzyj pustej maty z Auto Tune jako empty_reference

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Test: `app_cv/tests/test_main_static_audit.py`
- Test: `app_cv/tests/test_pipelines_contract.py`

- [ ] **Step 1: Write failing tests**

Add static test:

```python
    def test_autotune_empty_stage_captures_background_reference(self):
        source = self._read_main_source()
        autotune_start_index = source.index('if message.type == "autotune_start"')
        autotune_start_block = source[
            autotune_start_index:source.index('if message.type == "autotune_calibrate"')
        ]

        self.assertIn('message.scenario == "empty"', autotune_start_block)
        self.assertIn("background_model.clear()", autotune_start_block)
```

Add pipeline contract test:

```python
    def test_snapshot_pipeline_captures_empty_reference_after_empty_autotune_pass(self):
        # Use a MagicMock background_model and autotune_sample_recorder returning capture_empty_reference.
        # Expected: background_model.capture(analysis_frame) called once after analyzing empty snapshot.
```

Implement this test fully like existing pipeline tests:

```python
        background_model = MagicMock()
        recorder = MagicMock(return_value={"capture_empty_reference": True})
        ...
        pipeline = SnapshotFirstPipeline(..., background_model=background_model, autotune_sample_recorder=recorder)
        ...
        background_model.capture.assert_called_once()
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Expected: FAIL for missing clear/capture behavior.

- [ ] **Step 3: Implement capture signal**

In `record_autotune_sample_from_snapshot(sample)` add:

```python
    if scenario == "empty" and autotune_session.ready_to_score():
        result = autotune_session.stage_result()
        if result["state"] == "PASS":
            return {"capture_empty_reference": True}
```

But preserve existing `stage_completed` logging. The final shape should be:

```python
    if autotune_session.ready_to_score():
        result = autotune_session.stage_result()
        write_autotune_log("stage_completed")
        add_operator_warning(...)
        if scenario == "empty" and result["state"] == "PASS":
            return {"capture_empty_reference": True}
        return None
```

In `autotune_start` block:

```python
        if message.scenario == "empty":
            background_model.clear()
```

In pipeline after recorder result:

```python
                if (
                        isinstance(autotune_recorder_result, dict)
                        and autotune_recorder_result.get("capture_empty_reference")
                        and self.background_model is not None):
                    self.background_model.capture(analysis_frame)
                    self.runtime_metrics.add("background_reference_captured", 1)
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/main.py app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_main_static_audit.py app_cv/tests/test_pipelines_contract.py
git commit -m "feat: zapisz pusta mate jako referencje tła"
```

---

## Task 7: Dodaj diagnostyke zmian do CV Explain i logow

**Files:**
- Modify: `app_cv/tarotvision/operator_explainability.py`
- Test: `app_cv/tests/test_operator_explainability.py`
- Modify: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`

- [ ] **Step 1: Write failing explainability test**

Add to `app_cv/tests/test_operator_explainability.py`:

```python
    def test_change_detector_explains_false_positive_source(self):
        explain = build_cv_explainability(
            cards=[],
            metrics={
                "change_region_count": 0,
                "change_mask_ratio": 0.0,
                "snapshot_quads_found": 2,
            },
            runtime={"table": {"calibrated": True, "marker_ids": [10, 11, 12, 13]}},
            layout={"state": "holding_last_good", "card_count": 0},
            warnings=[],
        )

        messages = " ".join(step["message"] for step in explain["steps"])
        self.assertIn("brak regionow zmian", messages.lower())
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability -v
```

Expected: FAIL because explainability does not mention change regions.

- [ ] **Step 3: Implement explainability message**

In `operator_explainability.py`, add a step after ArUco/snapshot step:

```python
def _change_detection_step(metrics):
    region_count = int(metrics.get("change_region_count", 0) or 0)
    mask_ratio = float(metrics.get("change_mask_ratio", 0.0) or 0.0)
    global_shift = bool(metrics.get("change_global_shift", 0) or 0)
    if global_shift:
        return _step("warn", "Zmiana", "global", "Wykryto globalna zmiane obrazu: sprawdz swiatlo, ekspozycje albo stabilnosc kamery.")
    if region_count == 0:
        return _step("warn", "Zmiana", "0 ROI", "Brak regionow zmian; false positives z detektora kart powinny zostac odrzucone lub wymagaja kalibracji pustej maty.")
    return _step("ok", "Zmiana", str(region_count), f"Wykryto regiony zmian, mask ratio={mask_ratio:.3f}.")
```

Use the local helper names actually present in the file. Do not invent `_step` if the file uses another helper; adapt to existing pattern.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_operator_explainability -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/operator_explainability.py app_cv/tests/test_operator_explainability.py
git commit -m "feat: wyjasnij regiony zmian w cv explain"
```

---

## Task 8: Pelna weryfikacja i live smoke

**Files:**
- Modify: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`
- Modify: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`
- Modify: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`

- [ ] **Step 1: Run targeted tests**

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model app_cv.tests.test_change_detection app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability -v
```

Expected: PASS.

- [ ] **Step 2: Run full backend suite**

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest discover -s app_cv\tests -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

```powershell
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: PASS. Existing Vite warnings about large chunk and ineffective dynamic import are acceptable if unchanged.

- [ ] **Step 4: Live smoke with camera**

Start or restart Studio backend/frontend, then in `http://127.0.0.1:5174/?studio=1` or launcher URL:

1. Ensure ArUco table is calibrated.
2. Remove all cards.
3. Click `Pusta mata`.
4. Wait for `3/3`.
5. Expected: `PASS` if no false positives; if `FAIL`, logs must show exact false positives and change metrics.
6. Put one card.
7. Confirm motion triggers snapshot.
8. Expected: `change_region_count >= 1`, `change_added_count >= 1`, recognition runs in ROI.
9. Remove the card.
10. Expected: `change_removed_count >= 1`, state eventually clears card.

- [ ] **Step 5: Inspect logs**

Check latest files:

```powershell
Get-ChildItem logs\autotune_sessions -Filter *.json | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime,Length
Get-Content logs\cv_metrics.jsonl -Tail 10
```

Expected metrics in `cv_metrics.jsonl`:

```text
change_region_count
change_mask_ratio
change_global_shift
change_added_count
change_removed_count
```

- [ ] **Step 6: Update docs**

Append Polish session status to:

- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`

Required content:

```markdown
## Session Status (2026-06-02 Event-first background diff)

Stan aktualny: <PASS/YELLOW/RED live result>.
Co zostalo zrobione: wdrozono empty_reference, previous_stable_snapshot i ROI z regionow zmian.
Kolejne kroki: <co zostaje>.
```

- [ ] **Step 7: Commit**

```powershell
git add .ai/tasks/TASK-CV-AUTOTUNE-LIVE-001 docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md
git commit -m "docs: zapisz weryfikacje event-first background diff"
```

---

## Kryteria Akceptacji

- `Pusta mata` nie wisi na `0/3`; komplet probek powstaje deterministycznie.
- Po udanym `Pusta mata` system ma aktywny `empty_reference`.
- Po ruchu system porownuje `current_snapshot` z `previous_stable_snapshot`.
- Regiony zmian sa filtrowane po rozmiarze; drobne zmiany nie uruchamiaja rozpoznawania kart.
- `SnapshotAnalyzer` przyjmuje `roi_hints` i ogranicza detekcje do tych obszarow.
- Runtime metrics publikuja `change_region_count`, `change_mask_ratio`, `change_global_shift`, `change_added_count`, `change_removed_count`.
- CV Explain pokazuje, czy problem lezy w braku regionow zmian, globalnej zmianie obrazu czy false positives detektora.
- Pelny backend test suite przechodzi.
- Frontend build przechodzi.
- Live smoke pokazuje w logach, dlaczego etap `empty` jest PASS albo FAIL.

## Ryzyka

- Autoekspozycja kamery moze generowac globalne roznice. Mitigacja: `global_shift_ratio` i ostrzezenie zamiast publikacji nowego stanu.
- Zly warp ArUco moze przesuwac cala mate. Mitigacja: porownywac tylko gdy `table.calibrated == True`; inaczej fallback do globalnej detekcji z ostrzezeniem.
- Karta przesunieta o kilka pikseli moze dac obwodke zamiast pelnego regionu. Mitigacja: morfologia close + padding ROI.
- Karta lezaca od poczatku przed capture pustej maty zostanie uznana za tlo. Mitigacja: `Pusta mata PASS` wymaga `candidate_count=0` i `accepted_count=0`; UI musi mowic operatorowi, zeby zdjal wszystkie karty.
- Zbyt agresywne ROI moze ukryc prawdziwa karte. Mitigacja w pierwszej iteracji: ROI ogranicza tylko przy wiarygodnych regionach; przy `global_shift` albo braku referencji fallback do dotychczasowej analizy.

## Kolejnosc Integracji

1. Najpierw stabilny `BackgroundModel`.
2. Potem niezalezny `ChangeDetector`.
3. Potem ROI hints w `SnapshotAnalyzer`.
4. Potem wiring w `SnapshotFirstPipeline`.
5. Potem `main.py` i Auto Tune empty reference.
6. Na koncu CV Explain, logi i live smoke.

Ta kolejnosc jest celowa: najpierw budujemy czyste, testowalne moduly bez kamery, dopiero pozniej podpinamy je do runtime.

