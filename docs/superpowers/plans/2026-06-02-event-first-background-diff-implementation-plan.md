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

## Architectural Clarification: Autotune vs Runtime

Autotune / Calibration tworzy i waliduje referencje.
Runtime / Recording Pipeline używa referencji do pracy podczas sesji.

Autotuning nie jest wlasciwym pipeline nagraniowym. Jest procedura przygotowania sesji: wybor aktywnej talii, sprawdzenie kamery i swiatla, sprawdzenie ArUco, zebranie pustej maty, utworzenie `empty_reference`, test 1 karty, test 3 kart i zapis profilu sesji. Probki autotuningu nie powinny byc mieszane z roboczym stanem sesji nagraniowej.

Runtime / Recording Pipeline dziala podczas wlasciwego nagrania. Czeka na ruch przez motion gate, robi snapshot po ustaniu ruchu, warpuje go do przestrzeni maty, porownuje `current_snapshot` z `previous_stable_snapshot` i `empty_reference`, klasyfikuje zmiany, przekazuje ROI do `SnapshotAnalyzer`, rozpoznaje karte przez ORB tylko w ROI, aktualizuje stan kart i publikuje wynik do Studio / AR.

Po udanej kalibracji `empty_reference` globalne szukanie kart na calej macie nie jest glowna sciezka runtime. Global detection moze pozostac tylko fallbackiem diagnostycznym albo trybem awaryjnym, gdy nie ma aktywnej referencji pustej maty.

## Runtime Assumptions

- Nagrania odbywaja sie w kontrolowanym pomieszczeniu.
- Zrodlo swiatla jest stale.
- Kamera ma docelowo wylaczone auto focus / auto exposure / auto white balance, jesli sterownik na to pozwala.
- Kamera i mata nie zmieniaja pozycji w trakcie sesji.
- Po ustaniu ruchu znaczaca zmiana miedzy stabilnymi snapshotami oznacza dodanie, usuniecie albo przesuniecie karty.
- Reka i cien reki nie sa normalnym wejsciem do CV, bo motion gate ma opoznic analize do momentu stabilizacji sceny.
- Glownej sciezki runtime nie projektujemy pod losowe pojawianie sie obcych ksztaltow lub nowych odblaskow na pustej macie. Takie przypadki sa obslugiwane jako ostrzezenia awaryjne, nie jako centralne zalozenie architektury.

## Empty Reference Bootstrap

Pierwsze utworzenie `empty_reference` nie moze zalezec od starego wyniku globalnej detekcji kart. Obecny problem polega wlasnie na tym, ze stara detekcja potrafi widziec false positives na pustej macie.

Docelowa sekwencja:

1. Operator uruchamia etap `Pusta mata`.
2. System zbiera 3-5 stabilnych snapshotow pustej maty po motion gate / manualnym request sample.
3. System tworzy median `empty_reference` z tych snapshotow.
4. Dopiero po utworzeniu referencji system wykonuje walidacje, czy pusta mata jest stabilna i nie generuje regionow zmian.
5. Jezeli walidacja przejdzie, profil sesji moze uzyc tej referencji w runtime.
6. Jezeli walidacja nie przejdzie, Studio pokazuje operatorowi problem: niestabilne swiatlo, global shift, zbyt duzy szum albo false positive region.

## Safety Rules for Runtime

1. Jesli `empty_reference` jest aktywny i `ChangeDetector` nie zwraca `added_or_moved`, runtime nie powinien uruchamiac globalnej detekcji kart jako podstawowej sciezki.
2. Jesli `ChangeDetector` zwraca `ignored_global_shift`, pipeline powinien zachowac poprzedni dobry stan i pokazac ostrzezenie operatora.
3. Jesli nie ma `empty_reference`, system moze dzialac w fallback mode, ale Studio powinno jasno pokazac, ze pracuje bez pelnej kalibracji.
4. Jesli ROI jest zbyt male albo niepewne, pipeline powinien uzyc paddingu i diagnostyki, a nie publikowac przypadkowe karty.
5. ORB / recognition nadal pozostaje finalna walidacja tozsamosci karty.

## ROI Semantics

`SnapshotAnalyzer.analyze(frame, roi_hints=...)` musi rozrozniac trzy stany:

1. `roi_hints is None`
   - Event-first ROI filtering jest niedostepny albo celowo wylaczony.
   - Global detection moze dzialac jako fallback mode.
   - Studio / CV Explain powinno jasno pokazac, ze system pracuje bez pelnej kalibracji event-first.

2. `roi_hints == []`
   - Event-first mode jest aktywny, a `ChangeDetector` nie znalazl regionu `added_or_moved`.
   - Analyzer nie moze uruchamiac globalnej detekcji kart.
   - Analyzer powinien zwrocic zero candidate quads / zero kart, a diagnostyka powinna pokazac `roi_limited=True`, `roi_count=0`.
   - To jest normalny bezpieczny wynik dla stabilnej pustej maty.

3. `roi_hints == [...]`
   - Event-first mode jest aktywny, a `ChangeDetector` znalazl jeden albo wiecej regionow kandydackich.
   - Analyzer sprawdza wylacznie te regiony.
   - Global card detection nie moze dzialac poza wskazanymi ROI.

Obowiazkowy kontrakt bezpieczenstwa:

```text
empty_reference active + no added_or_moved ROI = no global scan and no new cards
```

## Projekt Docelowy

### Referencje

1. `empty_reference`
   - Tworzony przez Calibration / Autotune Mode po zebraniu 3-5 stabilnych snapshotow pustej maty.
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

### Podzial Trybow

Calibration / Autotune Mode:

- wybiera aktywna talie,
- sprawdza stabilnosc kamery i swiatla,
- sprawdza ArUco / obszar roboczy maty,
- zbiera kilka stabilnych snapshotow pustej maty,
- tworzy median `empty_reference`,
- waliduje test 1 karty,
- waliduje test 3 kart,
- dobiera podstawowe progi change detection, jesli bedzie to potrzebne,
- zapisuje profil sesji.

Runtime / Recording Pipeline:

- czeka na ruch przez motion gate,
- wykonuje snapshot dopiero po ustaniu ruchu,
- warpuje snapshot do przestrzeni maty, jesli ArUco jest skalibrowane,
- porownuje `current_snapshot` z `previous_stable_snapshot`,
- porownuje `current_snapshot` z `empty_reference`,
- klasyfikuje zmiany jako `added_or_moved`, `removed`, `ignored_small`, `ignored_global_shift`,
- przekazuje ROI tylko dla realnych regionow zmian do `SnapshotAnalyzer`,
- rozpoznaje karte przez ORB tylko w ROI,
- aktualizuje stan kart,
- publikuje stan do Studio / AR.

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

## Task 0: Clarify architecture

**Files:**
- Modify: `docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md`

- [x] **Step 1: Doprecyzuj Autotune vs Runtime**

W planie musi byc jawna zasada:

```text
Autotune / Calibration tworzy i waliduje referencje.
Runtime / Recording Pipeline używa referencji do pracy podczas sesji.
```

- [x] **Step 2: Dopisz runtime assumptions**

W planie musza byc zapisane kontrolowane zalozenia sesji: stale swiatlo, stabilna kamera/mata, docelowo wylaczone auto focus / auto exposure / auto white balance, motion gate czekajacy na ustanie ruchu.

- [x] **Step 3: Dopisz bootstrap empty_reference**

Pierwsze `empty_reference` musi powstac z 3-5 stabilnych snapshotow pustej maty przed walidacja, a nie na podstawie starej globalnej detekcji kart.

- [x] **Step 4: Dopisz safety rules**

Po udanej kalibracji global detection nie jest glowna sciezka runtime. Jest fallbackiem diagnostycznym albo trybem awaryjnym bez aktywnej referencji.

- [x] **Step 5: Zaktualizuj task breakdown**

Kolejnosc implementacji musi byc: Task 1 `Stable Empty Reference`, Task 2 `ChangeDetector`, Task 3 `SnapshotAnalyzer ROI Hints`, Task 4 `Runtime Pipeline Integration`, Task 5 `Autotune Creates Session Reference`, Task 6 `CV Explain and Diagnostics`, Task 7 `Live Smoke`.

---

## Task 1: Stable Empty Reference

**Files:**
- Modify: `app_cv/tarotvision/background_model.py`
- Test: `app_cv/tests/test_background_model.py`

- [x] **Step 1: Write failing tests**

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

- [x] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model -v
```

Expected: FAIL because `capture_many` and `changed_ratio` do not exist.

- [x] **Step 3: Implement minimal code**

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

- [x] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_background_model -v
```

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/background_model.py app_cv/tests/test_background_model.py
git commit -m "feat: ustabilizuj model pustej maty"
```

---

## Task 2: ChangeDetector

**Files:**
- Create: `app_cv/tarotvision/change_detection.py`
- Test: `app_cv/tests/test_change_detection.py`

- [x] **Step 1: Write failing tests**

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

- [x] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_change_detection -v
```

Expected: FAIL because `tarotvision.change_detection` does not exist.

- [x] **Step 3: Implement ChangeDetector**

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

- [x] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_change_detection -v
```

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/change_detection.py app_cv/tests/test_change_detection.py
git commit -m "feat: dodaj detekcje zmian miedzy snapshotami"
```

---

## Task 3: SnapshotAnalyzer ROI Hints

**Files:**
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Test: `app_cv/tests/test_snapshot_analyzer.py`

- [x] **Step 1: Write failing test**

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

- [x] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: FAIL because `analyze()` does not accept `roi_hints`.

- [x] **Step 3: Implement ROI support**

Modify `SnapshotAnalyzer.analyze` signature:

```python
    def analyze(self, frame, roi_hints=None):
```

Add diagnostics:

```python
            "roi_limited": roi_hints is not None,
            "roi_count": len(roi_hints or []),
```

Replace quad acquisition block with:

```python
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
roi_hints=[]      # event-first active, no global fallback
roi_hints=None    # global fallback allowed
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

- [x] **Step 4: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
```

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add app_cv/tarotvision/snapshot_analyzer.py app_cv/tests/test_snapshot_analyzer.py
git commit -m "feat: ogranicz analize snapshotu do regionow zmian"
```

---

## Task 4: Runtime Pipeline Integration

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Test: `app_cv/tests/test_main_static_audit.py`
- Test: `app_cv/tests/test_pipelines_contract.py`

- [x] **Step 1: Write failing test**

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

- [x] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_passes_change_rois_to_analyzer -v
```

Expected: FAIL because `SnapshotFirstPipeline.__init__` does not accept `change_detector`.

- [x] **Step 3: Add main.py static wiring test**

Add to `app_cv/tests/test_main_static_audit.py`:

```python
    def test_main_wires_change_detector_into_snapshot_pipeline(self):
        source = self._read_main_source()

        self.assertIn("from tarotvision.change_detection import ChangeDetector", source)
        self.assertIn("change_detector = ChangeDetector", source)
        self.assertIn("change_detector=change_detector", source)
        self.assertIn("background_model=background_model", source)
```

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit.TestMainStaticAudit.test_main_wires_change_detector_into_snapshot_pipeline -v
```

Expected: FAIL because `ChangeDetector` is not imported/wired.

- [x] **Step 4: Implement pipeline wiring**

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

If this list is empty, it must still be passed as `[]`, not converted back to `None`. This is correct:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints)
```

This is incorrect because it re-enables global detection when no event-first ROI exists:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints or None)
```

Replace:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame)
```

with:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints)
```

After the `layout_snapshot.update({ ... })` block that writes `layout_id`, `state`, `analysis_ms`, `quality_score` and `card_count`, update previous stable:

```python
                self.previous_stable_snapshot = analysis_frame.copy()
```

- [x] **Step 5: Implement main.py wiring**

In `app_cv/main.py`, add import:

```python
from tarotvision.change_detection import ChangeDetector
```

Near `background_model = BackgroundModel()` add:

```python
change_detector = ChangeDetector()
```

In the existing `SnapshotFirstPipeline(` constructor call in `app_cv/main.py`, add:

```python
    change_detector=change_detector,
    background_model=background_model,
```

- [ ] **Step 6: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_pipelines_contract app_cv.tests.test_main_static_audit -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add app_cv/main.py app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_main_static_audit.py app_cv/tests/test_pipelines_contract.py
git commit -m "feat: uzyj regionow zmian w snapshot-first"
```

---

## Task 5: Autotune Creates Session Reference

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Test: `app_cv/tests/test_main_static_audit.py`
- Test: `app_cv/tests/test_pipelines_contract.py`

**Important:** Ten task nie moze uzywac starego wyniku globalnej detekcji kart jako warunku utworzenia pierwszego `empty_reference`. Najpierw powstaje median reference z kilku stabilnych snapshotow pustej maty. Dopiero potem system waliduje, czy referencja jest stabilna i czy nie generuje regionow zmian.

- [ ] **Step 1: Write failing tests**

Add static test:

```python
    def test_autotune_empty_stage_bootstraps_reference_before_validation(self):
        source = self._read_main_source()
        autotune_start_index = source.index('if message.type == "autotune_start"')
        autotune_start_block = source[
            autotune_start_index:source.index('if message.type == "autotune_calibrate"')
        ]

        self.assertIn('message.scenario == "empty"', autotune_start_block)
        self.assertIn("background_model.clear()", autotune_start_block)
        self.assertIn("empty_reference_bootstrap", source)
        self.assertIn("capture_many", source)
```

Add pipeline contract test:

```python
    def test_snapshot_pipeline_collects_empty_reference_frames_before_validation(self):
        background_model = MagicMock()
        recorder = MagicMock(side_effect=[
            {"collect_empty_reference_frame": True},
            {"collect_empty_reference_frame": True},
            {"collect_empty_reference_frame": True, "finalize_empty_reference": True},
        ])

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
            background_model=background_model,
            autotune_sample_recorder=recorder,
        )

        # Process three forced empty snapshots.
        # Expected: background_model.capture_many(frames) is called only after the third frame,
        # not after a global detector PASS.
        background_model.capture_many.assert_called_once()

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

Implement this test fully like existing pipeline tests in `app_cv/tests/test_pipelines_contract.py`; do not leave ellipses in committed test code.

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Expected: FAIL for missing clear/capture behavior.

- [ ] **Step 3: Implement bootstrap state in main.py**

Add a small bootstrap buffer near existing autotune globals:

```python
empty_reference_bootstrap = []
```

In `autotune_start` block:

```python
        if message.scenario == "empty":
            background_model.clear()
            empty_reference_bootstrap.clear()
```

In `record_autotune_sample_from_snapshot(sample)`, return bootstrap signals for empty scenario:

```python
    if scenario == "empty":
        if autotune_session.ready_to_score():
            return {
                "collect_empty_reference_frame": True,
                "finalize_empty_reference": True,
            }
        return {
            "collect_empty_reference_frame": True,
            "request_next_sample": True,
        }
```

Preserve existing `stage_completed` logging. The final ready block should be shaped like:

```python
    if autotune_session.ready_to_score():
        result = autotune_session.stage_result()
        write_autotune_log("stage_completed")
        add_operator_warning(
            f"Autotuning {scenario}: {result['state']} - {result['message']}"
        )
        if scenario == "empty":
            return {
                "collect_empty_reference_frame": True,
                "finalize_empty_reference": True,
            }
        return None
```

- [ ] **Step 4: Implement capture_many in pipeline**

In pipeline after recorder result:

```python
                if (
                        isinstance(autotune_recorder_result, dict)
                        and autotune_recorder_result.get("collect_empty_reference_frame")):
                    self.empty_reference_frames.append(analysis_frame.copy())

                if (
                        isinstance(autotune_recorder_result, dict)
                        and autotune_recorder_result.get("finalize_empty_reference")
                        and self.background_model is not None):
                    self.background_model.capture_many(self.empty_reference_frames)
                    self.runtime_metrics.add("background_reference_captured", 1)
                    self.empty_reference_frames = []
```

Add `self.empty_reference_frames = []` to `SnapshotFirstPipeline.__init__`.

- [ ] **Step 5: Validate reference after bootstrap**

After `background_model.capture_many(self.empty_reference_frames)`, validate the last empty frame against the newly built reference. Do not validate with `change_detector.detect(analysis_frame, analysis_frame, ...)`, because comparing a frame to itself always hides reference drift.

```python
                validation_ratio = self.background_model.changed_ratio(analysis_frame, threshold=20)
                self.runtime_metrics.add("background_reference_validation_ratio", validation_ratio)

                if validation_ratio > 0.01:
                    self.runtime_metrics.add("background_reference_validation_warning", 1)
                else:
                    self.runtime_metrics.add("background_reference_validation_warning", 0)
```

Threshold `0.01` is an initial MVP value and may later move to runtime config / autotune profile. If validation reports warning, Studio / CV Explain should surface the issue in Task 6.

- [ ] **Step 6: Verify GREEN**

Run:

```powershell
$env:PYTHONPATH='C:\tmp\tarot_pydeps;app_cv'; python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add app_cv/main.py app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_main_static_audit.py app_cv/tests/test_pipelines_contract.py
git commit -m "feat: zapisz pusta mate jako referencje tła"
```

---

## Task 6: CV Explain and Diagnostics

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

## Task 7: Live Smoke

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
- `roi_hints=None` jest jedynym stanem, w ktorym global fallback detection moze dzialac.
- `roi_hints=[]` oznacza aktywny event-first bez regionow `added_or_moved`; analyzer nie moze wtedy uruchamiac globalnej detekcji.
- Stabilna pusta mata po kalibracji daje `roi_hints=[]`, `card_count=0` i brak globalnego skanu.
- Walidacja `empty_reference` uzywa `BackgroundModel.changed_ratio(current_empty_frame)` albo rownowaznego porownania reference-vs-current, nie `current_frame` vs samo siebie.
- Po aktywnej kalibracji `empty_reference` global card detection nie jest glowna sciezka robocza; moze dzialac tylko jako fallback diagnostyczny albo tryb awaryjny.
- Gdy `ChangeDetector` nie zwraca `added_or_moved`, runtime nie publikuje przypadkowych kart z globalnego skanu.
- Gdy `ChangeDetector` zwraca `ignored_global_shift`, pipeline zachowuje poprzedni dobry stan i publikuje ostrzezenie operatora.
- Gdy nie ma aktywnego `empty_reference`, Studio jasno pokazuje fallback mode bez pelnej kalibracji.
- Runtime metrics publikuja `change_region_count`, `change_mask_ratio`, `change_global_shift`, `change_added_count`, `change_removed_count`.
- CV Explain pokazuje, czy problem lezy w braku regionow zmian, globalnej zmianie obrazu czy false positives detektora.
- Pelny backend test suite przechodzi.
- Frontend build przechodzi.
- Live smoke pokazuje w logach, dlaczego etap `empty` jest PASS albo FAIL.

## Ryzyka

- Autoekspozycja kamery moze generowac globalne roznice. Mitigacja: `global_shift_ratio` i ostrzezenie zamiast publikacji nowego stanu.
- Zly warp ArUco moze przesuwac cala mate. Mitigacja: porownywac tylko gdy `table.calibrated == True`; inaczej fallback do globalnej detekcji z ostrzezeniem.
- Karta przesunieta o kilka pikseli moze dac obwodke zamiast pelnego regionu. Mitigacja: morfologia close + padding ROI.
- Karta lezaca od poczatku przed capture pustej maty zostanie uznana za tlo. Mitigacja: UI musi jasno mowic operatorowi, zeby zdjal wszystkie karty; po utworzeniu median `empty_reference` test 1 karty musi wykazac region `added_or_moved` o rozmiarze zblizonym do karty.
- Zbyt agresywne ROI moze ukryc prawdziwa karte. Mitigacja w pierwszej iteracji: ROI ogranicza tylko przy wiarygodnych regionach; przy `global_shift` albo braku referencji fallback do dotychczasowej analizy.

## Kolejnosc Integracji

1. Najpierw stabilny `BackgroundModel`.
2. Potem niezalezny `ChangeDetector`.
3. Potem ROI hints w `SnapshotAnalyzer`.
4. Potem wiring runtime w `SnapshotFirstPipeline` i `main.py`.
5. Potem Auto Tune empty reference jako procedura kalibracyjna.
6. Potem CV Explain i diagnostyka.
7. Na koncu live smoke.

Ta kolejnosc jest celowa: najpierw budujemy czyste, testowalne moduly bez kamery, dopiero pozniej podpinamy je do runtime.
