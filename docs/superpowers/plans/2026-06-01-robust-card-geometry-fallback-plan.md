# Robust Card Geometry Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Uodpornic snapshot-first card detection na odblaski, folie i slaby kontrast przez dodanie bezpiecznego fallbacku `cv2.minAreaRect` oraz zdefiniowanie kontrolowanej sciezki eskalacji do coraz luzniejszych rekonstrukcji krawedziowych, bez oslabiania finalnej walidacji rozpoznania ORB.

**Architecture:** Obecny detector pelnych quadow zostaje pierwsza sciezka. Nowy fallback generuje dodatkowe 4-punktowe kandydaty z poszarpanych konturow przez `cv2.minAreaRect`; kandydat nadal musi przejsc crop/deskew i rozpoznanie ORB, zanim karta trafi do payloadu. Jesli to nie wystarczy w live testach, kolejne zadania beda dokladac Hough/edge reconstruction w poziomach 3-edge, 2-edge i 1-edge, kazdy z osobna i tylko po pomiarach false positives.

**Tech Stack:** Python 3.13, OpenCV, NumPy, stdlib `unittest`, istniejący pipeline `SnapshotAnalyzer` / `find_card_quads_multi_profile`, Vite frontend only for regression if UI is touched.

---

## Status Ogolny

## Session Status (2026-06-01, Codex, Geometry Fallback)

Completed:
- Przywrocono kontrakt `SnapshotAnalyzer`: testowe `find_quads` znowu jest respektowane, a pelny debug detector jest opcjonalnym hookiem.
- Dodano stabilny kontrakt diagnostyki detekcji w `detection_diagnostics.py` i publikacje licznikow do runtime metrics.
- Dodano profil `min_area_rect` jako kontrolowany fallback dla poszarpanych konturow, z licznikami kandydatow i akceptacji.
- Odfiltrowano obce markery ArUco ze statusu/kalibracji, z zachowaniem zasady, ze extra marker nie uniewaznia kompletu `10-13`.

Verification:
- `python -m unittest app_cv.tests.test_detection_diagnostics app_cv.tests.test_snapshot_analyzer app_cv.tests.test_card_detection_profiles app_cv.tests.test_table_calibration app_cv.tests.test_pipelines_contract -v` -> PASS, 35 tests.
- `python -m unittest discover -s app_cv\tests -v` -> PASS, 219 tests. During import, an existing process occupied WebSocket port `8765`; this printed a background thread bind exception, but the unittest run completed `OK`.
- `python -m py_compile app_cv\main.py app_cv\tarotvision\card_detection.py app_cv\tarotvision\card_detection_profiles.py app_cv\tarotvision\detection_diagnostics.py app_cv\tarotvision\snapshot_analyzer.py app_cv\tarotvision\table_calibration.py app_cv\tarotvision\pipelines\snapshot_first.py` -> PASS.
- Lokalny `C:\tmp\tarot_pydeps` mial uszkodzony namespace `cv2`; testy uruchomiono na swiezym targetcie `E:\Antigravity\Projekty\TAROT\.tmp_pydeps`.

Remaining:
- Live retest z Gemini: pusta mata, Gilded na ciemnej macie, karta z odblaskiem/tasma.
- Jezeli `minAreaRect` nie wystarczy: najpierw Hough diagnostics spike, bez produkcyjnego 3/2/1-edge runtime w tym samym kroku.

### Stan aktualny

- Live test `TASK-CV-SNAPSHOT-LIVE-001` potwierdzil, ze `background_capture` odblokowal detekcje talii Gilded na ciemnej macie.
- Logi potwierdzily poprawne rozpoznanie `Gilded_73` po background-diff.
- Test odblasku na karcie z przezroczysta tasma pokazal porazke obecnej detekcji, bo aktualny detector wymaga pelnego, 4-punktowego konturu.
- Commit `ead062b docs:zapisz-wyniki-live-testu-snapshot-first` dodal przydatna diagnostyke, ale zmienil `SnapshotAnalyzer.analyze()` tak, ze ignoruje wstrzykniete `self.find_quads`; to trzeba naprawic przed dalszym wzmacnianiem detectora.
- Rewers Gilded potrafi byc falszywie wykrywany jako marker ArUco `37`; kalibracja stolu powinna akceptowac tylko markery `10-13`.

### Co zostalo zrobione

- Dodano przyciski `background_capture` i `background_clear` do Panelu Operatora.
- Poprawiono numeracje talii Boski: `Boski_79` -> `Boski_77`.
- Udokumentowano live test i wynik GREEN od Gemini.

### Kolejne kroki

1. Przywrocic testowalnosc `SnapshotAnalyzer`.
2. Wdrozyc szczegolowa diagnostyke detekcji jako warunek dalszej pracy.
3. Dodac `minAreaRect` fallback jako generator kandydatow 4-punktowych.
4. Odfiltrowac obce markery ArUco przed aktualizacja kalibracji.
5. Uruchomic testy backendowe i build frontendu, jezeli frontend zostanie dotkniety.

---

## Zasady Projektowe

1. **Nie obnizac finalnej walidacji karty.** Poluzowujemy tylko generowanie kandydatow geometrycznych; karta jest akceptowana dopiero po rozpoznaniu.
2. **Kontrolowana kaskada luzowania.** `minAreaRect` jest pierwszym produkcyjnym fallbackiem. Hough/3-edge/2-edge/1-edge sa kolejnymi poziomami, ale kazdy wymaga osobnego taska, testow pustej maty i live evidence.
3. **Zachowac dependency injection.** `SnapshotAnalyzer(find_quads=...)` musi dzialac w testach i dla przyszlych wariantow detectora.
4. **Diagnostyka nie moze zalewac dysku.** Obrazy debug zapisywac tylko przy fladze srodowiskowej albo jawnej opcji diagnostycznej.
5. **Diagnostyka jest czescia funkcji, nie dodatkiem.** Kazdy nowy profil detekcji musi raportowac, ile konturow zobaczyl, ile kandydatow rozwazyl, ile zaakceptowal i dlaczego odrzucil reszte.
6. **False positive jest gorszy niz brak detekcji.** Luzniejsze poziomy moga generowac kandydaty, ale nie moga publikowac kart bez mocnego ORB i braku false positives na pustej macie.
7. **Male commity.** Kazdy task ponizej ma byc testowalny i commitowany osobno.

---

## File Structure

### Modyfikacje

- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
  Przywraca respektowanie `self.find_quads`, usuwa bezwarunkowy import i wywolanie `find_card_quads_multi_profile`, porzadkuje zapis debug cropow za flaga.

- Modify: `app_cv/tarotvision/card_detection.py`
  Dodaje fallback `minAreaRect` dla konturow, ktore nie sa idealnym `approxPolyDP == 4`, ale maja sensowny rozmiar i proporcje.

- Modify: `app_cv/tarotvision/card_detection_profiles.py`
  Przekazuje szczegolowa diagnostyke profili, opcjonalnie wlacza fallback `min_area_rect` w profilach.

- Create: `app_cv/tarotvision/detection_diagnostics.py`
  Male, jawne struktury danych / helpery do normalizacji diagnostyki detekcji, zeby JSONL i testy mialy stabilny kontrakt.

- Modify: `app_cv/tarotvision/table_calibration.py`
  Filtruje ArUco do dozwolonych markerow `10, 11, 12, 13`.

- Modify: `app_cv/tests/test_snapshot_analyzer.py`
  Chroni dependency injection i liczenie diagnostyki.

- Modify: `app_cv/tests/test_card_detection_profiles.py`
  Dodaje testy syntetyczne dla poszarpanego konturu i pustej maty.

- Modify or create: `app_cv/tests/test_table_calibration.py`
  Dodaje test ignorowania obcego markera `37`, jesli istnieje juz lokalny test kalibracji.

---

## Task 1: Przywrocic Kontrakt `SnapshotAnalyzer`

**Files:**
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Modify: `app_cv/tests/test_snapshot_analyzer.py`

- [ ] **Step 1: Run existing analyzer tests and confirm failure or inspect static break**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_snapshot_analyzer -v"
```

Expected after Gemini commit: tests should fail once `cv2` environment is valid, because `SnapshotAnalyzer` ignores injected `find_quads`. If local `cv2` import is broken, document the exact environment error and continue with static fix plus later CI verification.

- [ ] **Step 2: Add a regression assertion for injected detector use**

In `app_cv/tests/test_snapshot_analyzer.py`, add:

```python
    def test_uses_injected_find_quads(self):
        calls = []
        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)

        def fake_find_quads(frame):
            calls.append(frame.shape)
            return [quad]

        analyzer = SnapshotAnalyzer(
            find_quads=fake_find_quads,
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {"name": "Gilded_73"},
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(calls, [(40, 40, 3)])
        self.assertEqual(result.card_count, 1)
        self.assertEqual(result.cards[0]["name"], "Gilded_73")
```

- [ ] **Step 3: Modify `snapshot_analyzer.py` to use `self.find_quads(frame)`**

Replace the hardcoded multi-profile block with:

```python
        quads = self.find_quads(frame)
        diagnostics["quads_found"] = len(quads)
```

Do not import `find_card_quads_multi_profile` inside `analyze()`.

- [ ] **Step 4: Gate debug crop writes**

In `snapshot_analyzer.py`, replace unconditional crop writing with:

```python
            if _debug_images_enabled():
                _write_debug_crop(crop, diagnostics["recognition_attempts"])
```

Add helpers near the top of the file:

```python
import os
import cv2


def _debug_images_enabled():
    return os.environ.get("TAROTVISION_DEBUG_IMAGES", "0") == "1"


def _debug_log_dir():
    return os.environ.get(
        "TAROTVISION_LOG_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs")),
    )


def _write_debug_crop(crop, index):
    try:
        log_dir = _debug_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        cv2.imwrite(os.path.join(log_dir, f"debug_crop_{index}.jpg"), crop)
    except Exception:
        pass
```

- [ ] **Step 5: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_snapshot_analyzer -v"
```

Expected: PASS, unless local `cv2` install is still broken. If broken locally, run in the known-good environment or rely on CI, but do not claim local PASS.

- [ ] **Step 6: Commit**

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/snapshot_analyzer.py app_cv/tests/test_snapshot_analyzer.py
git -C E:\Antigravity\Projekty\TAROT commit -m "fix:przywroc-iniekcje-detektora-snapshot-analyzer"
```

---

## Task 2: Wdrozyc Stabilny Kontrakt Diagnostyki Detekcji

**Files:**
- Create: `app_cv/tarotvision/detection_diagnostics.py`
- Modify: `app_cv/tarotvision/card_detection_profiles.py`
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Create or modify: `app_cv/tests/test_detection_diagnostics.py`
- Modify: `app_cv/tests/test_snapshot_analyzer.py`

- [ ] **Step 1: Write failing tests for diagnostic schema**

Create `app_cv/tests/test_detection_diagnostics.py`:

```python
import unittest

from tarotvision.detection_diagnostics import (
    empty_detection_diagnostics,
    summarize_detection_diagnostics,
)


class DetectionDiagnosticsTest(unittest.TestCase):
    def test_empty_diagnostics_has_stable_keys(self):
        data = empty_detection_diagnostics()

        self.assertEqual(data["profiles"], [])
        self.assertEqual(data["quads_final"], 0)
        self.assertEqual(data["best_profile"], None)
        self.assertEqual(data["geometry_source"], None)
        self.assertEqual(data["reject_reasons"], {})
        self.assertEqual(data["background_mask_nonzero_ratio"], None)

    def test_summary_counts_profile_candidates(self):
        diagnostics = {
            "profiles": [
                {
                    "name": "background_diff",
                    "quads": 0,
                    "contours_total": 7,
                    "candidates_after_quad": 0,
                    "min_area_rect_candidates": 0,
                    "min_area_rect_accepted": 0,
                },
                {
                    "name": "min_area_rect",
                    "quads": 1,
                    "contours_total": 3,
                    "candidates_after_quad": 0,
                    "min_area_rect_candidates": 2,
                    "min_area_rect_accepted": 1,
                },
            ],
            "quads_final": 1,
            "best_profile": "min_area_rect",
            "geometry_source": "min_area_rect",
            "reject_reasons": {"bad_aspect": 1},
            "background_mask_nonzero_ratio": 0.12,
        }

        summary = summarize_detection_diagnostics(diagnostics)

        self.assertEqual(summary["snapshot_detection_quads_final"], 1)
        self.assertEqual(summary["snapshot_detection_profile_count"], 2)
        self.assertEqual(summary["snapshot_min_area_rect_candidates"], 2)
        self.assertEqual(summary["snapshot_min_area_rect_accepted"], 1)
        self.assertEqual(summary["snapshot_foreground_contours_total"], 10)
        self.assertEqual(summary["snapshot_background_mask_nonzero_ratio"], 0.12)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_detection_diagnostics -v"
```

Expected: FAIL because `tarotvision.detection_diagnostics` does not exist.

- [ ] **Step 3: Implement diagnostics helpers**

Create `app_cv/tarotvision/detection_diagnostics.py`:

```python
def empty_detection_diagnostics():
    return {
        "profiles": [],
        "quads_final": 0,
        "best_profile": None,
        "geometry_source": None,
        "reject_reasons": {},
        "background_mask_nonzero_ratio": None,
    }


def _sum_profile_key(diagnostics, key):
    return sum(
        int(profile.get(key, 0) or 0)
        for profile in diagnostics.get("profiles", [])
    )


def summarize_detection_diagnostics(diagnostics):
    diagnostics = diagnostics or empty_detection_diagnostics()
    profiles = diagnostics.get("profiles", [])
    return {
        "snapshot_detection_quads_final": int(diagnostics.get("quads_final", 0) or 0),
        "snapshot_detection_profile_count": len(profiles),
        "snapshot_strict_quad_candidates": _sum_profile_key(diagnostics, "candidates_after_quad"),
        "snapshot_min_area_rect_candidates": _sum_profile_key(diagnostics, "min_area_rect_candidates"),
        "snapshot_min_area_rect_accepted": _sum_profile_key(diagnostics, "min_area_rect_accepted"),
        "snapshot_foreground_contours_total": _sum_profile_key(diagnostics, "contours_total"),
        "snapshot_background_mask_nonzero_ratio": diagnostics.get("background_mask_nonzero_ratio"),
    }
```

- [ ] **Step 4: Extend `card_detection_profiles.py` debug dict now, before adding new fallback**

Ensure every profile debug entry includes these keys, even when value is zero:

```python
{
    "name": profile.name,
    "mode": profile.mode,
    "quads": len(quads),
    "contours_total": debug.get("contours_total", 0),
    "candidates_after_quad": debug.get("candidates_after_quad", 0),
    "min_area_rect_candidates": debug.get("min_area_rect_candidates", 0),
    "min_area_rect_accepted": debug.get("min_area_rect_accepted", 0),
}
```

For `background_diff`, also include those same keys. Add top-level keys:

```python
debug={
    "profiles": debug_profiles,
    "quads_final": len(deduped),
    "best_profile": best_profile,
    "geometry_source": best_profile,
    "reject_reasons": {},
    "background_mask_nonzero_ratio": background_mask_nonzero_ratio,
}
```

Compute `background_mask_nonzero_ratio` when background mask exists:

```python
background_mask_nonzero_ratio = float(np.count_nonzero(mask)) / mask.size
```

Use `None` if no mask exists.

- [ ] **Step 5: Add `find_quads_with_debug` path to `SnapshotAnalyzer`**

In `SnapshotAnalyzer.__init__`, add:

```python
                 find_quads_with_debug=None):
        self.find_quads_with_debug = find_quads_with_debug
```

In `analyze()`:

```python
        detection_debug = {}
        if self.find_quads_with_debug is not None:
            detection_result = self.find_quads_with_debug(frame)
            quads = detection_result.quads
            detection_debug = detection_result.debug
        else:
            quads = self.find_quads(frame)
        diagnostics["detection"] = detection_debug
```

Do not hardcode `find_card_quads_multi_profile()` inside `analyze()`.

- [ ] **Step 6: Publish diagnostic numeric metrics in `snapshot_first.py`**

Import:

```python
from tarotvision.detection_diagnostics import summarize_detection_diagnostics
```

After `diagnostics = result.diagnostics ...`, add:

```python
                detection_summary = summarize_detection_diagnostics(
                    diagnostics.get("detection", {})
                )
                for metric_name, metric_value in detection_summary.items():
                    if isinstance(metric_value, (int, float)) and metric_value is not None:
                        self.runtime_metrics.add(metric_name, metric_value)
```

Do not add string metrics to `RuntimeMetrics`.

- [ ] **Step 7: Add visual debug image set behind flag**

Keep image writes disabled by default. When `TAROTVISION_DEBUG_IMAGES=1`, write:

```text
debug_background_mask.jpg
debug_quads_overlay.jpg
debug_crop_<n>.jpg
```

If adding overlay is too much for this task, implement only mask and crop, but keep the helper names stable.

- [ ] **Step 8: Verify diagnostics tests**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_detection_diagnostics app_cv.tests.test_snapshot_analyzer -v"
```

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/detection_diagnostics.py app_cv/tarotvision/card_detection_profiles.py app_cv/tarotvision/snapshot_analyzer.py app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_detection_diagnostics.py app_cv/tests/test_snapshot_analyzer.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat:dodaj-kontrakt-diagnostyki-detekcji-kart"
```

---

## Task 3: Dodac `minAreaRect` Fallback w Detekcji Kart

**Files:**
- Modify: `app_cv/tarotvision/card_detection.py`
- Modify: `app_cv/tests/test_card_detection_profiles.py`

- [ ] **Step 1: Inspect current detector API**

Read:

```powershell
Get-Content -Raw -LiteralPath E:\Antigravity\Projekty\TAROT\app_cv\tarotvision\card_detection.py
```

Confirm exact names for `find_card_quads`, aspect-ratio checks, area checks and debug dict keys before editing.

- [ ] **Step 2: Add failing test for ragged contour**

In `app_cv/tests/test_card_detection_profiles.py`, add a test that creates a dark card-like polygon with a damaged corner on a dark background:

```python
    def test_min_area_rect_fallback_detects_ragged_card_contour(self):
        frame = np.zeros((220, 220, 3), dtype=np.uint8)
        frame[:, :] = (22, 28, 42)
        ragged = np.array([
            [70, 30], [145, 35], [156, 58], [152, 180],
            [72, 174], [65, 115], [78, 95], [66, 62],
        ], dtype=np.int32)
        cv2.fillPoly(frame, [ragged], (86, 92, 110))

        result = find_card_quads_multi_profile(frame)

        self.assertGreaterEqual(len(result.quads), 1)
        self.assertIn("min_area_rect", [
            profile["name"] for profile in result.debug["profiles"]
        ])
```

Expected before implementation: FAIL because current strict quad path may reject the ragged contour or no `min_area_rect` profile exists.

- [ ] **Step 3: Add false-positive test for empty mat**

In the same test file:

```python
    def test_min_area_rect_fallback_rejects_empty_mat(self):
        frame = np.zeros((220, 220, 3), dtype=np.uint8)
        frame[:, :] = (22, 28, 42)

        result = find_card_quads_multi_profile(frame)

        self.assertEqual(result.quads, [])
```

- [ ] **Step 4: Implement helper in `card_detection.py`**

Add a helper that converts a contour to a valid quad only when it resembles a tarot card:

```python
def contour_to_min_area_quad(contour, frame_area, min_area_ratio=0.001,
                             min_aspect=1.35, max_aspect=2.15):
    area = cv2.contourArea(contour)
    if area < frame_area * min_area_ratio:
        return None

    rect = cv2.minAreaRect(contour)
    (width, height) = rect[1]
    if width <= 1 or height <= 1:
        return None

    long_side = max(width, height)
    short_side = min(width, height)
    aspect = long_side / short_side
    if aspect < min_aspect or aspect > max_aspect:
        return None

    box = cv2.boxPoints(rect)
    return box.reshape(4, 1, 2).astype(np.float32)
```

Do not use deprecated `np.int0`.

- [ ] **Step 5: Add optional fallback branch to `find_card_quads`**

Extend `find_card_quads(...)` with a keyword:

```python
use_min_area_rect_fallback=False
```

When `approxPolyDP` is not a valid 4-point quad and fallback is enabled, call `contour_to_min_area_quad(...)`. Add debug counters:

```python
debug["min_area_rect_candidates"] = 0
debug["min_area_rect_accepted"] = 0
```

Increment candidates for contours considered by fallback and accepted for returned fallback quads.

- [ ] **Step 6: Wire fallback as a profile**

In `app_cv/tarotvision/card_detection_profiles.py`, add:

```python
DetectionProfile("min_area_rect", "adaptive_dark", min_area_ratio=0.001, contour_mode="list")
```

When profile name is `"min_area_rect"`, call `find_card_quads(..., use_min_area_rect_fallback=True, return_debug=True)`.

Include debug fields:

```python
"min_area_rect_candidates": debug.get("min_area_rect_candidates", 0),
"min_area_rect_accepted": debug.get("min_area_rect_accepted", 0),
```

- [ ] **Step 7: Verify targeted tests**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_card_detection_profiles -v"
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/card_detection.py app_cv/tarotvision/card_detection_profiles.py app_cv/tests/test_card_detection_profiles.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat:dodaj-minarearect-fallback-detekcji-kart"
```

---

## Task 4: Polaczyc Diagnostyke Runtime z Profilami Bez Obejscia Analyzer API

**Files:**
- Modify: `app_cv/tarotvision/card_detection_profiles.py`
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Modify: `app_cv/tests/test_snapshot_analyzer.py`
- Modify: `app_cv/tests/test_pipelines_contract.py`

- [ ] **Step 1: Add a detector result path without breaking `find_quads` injection**

If Task 2 already added `find_quads_with_debug`, verify it is still present:

```python
    def __init__(self, find_quads=None, crop_card=None, recognize_crop=None,
                 scene_width=26.0, scene_height=15.6, background_model=None,
                 find_quads_with_debug=None):
        self.find_quads = find_quads or self._find_quads_default
        self.find_quads_with_debug = find_quads_with_debug
```

- [ ] **Step 2: Use debug detector only when provided**

In `analyze()`:

```python
        detection_debug = {}
        if self.find_quads_with_debug is not None:
            detection_result = self.find_quads_with_debug(frame)
            quads = detection_result.quads
            detection_debug = detection_result.debug
        else:
            quads = self.find_quads(frame)
```

Then add:

```python
        diagnostics["detection"] = detection_debug
```

- [ ] **Step 3: Wire runtime analyzer with debug detector in `main.py`**

In `main.py`, when constructing `SnapshotAnalyzer`, pass:

```python
find_quads_with_debug=lambda frame: find_card_quads_multi_profile(
    frame,
    background_model=background_model,
),
```

If `find_card_quads_multi_profile` is not imported in `main.py`, import it from `tarotvision.card_detection_profiles`.

- [ ] **Step 4: Publish useful detector metrics in `snapshot_first.py`**

After:

```python
diagnostics = result.diagnostics if isinstance(result.diagnostics, dict) else {}
```

Add:

```python
                detection_debug = diagnostics.get("detection", {})
                self.runtime_metrics.add(
                    "snapshot_detection_profiles",
                    len(detection_debug.get("profiles", [])),
                )
                self.runtime_metrics.add(
                    "snapshot_detection_quads_final",
                    detection_debug.get("quads_final", diagnostics.get("quads_found", 0)),
                )
```

Do not add string-valued metrics to `RuntimeMetrics` unless it supports non-numeric values.

- [ ] **Step 5: Add tests**

In `app_cv/tests/test_snapshot_analyzer.py`, add:

```python
    def test_uses_debug_detector_when_provided(self):
        class DetectionResult:
            def __init__(self, quads, debug):
                self.quads = quads
                self.debug = debug

        quad = np.array([[[10, 10]], [[20, 10]], [[20, 30]], [[10, 30]]],
                        dtype=np.float32)
        analyzer = SnapshotAnalyzer(
            crop_card=lambda frame, quad: "crop",
            recognize_crop=lambda crop: {"name": "Gilded_73"},
            find_quads_with_debug=lambda frame: DetectionResult(
                [quad],
                {"profiles": [{"name": "min_area_rect"}], "quads_final": 1},
            ),
        )

        result = analyzer.analyze(np.zeros((40, 40, 3), dtype=np.uint8))

        self.assertEqual(result.card_count, 1)
        self.assertEqual(result.diagnostics["detection"]["quads_final"], 1)
```

- [ ] **Step 6: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract -v"
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/main.py app_cv/tarotvision/snapshot_analyzer.py app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_snapshot_analyzer.py app_cv/tests/test_pipelines_contract.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat:dodaj-diagnostyke-profili-detekcji-snapshot"
```

---

## Task 5: Filtrowanie Obcych Markerow ArUco

**Files:**
- Modify: `app_cv/tarotvision/table_calibration.py`
- Test: existing or new `app_cv/tests/test_table_calibration.py`

- [ ] **Step 1: Inspect calibration module**

Run:

```powershell
Get-Content -Raw -LiteralPath E:\Antigravity\Projekty\TAROT\app_cv\tarotvision\table_calibration.py
```

Find where detected marker IDs are stored and where calibration is updated.

- [ ] **Step 2: Add allowed marker constant**

In `table_calibration.py`, define:

```python
ALLOWED_TABLE_MARKER_IDS = {10, 11, 12, 13}
```

- [ ] **Step 3: Filter detections before calibration state update**

Where marker IDs and corners are read from OpenCV, keep only pairs whose ID is in `ALLOWED_TABLE_MARKER_IDS`. The stored `marker_ids` in status must not include `37`.

- [ ] **Step 4: Add test for ignoring marker 37**

If `TableCalibration` exposes a helper for marker processing, test that helper. If not, extract a small pure helper:

```python
def filter_table_markers(corners, ids):
    if ids is None:
        return [], None
    kept_corners = []
    kept_ids = []
    for corner, marker_id in zip(corners, ids.reshape(-1)):
        if int(marker_id) in ALLOWED_TABLE_MARKER_IDS:
            kept_corners.append(corner)
            kept_ids.append([int(marker_id)])
    if not kept_ids:
        return [], None
    return kept_corners, np.array(kept_ids, dtype=np.int32)
```

Test:

```python
    def test_filter_table_markers_ignores_non_table_marker(self):
        corners = [np.zeros((1, 4, 2), dtype=np.float32) for _ in range(2)]
        ids = np.array([[10], [37]], dtype=np.int32)

        kept_corners, kept_ids = filter_table_markers(corners, ids)

        self.assertEqual(len(kept_corners), 1)
        self.assertEqual(kept_ids.tolist(), [[10]])
```

- [ ] **Step 5: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_table_calibration -v"
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/table_calibration.py app_cv/tests/test_table_calibration.py
git -C E:\Antigravity\Projekty\TAROT commit -m "fix:filtruj-obce-markery-aruco-stolu"
```

---

## Task 6: Zdefiniowac Nastepne Poziomy Luzowania jako Bramkowany Spike

**Files:**
- Modify: `docs/superpowers/plans/2026-06-01-robust-card-geometry-fallback-plan.md`
- Optional create: `docs/superpowers/plans/2026-06-01-hough-edge-fallback-spike-plan.md`
- Modify: `.ai/TASKS_INDEX.md`

- [ ] **Step 1: Add explicit escalation ladder**

If `minAreaRect` fails live tests, use this order. Do not skip levels:

```markdown
### Escalation Ladder

Level 0: strict quad / current contour detector.
Level 1: `minAreaRect` from ragged contour. Production candidate after tests.
Level 2: Hough diagnostics only. No card publishing.
Level 3: 3-edge reconstruction. Candidate publishing only after ORB and empty-mat tests.
Level 4: 2-edge reconstruction. Requires stricter ORB and foreground-fill validation.
Level 5: 1-edge reconstruction. Debug/spike only until proven on live samples.
```

- [ ] **Step 2: Write future spike plan only if needed**

Create `docs/superpowers/plans/2026-06-01-hough-edge-fallback-spike-plan.md` only after live tests prove `minAreaRect` insufficient. The spike must collect:

```markdown
- Hough line count per snapshot
- dominant line angle clusters
- line length distribution
- foreground side agreement from `background_diff`
- candidate crop count
- ORB confirmation rate
- false positives on empty mat
```

- [ ] **Step 3: Acceptance gate for any edge reconstruction**

Before any 3/2/1-edge reconstruction is allowed into runtime, require:

```text
empty mat false positives: 0 in live smoke test
recognition_attempts: > 0 on difficult card
accepted card: correct deck_id and card_id
manual visual crop check: crop contains whole card, not mat/cable/hand
```

- [ ] **Step 4: Commit escalation docs**

```powershell
git -C E:\Antigravity\Projekty\TAROT add docs/superpowers/plans/2026-06-01-robust-card-geometry-fallback-plan.md
git -C E:\Antigravity\Projekty\TAROT commit -m "docs:dodaj-kaskade-luzowania-detekcji-kart"
```

---

## Task 7: Pelna Weryfikacja i Handoff

**Files:**
- Modify: `docs/superpowers/plans/2026-06-01-robust-card-geometry-fallback-plan.md`
- Modify: `.ai/TASKS_INDEX.md`
- Optional create: `.ai/tasks/TASK-CV-GEOMETRY-FALLBACK-001/STATE.md`
- Optional create: `.ai/tasks/TASK-CV-GEOMETRY-FALLBACK-001/TEST_REPORT.md`
- Optional create: `.ai/tasks/TASK-CV-GEOMETRY-FALLBACK-001/GEMINI_REPORT.md`

- [ ] **Step 1: Register task**

Add row to `.ai/TASKS_INDEX.md`:

```markdown
| **TASK-CV-GEOMETRY-FALLBACK-001** | `DONE` | `codex/snapshot-first-recognition-hardening` | Codex | MinAreaRect fallback i filtr ArUco dla live snapshot-first | 2026-06-01 | Oczekuje na review |
```

- [ ] **Step 2: Run targeted backend tests**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_card_detection_profiles app_cv.tests.test_pipelines_contract app_cv.tests.test_table_calibration -v"
```

Expected: PASS.

- [ ] **Step 3: Run full backend suite**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Expected: PASS.

- [ ] **Step 4: Run frontend build only if frontend changed**

If `app_ar/` changed in this task, run:

```powershell
cmd.exe /c npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: PASS. Existing Vite warnings about chunk size and ineffective dynamic import are acceptable.

- [ ] **Step 5: Update this plan session status**

Append:

```markdown
## Session Status (2026-06-01, Codex, Geometry Fallback)

Completed:
- <hash>: fix:przywroc-iniekcje-detektora-snapshot-analyzer
- <hash>: feat:dodaj-minarearect-fallback-detekcji-kart
- <hash>: feat:dodaj-diagnostyke-profili-detekcji-snapshot
- <hash>: fix:filtruj-obce-markery-aruco-stolu

Verification:
- `python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_card_detection_profiles app_cv.tests.test_pipelines_contract app_cv.tests.test_table_calibration -v` -> PASS/FAIL
- `python -m unittest discover -s app_cv\tests -v` -> PASS/FAIL

Remaining:
- Live retest z Gemini: karta Gilded z odblaskiem/tasma oraz pusta mata po `background_capture`.
- Jezeli `minAreaRect` nie wystarczy: uruchomic Hough diagnostics spike, nie wdrazac od razu 3/2/1-edge runtime.
```

- [ ] **Step 6: Commit docs**

```powershell
git -C E:\Antigravity\Projekty\TAROT add docs/superpowers/plans/2026-06-01-robust-card-geometry-fallback-plan.md .ai/TASKS_INDEX.md
git -C E:\Antigravity\Projekty\TAROT commit -m "docs:zaplanuj-minarearect-fallback-detekcji-kart"
```

---

## Acceptance Criteria

- `SnapshotAnalyzer` nadal respektuje wstrzykniete `find_quads`.
- Diagnostyka detekcji ma stabilny kontrakt w `detection_diagnostics.py`.
- JSONL/runtime metrics zawieraja liczniki profili, kandydatow i background mask ratio potrzebne do analizy live testow.
- Diagnostyka obrazow jest domyslnie wylaczona i wlaczana przez `TAROTVISION_DEBUG_IMAGES=1`.
- `find_card_quads_multi_profile()` potrafi znalezc kandydata z poszarpanego konturu przez `minAreaRect`.
- Pusta mata nie generuje fallbackowego quada.
- Karta jest publikowana tylko po rozpoznaniu, nie po samej geometrii.
- Status kalibracji ArUco ignoruje marker `37` i wszystkie ID spoza `10-13`.
- Plan zawiera jasna drabine dalszego luzowania: minAreaRect -> Hough diagnostics -> 3-edge -> 2-edge -> 1-edge.
- Targeted backend tests przechodza.
- Full backend suite przechodzi albo raportuje dokladny, niezalezny blocker srodowiskowy.

## Out of Scope

- Produkcyjne wdrozenie rekonstrukcji z 3 wierzcholkow w tym tasku.
- Produkcyjne wdrozenie rekonstrukcji z 2 wierzcholkow w tym tasku.
- Produkcyjne wdrozenie rekonstrukcji z 1 krawedzi w tym tasku.
- YOLO/OBB/Ultralytics.
- Zmiana progow ORB jako kompensacja slabej geometrii.
- Commitowanie fizycznych zdjec z kamery bez zgody Michala.

## Immediate Next Action

Zaczac od Task 1. Nie implementowac `minAreaRect`, dopoki `SnapshotAnalyzer` nie odzyska kontraktu dependency injection; inaczej testy beda mylace i trudniej bedzie ocenic regresje.
