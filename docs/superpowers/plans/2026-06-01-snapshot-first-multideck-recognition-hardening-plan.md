# Snapshot-First Multideck Recognition Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Utrwalić `snapshot-first` jako jedyny produkcyjny pipeline CV i poprawić wykrywanie oraz identyfikację kart dla ciemnych talii na różnych matach bez wprowadzania ryzykownej zależności ML do runtime.

**Architecture:** System ma działać jako sekwencja: motion gate -> wybór najlepszego snapshotu -> opcjonalny warp ArUco -> wielowariantowa detekcja prostokątów -> crop/deskew -> rozpoznanie cropa -> publikacja layoutu. Stary `state-first` zostaje usunięty z kodu produkcyjnego i testów, a nowe moduły mają rozdzielać odpowiedzialności: obraz I/O, ładowanie wzorców, diagnostyka, detekcja kandydatów, model tła i scoring autotuningu. Ultralytics/YOLO pozostaje wyłącznie jako osobny, licencyjnie bramkowany spike po zebraniu danych.

**Tech Stack:** Python 3.13, OpenCV, NumPy, stdlib `unittest`, JSONL diagnostics, Vite build for frontend regression, existing WebSocket payload v1.

---

## Status Ogólny

### Stan aktualny

- Produkcyjny kierunek decyzyjny od Michała: w repo zostaje tylko podejście `snapshot-first`.
- `app_cv/main.py` nadal importuje i inicjalizuje `StateFirstLegacyPipeline`; gałąź runtime jest wybierana przez `TAROTVISION_SNAPSHOT_FIRST`.
- `app_cv/tarotvision/pipelines/state_first_legacy.py` istnieje i może mylić kolejnego agenta.
- `app_cv/tests/test_pipelines_contract.py` nadal wymaga kontraktu legacy pipeline.
- `README.md` nadal opisuje state-first jako następny kierunek rozwoju.
- Obecna detekcja kart w `app_cv/tarotvision/card_detection.py` jest prosta: grayscale -> GaussianBlur -> Canny -> `findContours` -> `approxPolyDP` -> aspect ratio.
- Obecny `SnapshotAnalyzer` analizuje przekazaną klatkę bez jawnego użycia `TableCalibration.warp_frame()` w samym pipeline snapshot-first.
- `main.py` ładuje wzorce CV przez `cv2.imread()`, co na Windowsie nie czyta niezawodnie ścieżek z polskimi znakami. Lokalny test pokazał ostrzeżenia dla `Światło_i_Cień_*.jpg`.
- Ciemne talie mają dużo cech ORB na wzorcach po CLAHE, więc pierwotny problem ciemna talia + ciemna mata jest najpewniej przed matchingiem: lokalizacja prostokąta, crop, kontrast względem maty albo brak diagnostyki porażki.

### Co zostało zrobione

- `TASK-CV-RECT-001` sparametryzował `find_card_quads()` pod Canny / contour mode / max candidates.
- `TASK-CV-AUTOTUNE-001` dodał offline autotuner geometrii prostokąta, zatwierdzony przez Codex review jako `LIGHT: GREEN`.
- Operator console i profile runtime już istnieją, ale aktualny autotuning nie jest jeszcze częścią live snapshot-first flow.
- `TASK-CV-SNAPSHOT-001` usunął runtime legacy state-first z `main.py`, eksportów i testów kontraktowych; snapshot-first jest teraz bezwarunkową ścieżką backendu CV.
- `TASK-CV-SNAPSHOT-002` dodał Unicode-safe image I/O i przeniósł ładowanie aktywnych talii do `reference_loader.py`.
- `TASK-CV-SNAPSHOT-003` podłączył analizę snapshotu do klatki sprostowanej przez ArUco, gdy kalibracja jest dostępna.

### Kolejne kroki

1. Usunąć legacy state-first z runtime i testów.
2. Naprawić Unicode image loading dla wzorców.
3. Dodać diagnostykę porażek snapshot-first.
4. Wprowadzić robust OpenCV detector dla ciemnych talii i mat.
5. Dodać model pustej maty jako opcjonalne źródło kontrastu foreground.
6. Rozszerzyć autotuning tak, żeby scoring uwzględniał rozpoznanie cropa, nie tylko geometrię.
7. Dopiero po tych krokach zrobić osobny, bramkowany spike YOLO OBB.

## Session Status (2026-06-01, Codex)

Zrealizowano `TASK-CV-SNAPSHOT-001`: usunięto `StateFirstLegacyPipeline` z eksportów, runtime i testów; `main.py` wywołuje bezwarunkowo `SnapshotFirstPipeline`; README i `.ai/PROJECT_STATE.md` opisują snapshot-first jako jedyną produkcyjną ścieżkę CV.

Weryfikacja:
- `python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v` -> PASS, 5 testów.
- `python -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\__init__.py app_cv\tarotvision\pipelines\snapshot_first.py` -> PASS.

Następny krok: `TASK-CV-SNAPSHOT-002`, czyli Unicode-safe image I/O i przeniesienie loadera wzorców poza `main.py`.

## Session Status (2026-06-01, Codex, Task 2)

Zrealizowano `TASK-CV-SNAPSHOT-002`: dodano `image_io.py`, `reference_loader.py`, testy dla polskich ścieżek i diagnostyki pominietych wzorców; `main.py` używa `load_active_reference_cards()`, a `card_recognition.load_reference_cards()` nie używa już `cv2.imread()` bezpośrednio.

Weryfikacja:
- `python -m unittest app_cv.tests.test_image_io app_cv.tests.test_reference_loader app_cv.tests.test_card_recognition -v` -> PASS, 19 testów.
- `python -m py_compile app_cv\main.py app_cv\tarotvision\image_io.py app_cv\tarotvision\reference_loader.py app_cv\tarotvision\card_recognition.py` -> PASS.

Następny krok: `TASK-CV-SNAPSHOT-003`, czyli analiza snapshotu na klatce po warp ArUco.

## Session Status (2026-06-01, Codex, Task 3)

Zrealizowano `TASK-CV-SNAPSHOT-003`: `SnapshotFirstPipeline` wybiera `analysis_frame`; przy skalibrowanym stole i poprawnym `warp_frame()` analyzer dostaje obraz po korekcji perspektywy, a metryka `snapshot_analysis_warped` raportuje użycie warpu.

Weryfikacja:
- `python -m unittest app_cv.tests.test_pipelines_contract -v` -> PASS, 4 testy.
- `python -m py_compile app_cv\tarotvision\pipelines\snapshot_first.py` -> PASS.

Następny krok: `TASK-CV-SNAPSHOT-004`, czyli diagnostyka porażek detekcji i rozpoznania.

---

## Zasady Projektowe

1. **Snapshot-first jest jedyną ścieżką produkcyjną.** Nie zostawiamy przełącznika środowiskowego, który może uruchomić stary pipeline.
2. **Najpierw diagnostyka, potem tuning.** Każda porażka musi dać odpowiedź, czy padł etap: snapshot quality, quad detection, crop keypoints, matching, homografia czy próg akceptacji.
3. **OpenCV-first.** Nie dodajemy Ultralytics do runtime bez osobnej decyzji licencyjnej Michała.
4. **Bez rozbudowy `main.py`.** Nowa logika idzie do modułów `app_cv/tarotvision/`, a `main.py` tylko je składa.
5. **Kompatybilność payloadu.** Frontend AR i Studio mogą ignorować nowe pola diagnostyczne. Nie wolno łamać `cards`, `metrics`, `runtime`, `operator`, `layout`.
6. **Małe PR-y.** Każdy task poniżej powinien dawać testowalny stan i osobny commit.

---

## File Structure

### Usunięcia

- Delete: `app_cv/tarotvision/pipelines/state_first_legacy.py`
  Usuwa historyczny pipeline continuous/state-first z kodu produkcyjnego.

### Modyfikacje

- Modify: `app_cv/main.py`
  Usuwa import, inicjalizację i gałąź runtime legacy. Zostawia wyłącznie `SnapshotFirstPipeline`.
- Modify: `app_cv/tarotvision/pipelines/__init__.py`
  Eksportuje tylko `VisionPipeline` i `SnapshotFirstPipeline`.
- Modify: `app_cv/tests/test_pipelines_contract.py`
  Usuwa test legacy pipeline i dodaje asercję, że `StateFirstLegacyPipeline` nie jest eksportowany.
- Modify: `app_cv/tests/test_main_static_audit.py`
  Dodaje blokadę na ponowne importowanie `StateFirstLegacyPipeline` i używanie `TAROTVISION_SNAPSHOT_FIRST`.
- Modify: `README.md`
  Aktualizuje opis architektury na snapshot-first-only.
- Modify: `.ai/PROJECT_STATE.md`
  Aktualizuje główny opis modułów i priorytetów.
- Modify: `.ai/TASKS_INDEX.md`
  Dodaje nowe taski wykonawcze ze statusem zgodnym ze słownikiem statusów w rejestrze.

### Nowe moduły

- Create: `app_cv/tarotvision/image_io.py`
  Unicode-safe `imread`/`imwrite` wrappers dla Windows i polskich ścieżek.
- Create: `app_cv/tarotvision/reference_loader.py`
  Ładowanie wzorców aktywnych talii poza `main.py`, z deck metadata i diagnostyką liczby keypointów.
- Create: `app_cv/tarotvision/card_detection_debug.py`
  Artefakty diagnostyczne dla snapshotów: raw, warped, gray, edges, mask, contour overlay, crop.
- Create: `app_cv/tarotvision/card_detection_profiles.py`
  Profile detekcji kart: canny, adaptive threshold, light-on-dark, dark-on-light, background-diff.
- Create: `app_cv/tarotvision/background_model.py`
  Opcjonalna kalibracja pustej maty i maska foreground dla snapshot-first.
- Create: `app_cv/tarotvision/recognition_debug.py`
  Debug rozpoznawania cropa: liczba keypointów, top-k kandydatów, match/inlier diagnostics.
- Create: `app_cv/tarotvision/snapshot_autotune.py`
  Recognition-aware autotuning dla snapshotu: ocenia detektor + crop + ORB/homografia.

### Nowe testy

- Create: `app_cv/tests/test_image_io.py`
- Create: `app_cv/tests/test_reference_loader.py`
- Create: `app_cv/tests/test_card_detection_profiles.py`
- Create: `app_cv/tests/test_background_model.py`
- Create: `app_cv/tests/test_recognition_debug.py`
- Create: `app_cv/tests/test_snapshot_autotune.py`

---

## Task 1: Usunięcie Legacy State-First i Utrwalenie Snapshot-First

**Task ID:** `TASK-CV-SNAPSHOT-001`

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tarotvision/pipelines/__init__.py`
- Delete: `app_cv/tarotvision/pipelines/state_first_legacy.py`
- Modify: `app_cv/tests/test_pipelines_contract.py`
- Modify: `app_cv/tests/test_main_static_audit.py`
- Modify: `README.md`
- Modify: `.ai/PROJECT_STATE.md`
- Modify: `.ai/TASKS_INDEX.md`

- [x] **Step 1: Create branch**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT switch -c codex/snapshot-first-recognition-hardening
```

Expected: branch created from the current accepted base. If execution starts after merge of `TASK-CV-AUTOTUNE-001`, create it from latest `master`.

- [x] **Step 2: Write static guard test**

Modify `app_cv/tests/test_main_static_audit.py` by adding this test method to `TestMainStaticAudit`:

```python
    def test_snapshot_first_is_the_only_runtime_pipeline(self):
        tree = ast.parse(self.main_source)
        forbidden_names = {
            "StateFirstLegacyPipeline",
            "USE_SNAPSHOT_FIRST_CV",
            "legacy_pipeline",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in forbidden_names:
                self.fail(
                    f"main.py must not reference legacy snapshot switch symbol "
                    f"'{node.id}' at line {node.lineno}."
                )
            if isinstance(node, ast.Constant) and node.value == "TAROTVISION_SNAPSHOT_FIRST":
                self.fail(
                    "main.py must not read TAROTVISION_SNAPSHOT_FIRST; "
                    "snapshot-first is now the only production pipeline."
                )
```

- [x] **Step 3: Run static guard and verify failure**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit -v"
```

Expected: FAIL because `main.py` still imports `StateFirstLegacyPipeline`, defines `USE_SNAPSHOT_FIRST_CV`, initializes `legacy_pipeline`, and branches into it.

- [x] **Step 4: Remove legacy export**

Replace `app_cv/tarotvision/pipelines/__init__.py` with:

```python
from .base import VisionPipeline
from .snapshot_first import SnapshotFirstPipeline

__all__ = ["VisionPipeline", "SnapshotFirstPipeline"]
```

- [x] **Step 5: Update pipeline contract tests**

Replace the import in `app_cv/tests/test_pipelines_contract.py`:

```python
from tarotvision.pipelines import VisionPipeline, SnapshotFirstPipeline
```

Delete the whole `test_legacy_pipeline_contract` method.

Add this method:

```python
    def test_legacy_pipeline_is_not_exported(self):
        import tarotvision.pipelines as pipelines

        self.assertFalse(hasattr(pipelines, "StateFirstLegacyPipeline"))
```

- [x] **Step 6: Remove legacy runtime from `main.py`**

In `app_cv/main.py`:

1. Replace:

```python
from tarotvision.pipelines import SnapshotFirstPipeline, StateFirstLegacyPipeline
```

with:

```python
from tarotvision.pipelines import SnapshotFirstPipeline
```

2. Delete:

```python
USE_TABLE_CARD_DETECTION = False
USE_SNAPSHOT_FIRST_CV = os.environ.get("TAROTVISION_SNAPSHOT_FIRST", "0") == "1"
```

3. Delete the full `legacy_pipeline = StateFirstLegacyPipeline(...)` initialization block.

4. In the main loop, replace:

```python
    if USE_SNAPSHOT_FIRST_CV:
        pipeline_result = snapshot_pipeline.process_frame(
            frame=frame,
            motion_result=motion_result,
            frame_width=frame_width,
            frame_height=frame_height,
            frame_loop_start=frame_loop_start
        )
        if pipeline_result["action"] == "quit":
            break
        elif pipeline_result["action"] == "switch":
            frame_width = pipeline_result["frame_width"]
            frame_height = pipeline_result["frame_height"]
            log_event(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")
        continue
```

with unconditional snapshot-first processing:

```python
    pipeline_result = snapshot_pipeline.process_frame(
        frame=frame,
        motion_result=motion_result,
        frame_width=frame_width,
        frame_height=frame_height,
        frame_loop_start=frame_loop_start,
    )
    if pipeline_result["action"] == "quit":
        break
    if pipeline_result["action"] == "switch":
        frame_width = pipeline_result["frame_width"]
        frame_height = pipeline_result["frame_height"]
        log_event(f"[KAMERA] Nowa rozdzielczosc: {frame_width}x{frame_height}")
    continue
```

5. Delete the remaining continuous matching / state-first block below that branch.

- [x] **Step 7: Delete legacy file**

Run:

```powershell
Remove-Item -LiteralPath E:\Antigravity\Projekty\TAROT\app_cv\tarotvision\pipelines\state_first_legacy.py
```

The path is inside the project workspace. Do not delete any other file in this step.

- [x] **Step 8: Update README architecture wording**

In `README.md`, replace the state-first direction paragraph with:

```markdown
Następny kierunek rozwoju CV: architektura snapshot-first. System czeka na ustanie ruchu, wybiera najlepszy snapshot, opcjonalnie prostuje matę przez ArUco, wykrywa prostokąty kart, normalizuje cropy i rozpoznaje je przez dopasowanie cech do aktywnych talii. Nie utrzymujemy już równoległego pipeline state-first, żeby nie mieszać decyzji runtime i uprościć diagnostykę.
```

Replace package description:

```markdown
│   ├── tarotvision/     # Pakiet snapshot-first CV (modul zespolowy)
```

- [x] **Step 9: Update project state**

In `.ai/PROJECT_STATE.md`, update backend module bullet:

```markdown
* `tarotvision/pipelines/snapshot_first.py` — jedyny produkcyjny rurociąg CV oparty o motion gate, wybór snapshotu, analizę układu kart i publikację layoutu.
```

Remove wording that says `Snapshot-First i Legacy State-First`.

- [x] **Step 10: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v"
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m py_compile app_cv\main.py app_cv\tarotvision\pipelines\__init__.py app_cv\tarotvision\pipelines\snapshot_first.py"
```

Expected: all tests PASS and compile OK.

- [ ] **Step 11: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/main.py app_cv/tarotvision/pipelines/__init__.py app_cv/tests/test_pipelines_contract.py app_cv/tests/test_main_static_audit.py README.md .ai/PROJECT_STATE.md .ai/TASKS_INDEX.md
git -C E:\Antigravity\Projekty\TAROT add -u app_cv/tarotvision/pipelines/state_first_legacy.py
git -C E:\Antigravity\Projekty\TAROT commit -m "refactor: utrwal snapshot-first jako jedyny pipeline CV"
```

---

## Task 2: Unicode-Safe Image I/O i Reference Loader poza `main.py`

**Task ID:** `TASK-CV-SNAPSHOT-002`

**Files:**
- Create: `app_cv/tarotvision/image_io.py`
- Create: `app_cv/tarotvision/reference_loader.py`
- Create: `app_cv/tests/test_image_io.py`
- Create: `app_cv/tests/test_reference_loader.py`
- Modify: `app_cv/main.py`
- Modify: `app_cv/tarotvision/card_recognition.py`

- [x] **Step 1: Write image I/O tests**

Create `app_cv/tests/test_image_io.py`:

```python
import os
import tempfile
import unittest

import cv2
import numpy as np

from tarotvision.image_io import imread_grayscale_unicode, imwrite_unicode


class ImageIoTest(unittest.TestCase):
    def test_round_trip_polish_path_grayscale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "Światło_i_Cień_00.jpg")
            source = np.full((12, 16), 127, dtype=np.uint8)

            self.assertTrue(imwrite_unicode(path, source))
            loaded = imread_grayscale_unicode(path)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.shape, (12, 16))
        self.assertEqual(loaded.dtype, np.uint8)

    def test_missing_path_returns_none(self):
        loaded = imread_grayscale_unicode("Z:\\missing\\Światło_i_Cień.jpg")

        self.assertIsNone(loaded)

    def test_color_file_can_be_loaded_as_grayscale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "kolor_ąę.jpg")
            source = np.zeros((10, 10, 3), dtype=np.uint8)
            source[:, :, 1] = 255

            self.assertTrue(imwrite_unicode(path, source))
            loaded = imread_grayscale_unicode(path)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.ndim, 2)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run image I/O tests and verify failure**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_image_io -v"
```

Expected: FAIL because `tarotvision.image_io` does not exist.

- [x] **Step 3: Implement `image_io.py`**

Create `app_cv/tarotvision/image_io.py`:

```python
import os

import cv2
import numpy as np


def imread_unicode(path, flags=cv2.IMREAD_UNCHANGED):
    if not os.path.exists(path):
        return None
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)


def imread_grayscale_unicode(path):
    return imread_unicode(path, cv2.IMREAD_GRAYSCALE)


def imwrite_unicode(path, image, params=None):
    extension = os.path.splitext(path)[1]
    if not extension:
        return False
    ok, encoded = cv2.imencode(extension, image, params or [])
    if not ok:
        return False
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    encoded.tofile(path)
    return True
```

- [x] **Step 4: Verify image I/O tests pass**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_image_io -v"
```

Expected: `Ran 3 tests ... OK`.

- [x] **Step 5: Write reference loader tests**

Create `app_cv/tests/test_reference_loader.py`:

```python
import json
import os
import tempfile
import unittest

import cv2
import numpy as np

from tarotvision.image_io import imwrite_unicode
from tarotvision.reference_loader import load_active_reference_cards


class ReferenceLoaderTest(unittest.TestCase):
    def _write_card(self, path):
        img = np.zeros((120, 70), dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (60, 110), 255, 2)
        cv2.line(img, (10, 10), (60, 110), 255, 1)
        self.assertTrue(imwrite_unicode(path, img))

    def test_loads_polish_deck_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cv_dir = os.path.join(tmpdir, "biblioteka_talii", "światło_i_cień", "produkcja", "wzorce_cv")
            os.makedirs(cv_dir)
            self._write_card(os.path.join(cv_dir, "Światło_i_Cień_00.jpg"))
            manifest = {
                "version": 1,
                "decks": [{
                    "id": "swiatlo_i_cien",
                    "display_name": "Światło i Cień",
                    "prefix": "Światło_i_Cień",
                    "cv_path": "biblioteka_talii/światło_i_cień/produkcja/wzorce_cv",
                }],
            }
            active = {"version": 1, "active_decks": ["swiatlo_i_cien"]}
            manifest_path = os.path.join(tmpdir, "decks_manifest.json")
            active_path = os.path.join(tmpdir, "active_decks.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)
            with open(active_path, "w", encoding="utf-8") as f:
                json.dump(active, f)

            orb = cv2.ORB_create(nfeatures=500)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            result = load_active_reference_cards(
                project_root=tmpdir,
                manifest_path=manifest_path,
                active_decks_path=active_path,
                fallback_deck_id="swiatlo_i_cien",
                orb=orb,
                clahe=clahe,
            )

        self.assertIn("Światło_i_Cień_00", result.cards)
        self.assertEqual(result.loaded_deck_ids, ["swiatlo_i_cien"])
        self.assertEqual(result.skipped_files, [])

    def test_skips_unreadable_file_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cv_dir = os.path.join(tmpdir, "deck", "cv")
            os.makedirs(cv_dir)
            bad_path = os.path.join(cv_dir, "Bad_00.jpg")
            with open(bad_path, "wb") as f:
                f.write(b"not a jpeg")
            manifest_path = os.path.join(tmpdir, "manifest.json")
            active_path = os.path.join(tmpdir, "active.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({"decks": [{"id": "bad", "display_name": "Bad", "prefix": "Bad", "cv_path": "deck/cv"}]}, f)
            with open(active_path, "w", encoding="utf-8") as f:
                json.dump({"active_decks": ["bad"]}, f)

            result = load_active_reference_cards(
                project_root=tmpdir,
                manifest_path=manifest_path,
                active_decks_path=active_path,
                fallback_deck_id="bad",
                orb=cv2.ORB_create(nfeatures=500),
                clahe=cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)),
            )

        self.assertEqual(result.cards, {})
        self.assertEqual(len(result.skipped_files), 1)
        self.assertTrue(result.skipped_files[0].endswith("Bad_00.jpg"))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 6: Implement `reference_loader.py`**

Create `app_cv/tarotvision/reference_loader.py`:

```python
from dataclasses import dataclass
import glob
import json
import os

import cv2

from tarotvision.image_io import imread_grayscale_unicode


@dataclass(frozen=True)
class ReferenceLoadResult:
    cards: dict
    loaded_deck_ids: list
    skipped_files: list
    keypoint_counts: dict


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_matcher(descriptors):
    if descriptors is None or len(descriptors) == 0:
        return None
    try:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        matcher.add([descriptors])
        matcher.train()
        return matcher
    except cv2.error:
        return None


def _load_one_card(file_path, orb, clahe):
    card_name = os.path.basename(file_path).replace(".jpg", "")
    img = imread_grayscale_unicode(file_path)
    if img is None:
        return card_name, None
    img = clahe.apply(img)
    keypoints, descriptors = orb.detectAndCompute(img, None)
    if descriptors is not None:
        keypoints = keypoints[:500]
        descriptors = descriptors[:500]
    reversed_img = cv2.rotate(img, cv2.ROTATE_180)
    reversed_keypoints, reversed_descriptors = orb.detectAndCompute(reversed_img, None)
    return card_name, {
        "image": img,
        "keypoints": keypoints,
        "descriptors": descriptors,
        "reversed_image": reversed_img,
        "reversed_keypoints": reversed_keypoints,
        "reversed_descriptors": reversed_descriptors,
        "matcher": _build_matcher(descriptors),
    }


def load_active_reference_cards(project_root, manifest_path, active_decks_path,
                                fallback_deck_id, orb, clahe, active_ids=None):
    manifest = _load_json(manifest_path, {"decks": []})
    if active_ids is None:
        active_data = _load_json(active_decks_path, {"active_decks": []})
        active_ids = active_data.get("active_decks", [])
    if not active_ids:
        active_ids = [fallback_deck_id]

    decks_by_id = {deck.get("id"): deck for deck in manifest.get("decks", [])}
    cards = {}
    loaded_deck_ids = []
    skipped_files = []
    keypoint_counts = {}

    for deck_id in active_ids:
        deck = decks_by_id.get(deck_id)
        if not deck:
            continue
        cv_path = os.path.abspath(os.path.join(project_root, deck.get("cv_path", "")))
        file_paths = sorted(glob.glob(os.path.join(cv_path, "*.jpg")))
        if not file_paths:
            continue
        loaded_deck_ids.append(deck_id)
        for file_path in file_paths:
            card_name, card_data = _load_one_card(file_path, orb, clahe)
            if card_data is None:
                skipped_files.append(file_path)
                continue
            cards[card_name] = card_data
            keypoint_counts[card_name] = len(card_data.get("keypoints") or [])

    return ReferenceLoadResult(
        cards=cards,
        loaded_deck_ids=loaded_deck_ids,
        skipped_files=skipped_files,
        keypoint_counts=keypoint_counts,
    )
```

- [x] **Step 7: Replace duplicate loader code in `main.py`**

In `main.py`, import:

```python
from tarotvision.reference_loader import load_active_reference_cards
```

Replace the body of `load_reference_cards(active_ids=None)` with:

```python
def load_reference_cards(active_ids=None):
    """Wczytuje cyfrowe wzorce kart dla aktywnych talii sesji pod lockiem."""
    global reference_cards
    result = load_active_reference_cards(
        project_root=PROJECT_ROOT,
        manifest_path=decks_manifest_path,
        active_decks_path=active_decks_path,
        fallback_deck_id=DECK_NAME,
        orb=orb,
        clahe=clahe,
        active_ids=active_ids,
    )
    reference_cards.clear()
    reference_cards.update(result.cards)
    if result.loaded_deck_ids:
        log_event(
            f"[OK] Zaladowano talie aktywne: {result.loaded_deck_ids}; "
            f"wzorce={len(reference_cards)}, pominiete={len(result.skipped_files)}"
        )
    else:
        log_event("[BLAD] Nie zaladowano zadnych wzorcow CV dla aktywnych talii.")
    for skipped in result.skipped_files[:10]:
        log_event(f"[OSTRZEZENIE] Pominieto nieczytelny wzorzec CV: {skipped}")
    if "table_state" in globals() and table_state is not None:
        table_state.all_card_ids = list(reference_cards.keys())
        table_state.cards.clear()
        log_event("[TABLE_STATE] Zresetowano i zaktualizowano ID kart w TableState.")
```

If `table_state` is removed later with legacy cleanup, remove only the guarded block in the same task that removes `TableState` usage.

- [x] **Step 8: Update `card_recognition.load_reference_cards`**

In `app_cv/tarotvision/card_recognition.py`, replace `cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)` with:

```python
from tarotvision.image_io import imread_grayscale_unicode
```

and:

```python
img = imread_grayscale_unicode(file_path)
```

- [x] **Step 9: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_image_io app_cv.tests.test_reference_loader app_cv.tests.test_card_recognition -v"
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m py_compile app_cv\main.py app_cv\tarotvision\image_io.py app_cv\tarotvision\reference_loader.py app_cv\tarotvision\card_recognition.py"
```

Expected: tests PASS and compile OK.

- [ ] **Step 10: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/image_io.py app_cv/tarotvision/reference_loader.py app_cv/tests/test_image_io.py app_cv/tests/test_reference_loader.py app_cv/main.py app_cv/tarotvision/card_recognition.py
git -C E:\Antigravity\Projekty\TAROT commit -m "fix: laduj wzorce CV przez unicode-safe image io"
```

---

## Task 3: Snapshot-First Warp ArUco przed Analizą Kart

**Task ID:** `TASK-CV-SNAPSHOT-003`

**Files:**
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`
- Modify: `app_cv/tests/test_pipelines_contract.py`

- [x] **Step 1: Add unit test for warped analysis frame**

In `app_cv/tests/test_pipelines_contract.py`, add:

```python
    def test_snapshot_pipeline_analyzes_warped_frame_when_table_is_calibrated(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        camera_session.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        snapshot_analyzer = MagicMock()
        snapshot_analyzer.analyze.return_value.card_count = 0
        snapshot_analyzer.analyze.return_value.cards = []

        table_calibration = MagicMock()
        table_calibration.calibrated = True
        warped = np.full((720, 1280, 3), 77, dtype=np.uint8)
        table_calibration.warp_frame.return_value = warped
        table_calibration.status.return_value = {"calibrated": True, "marker_ids": [10, 11, 12, 13]}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

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
        )

        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=frame,
            motion_result=motion_result,
            frame_width=1280,
            frame_height=720,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_called_once()
        analyzed_frame = snapshot_analyzer.analyze.call_args.args[0]
        self.assertTrue(np.array_equal(analyzed_frame, warped))
```

- [x] **Step 2: Run test and verify failure**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_pipelines_contract.TestPipelinesContract.test_snapshot_pipeline_analyzes_warped_frame_when_table_is_calibrated -v"
```

Expected: FAIL because current pipeline analyzes `selected.frame`.

- [x] **Step 3: Implement warped analysis frame**

In `app_cv/tarotvision/pipelines/snapshot_first.py`, before:

```python
                result = self.snapshot_analyzer.analyze(selected.frame)
```

insert:

```python
                analysis_frame = selected.frame
                if self.table_calibration.calibrated:
                    warped_frame = self.table_calibration.warp_frame(selected.frame)
                    if warped_frame is not None:
                        analysis_frame = warped_frame
                        self.runtime_metrics.add("snapshot_analysis_warped", 1)
                    else:
                        self.runtime_metrics.add("snapshot_analysis_warped", 0)
                else:
                    self.runtime_metrics.add("snapshot_analysis_warped", 0)
```

Then replace:

```python
                result = self.snapshot_analyzer.analyze(selected.frame)
```

with:

```python
                result = self.snapshot_analyzer.analyze(analysis_frame)
```

- [x] **Step 4: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_pipelines_contract -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_pipelines_contract.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: analizuj snapshot na sprostowanej macie ArUco"
```

---

## Task 4: Diagnostyka Porażek Detekcji i Rozpoznania

**Task ID:** `TASK-CV-SNAPSHOT-004`

**Files:**
- Create: `app_cv/tarotvision/card_detection_debug.py`
- Create: `app_cv/tarotvision/recognition_debug.py`
- Create: `app_cv/tests/test_recognition_debug.py`
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
- Modify: `app_cv/tarotvision/card_recognition.py`
- Modify: `app_cv/tarotvision/pipelines/snapshot_first.py`

- [ ] **Step 1: Add recognition debug tests**

Create `app_cv/tests/test_recognition_debug.py`:

```python
import unittest

from tarotvision.recognition_debug import RecognitionDebug, top_match_summary


class RecognitionDebugTest(unittest.TestCase):
    def test_top_match_summary_sorts_by_score(self):
        debug = RecognitionDebug(
            crop_keypoints=120,
            top_matches=[
                {"name": "RWS_01", "score": 4.0, "match_count": 8, "inlier_ratio": 0.5},
                {"name": "Boski_02", "score": 9.0, "match_count": 12, "inlier_ratio": 0.75},
            ],
            reject_reason=None,
        )

        result = top_match_summary(debug, limit=1)

        self.assertEqual(result, [{
            "name": "Boski_02",
            "score": 9.0,
            "match_count": 12,
            "inlier_ratio": 0.75,
        }])

    def test_summary_handles_empty_debug(self):
        debug = RecognitionDebug(crop_keypoints=0, top_matches=[], reject_reason="no_descriptors")

        self.assertEqual(top_match_summary(debug), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement recognition debug data model**

Create `app_cv/tarotvision/recognition_debug.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RecognitionDebug:
    crop_keypoints: int
    top_matches: list
    reject_reason: str | None


def top_match_summary(debug, limit=5):
    sorted_matches = sorted(
        debug.top_matches,
        key=lambda item: item.get("score", 0.0),
        reverse=True,
    )
    return [
        {
            "name": item.get("name"),
            "score": float(item.get("score", 0.0)),
            "match_count": int(item.get("match_count", 0)),
            "inlier_ratio": float(item.get("inlier_ratio", 0.0)),
        }
        for item in sorted_matches[:limit]
    ]
```

- [ ] **Step 3: Extend recognition without breaking existing API**

In `app_cv/tarotvision/card_recognition.py`, import:

```python
from tarotvision.recognition_debug import RecognitionDebug
```

Add a new function after `recognize_card_crop`:

```python
def recognize_card_crop_with_debug(gray_crop, reference_cards, orb, matcher,
                                   min_good_matches=MIN_GOOD_MATCHES,
                                   lowe_ratio=LOWE_RATIO,
                                   min_inlier_ratio=MIN_INLIER_RATIO):
    result = recognize_card_crop(
        gray_crop,
        reference_cards,
        orb,
        matcher,
        min_good_matches=min_good_matches,
        lowe_ratio=lowe_ratio,
        min_inlier_ratio=min_inlier_ratio,
    )
    orb_crop = cv2.ORB_create(nfeatures=500)
    keypoints, descriptors = orb_crop.detectAndCompute(gray_crop, None)
    crop_keypoints = len(keypoints or [])
    if descriptors is None or len(descriptors) < min_good_matches:
        debug = RecognitionDebug(
            crop_keypoints=crop_keypoints,
            top_matches=[],
            reject_reason="not_enough_crop_descriptors",
        )
        return result, debug
    debug = RecognitionDebug(
        crop_keypoints=crop_keypoints,
        top_matches=[] if result is None else [{
            "name": result["name"],
            "score": float(result.get("match_count", 0)) * float(result.get("inlier_ratio", 0.0)),
            "match_count": int(result.get("match_count", 0)),
            "inlier_ratio": float(result.get("inlier_ratio", 0.0)),
        }],
        reject_reason=None if result is not None else "no_match_above_thresholds",
    )
    return result, debug
```

This first debug function is intentionally conservative: it records crop feature availability and accepted match. Task 8 expands it to top-k candidates.

- [ ] **Step 4: Add card detection debug artifact writer**

Create `app_cv/tarotvision/card_detection_debug.py`:

```python
import json
import os
from datetime import datetime

import cv2
import numpy as np

from tarotvision.image_io import imwrite_unicode


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def draw_quads(frame, quads):
    canvas = frame.copy()
    for index, quad in enumerate(quads):
        cv2.polylines(canvas, [np.asarray(quad, dtype=np.int32)], True, (0, 255, 0), 2)
        x, y, _, _ = cv2.boundingRect(np.asarray(quad, dtype=np.int32))
        cv2.putText(canvas, str(index), (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return canvas


def save_snapshot_debug_artifacts(directory, frame, quads, metadata):
    os.makedirs(directory, exist_ok=True)
    stem = _timestamp()
    raw_path = os.path.join(directory, f"{stem}_raw.jpg")
    overlay_path = os.path.join(directory, f"{stem}_quads.jpg")
    json_path = os.path.join(directory, f"{stem}_metadata.json")

    imwrite_unicode(raw_path, frame)
    imwrite_unicode(overlay_path, draw_quads(frame, quads))
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
    return {
        "raw": raw_path,
        "quads": overlay_path,
        "metadata": json_path,
    }
```

- [ ] **Step 5: Add analyzer diagnostics fields**

Modify `SnapshotAnalysisResult` in `snapshot_analyzer.py`:

```python
@dataclass(frozen=True)
class SnapshotAnalysisResult:
    cards: list
    card_count: int
    diagnostics: dict | None = None
```

In `SnapshotAnalyzer.analyze`, initialize:

```python
        diagnostics = {
            "quads_found": 0,
            "recognition_attempts": 0,
            "recognition_rejections": 0,
        }
```

After `for quad in self.find_quads(frame):`, set:

```python
        quads = self.find_quads(frame)
        diagnostics["quads_found"] = len(quads)
        for quad in quads:
```

Inside the loop before recognition:

```python
            diagnostics["recognition_attempts"] += 1
```

When recognition is false:

```python
                diagnostics["recognition_rejections"] += 1
```

Return:

```python
        return SnapshotAnalysisResult(
            cards=cards,
            card_count=len(cards),
            diagnostics=diagnostics,
        )
```

- [ ] **Step 6: Publish diagnostics metrics**

In `snapshot_first.py`, after `result = self.snapshot_analyzer.analyze(analysis_frame)`, add:

```python
                diagnostics = result.diagnostics or {}
                self.runtime_metrics.add("snapshot_quads_found", diagnostics.get("quads_found", 0))
                self.runtime_metrics.add("snapshot_recognition_attempts", diagnostics.get("recognition_attempts", 0))
                self.runtime_metrics.add("snapshot_recognition_rejections", diagnostics.get("recognition_rejections", 0))
```

- [ ] **Step 7: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_recognition_debug app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract -v"
```

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/card_detection_debug.py app_cv/tarotvision/recognition_debug.py app_cv/tarotvision/card_recognition.py app_cv/tarotvision/snapshot_analyzer.py app_cv/tarotvision/pipelines/snapshot_first.py app_cv/tests/test_recognition_debug.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj diagnostyke porazek snapshot-first"
```

---

## Task 5: Multi-Profile Card Detection dla Ciemnych Talii i Mat

**Task ID:** `TASK-CV-SNAPSHOT-005`

**Files:**
- Create: `app_cv/tarotvision/card_detection_profiles.py`
- Create: `app_cv/tests/test_card_detection_profiles.py`
- Modify: `app_cv/tarotvision/card_detection.py`
- Modify: `app_cv/tarotvision/snapshot_analyzer.py`

- [ ] **Step 1: Write detector profile tests**

Create `app_cv/tests/test_card_detection_profiles.py`:

```python
import unittest

import cv2
import numpy as np

from tarotvision.card_detection_profiles import (
    DetectionProfile,
    find_card_quads_multi_profile,
)


class CardDetectionProfilesTest(unittest.TestCase):
    def test_detects_dark_card_on_dark_green_background_with_bright_border(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        frame[:, :] = (20, 55, 35)
        cv2.rectangle(frame, (325, 171), (475, 429), (18, 24, 22), -1)
        cv2.rectangle(frame, (325, 171), (475, 429), (120, 150, 130), 3)

        result = find_card_quads_multi_profile(frame)

        self.assertGreaterEqual(len(result.quads), 1)
        self.assertIn(result.best_profile, {"canny_low", "adaptive_light", "adaptive_dark"})

    def test_deduplicates_same_quad_from_multiple_profiles(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(frame, (325, 171), (475, 429), (255, 255, 255), -1)

        result = find_card_quads_multi_profile(frame)

        self.assertEqual(len(result.quads), 1)

    def test_returns_debug_counts_per_profile(self):
        frame = np.zeros((600, 800, 3), dtype=np.uint8)

        result = find_card_quads_multi_profile(frame)

        self.assertIn("profiles", result.debug)
        self.assertGreaterEqual(len(result.debug["profiles"]), 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_card_detection_profiles -v"
```

Expected: FAIL because `card_detection_profiles.py` does not exist.

- [ ] **Step 3: Implement profile detector**

Create `app_cv/tarotvision/card_detection_profiles.py`:

```python
from dataclasses import dataclass

import cv2
import numpy as np

from tarotvision.card_detection import find_card_quads


@dataclass(frozen=True)
class DetectionProfile:
    name: str
    mode: str
    canny_low: int = 30
    canny_high: int = 100
    min_area_ratio: float = 0.001
    contour_mode: str = "list"


@dataclass(frozen=True)
class MultiProfileDetectionResult:
    quads: list
    best_profile: str | None
    debug: dict


DEFAULT_PROFILES = [
    DetectionProfile("canny_low", "canny", canny_low=20, canny_high=80, min_area_ratio=0.001, contour_mode="list"),
    DetectionProfile("canny_default", "canny", canny_low=50, canny_high=150, min_area_ratio=0.005, contour_mode="external"),
    DetectionProfile("adaptive_light", "adaptive_light", min_area_ratio=0.001, contour_mode="list"),
    DetectionProfile("adaptive_dark", "adaptive_dark", min_area_ratio=0.001, contour_mode="list"),
]


def _gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def _profile_frame(frame, profile):
    gray = _gray(frame)
    if profile.mode == "canny":
        return frame
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    if profile.mode == "adaptive_light":
        mask = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 3,
        )
        return mask
    if profile.mode == "adaptive_dark":
        mask = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 3,
        )
        return mask
    return frame


def _bbox(quad):
    x, y, w, h = cv2.boundingRect(np.asarray(quad, dtype=np.int32))
    return x, y, w, h


def _iou_box(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1 = max(ax, bx)
    y1 = max(ay, by)
    x2 = min(ax + aw, bx + bw)
    y2 = min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = aw * ah + bw * bh - inter
    return 0.0 if union <= 0 else inter / union


def _dedupe_quads(quads, iou_threshold=0.85):
    accepted = []
    accepted_boxes = []
    for quad in sorted(quads, key=lambda item: cv2.contourArea(item), reverse=True):
        box = _bbox(quad)
        if any(_iou_box(box, existing) >= iou_threshold for existing in accepted_boxes):
            continue
        accepted.append(quad)
        accepted_boxes.append(box)
    return accepted


def find_card_quads_multi_profile(frame, profiles=None, max_candidates=10):
    profiles = profiles or DEFAULT_PROFILES
    all_quads = []
    debug_profiles = []
    best_profile = None
    best_count = 0

    for profile in profiles:
        profile_input = _profile_frame(frame, profile)
        quads, debug = find_card_quads(
            profile_input,
            min_area_ratio=profile.min_area_ratio,
            canny_low=profile.canny_low,
            canny_high=profile.canny_high,
            contour_mode=profile.contour_mode,
            max_candidates=max_candidates,
            return_debug=True,
        )
        all_quads.extend(quads)
        if len(quads) > best_count:
            best_count = len(quads)
            best_profile = profile.name
        debug_profiles.append({
            "name": profile.name,
            "mode": profile.mode,
            "quads": len(quads),
            "contours_total": debug.get("contours_total", 0),
            "candidates_after_quad": debug.get("candidates_after_quad", 0),
        })

    deduped = _dedupe_quads(all_quads)[:max_candidates]
    return MultiProfileDetectionResult(
        quads=deduped,
        best_profile=best_profile,
        debug={"profiles": debug_profiles, "quads_final": len(deduped)},
    )
```

- [ ] **Step 4: Integrate with SnapshotAnalyzer**

In `snapshot_analyzer.py`, import:

```python
from tarotvision.card_detection_profiles import find_card_quads_multi_profile
```

Change constructor default:

```python
        self.find_quads = find_quads or self._find_quads_default
```

Add method inside `SnapshotAnalyzer`:

```python
    def _find_quads_default(self, frame):
        return find_card_quads_multi_profile(frame).quads
```

Keep the existing `find_quads` dependency injection behavior for tests.

- [ ] **Step 5: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_card_detection_profiles app_cv.tests.test_snapshot_analyzer -v"
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/card_detection_profiles.py app_cv/tarotvision/snapshot_analyzer.py app_cv/tests/test_card_detection_profiles.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj wieloprofilowa detekcje kart snapshot-first"
```

---

## Task 6: Opcjonalny Model Pustej Maty dla Background-Diff

**Task ID:** `TASK-CV-SNAPSHOT-006`

**Files:**
- Create: `app_cv/tarotvision/background_model.py`
- Create: `app_cv/tests/test_background_model.py`
- Modify: `app_cv/tarotvision/card_detection_profiles.py`
- Modify: `app_cv/tarotvision/tuning_protocol.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write background model tests**

Create `app_cv/tests/test_background_model.py`:

```python
import unittest

import cv2
import numpy as np

from tarotvision.background_model import BackgroundModel


class BackgroundModelTest(unittest.TestCase):
    def test_foreground_mask_detects_card_added_to_empty_mat(self):
        empty = np.zeros((100, 140, 3), dtype=np.uint8)
        empty[:, :] = (20, 55, 35)
        frame = empty.copy()
        cv2.rectangle(frame, (45, 20), (95, 80), (80, 90, 85), -1)

        model = BackgroundModel()
        model.capture(empty)
        mask = model.foreground_mask(frame, threshold=20)

        changed_ratio = float(np.count_nonzero(mask)) / mask.size
        self.assertGreater(changed_ratio, 0.15)

    def test_uncaptured_model_reports_inactive(self):
        model = BackgroundModel()

        self.assertFalse(model.active)
        self.assertIsNone(model.foreground_mask(np.zeros((10, 10, 3), dtype=np.uint8)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement background model**

Create `app_cv/tarotvision/background_model.py`:

```python
import cv2
import numpy as np


class BackgroundModel:
    def __init__(self):
        self._gray_background = None

    @property
    def active(self):
        return self._gray_background is not None

    def capture(self, frame):
        arr = np.asarray(frame)
        if arr.ndim == 2:
            gray = arr
        else:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        self._gray_background = gray.copy()

    def clear(self):
        self._gray_background = None

    def foreground_mask(self, frame, threshold=18):
        if self._gray_background is None:
            return None
        arr = np.asarray(frame)
        if arr.ndim == 2:
            gray = arr
        else:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        if gray.shape != self._gray_background.shape:
            return None
        diff = cv2.absdiff(self._gray_background, gray)
        _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return mask
```

- [ ] **Step 3: Extend tuning protocol**

In `app_cv/tarotvision/tuning_protocol.py`, add allowed types:

```python
"background_capture",
"background_clear",
```

No extra payload fields are required. The parser should return `ControlMessage(type=message_type)`.

Add tests to `app_cv/tests/test_tuning_protocol.py`:

```python
    def test_parses_background_capture(self):
        message = parse_control_message('{"type": "background_capture"}')

        self.assertEqual(message.type, "background_capture")

    def test_parses_background_clear(self):
        message = parse_control_message('{"type": "background_clear"}')

        self.assertEqual(message.type, "background_clear")
```

- [ ] **Step 4: Wire model in `main.py`**

Import:

```python
from tarotvision.background_model import BackgroundModel
```

Create global:

```python
background_model = BackgroundModel()
```

In control message handling:

```python
    if message.type == "background_clear":
        background_model.clear()
        add_operator_warning("Wyczyszczono model pustej maty")
        return
```

For `background_capture`, add a flag:

```python
pending_background_capture = False
```

In handler:

```python
    global pending_background_capture
    if message.type == "background_capture":
        pending_background_capture = True
        add_operator_warning("Zlecono przechwycenie pustej maty z nastepnej klatki")
        return
```

In the main loop after successful `ret, frame = camera_session.read()`:

```python
    if pending_background_capture:
        capture_frame = table_calibration.warp_frame(frame) if table_calibration.calibrated else frame
        if capture_frame is not None:
            background_model.capture(capture_frame)
            add_operator_warning("Przechwycono model pustej maty")
        pending_background_capture = False
```

- [ ] **Step 5: Pass background model to detector**

This step is integration-only. Add an optional `background_model` argument to `find_card_quads_multi_profile(frame, profiles=None, max_candidates=10, background_model=None)`.

If active:

```python
    if background_model is not None and background_model.active:
        mask = background_model.foreground_mask(frame)
        if mask is not None:
            bg_quads, bg_debug = find_card_quads(
                mask,
                min_area_ratio=0.001,
                canny_low=20,
                canny_high=80,
                contour_mode="list",
                max_candidates=max_candidates,
                return_debug=True,
            )
            all_quads.extend(bg_quads)
            debug_profiles.append({
                "name": "background_diff",
                "mode": "background_diff",
                "quads": len(bg_quads),
                "contours_total": bg_debug.get("contours_total", 0),
                "candidates_after_quad": bg_debug.get("candidates_after_quad", 0),
            })
```

- [ ] **Step 6: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_background_model app_cv.tests.test_tuning_protocol app_cv.tests.test_card_detection_profiles -v"
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/background_model.py app_cv/tarotvision/card_detection_profiles.py app_cv/tarotvision/tuning_protocol.py app_cv/main.py app_cv/tests/test_background_model.py app_cv/tests/test_tuning_protocol.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj model pustej maty dla detekcji snapshot-first"
```

---

## Task 7: Recognition-Aware Snapshot Autotuning

**Task ID:** `TASK-CV-SNAPSHOT-007`

**Files:**
- Create: `app_cv/tarotvision/snapshot_autotune.py`
- Create: `app_cv/tests/test_snapshot_autotune.py`
- Modify: `app_cv/tarotvision/auto_tuner.py`
- Modify: `app_cv/tarotvision/runtime_config.py`

- [ ] **Step 1: Write snapshot autotune tests**

Create `app_cv/tests/test_snapshot_autotune.py`:

```python
import unittest

import cv2
import numpy as np

from tarotvision.snapshot_autotune import score_snapshot_candidate


class SnapshotAutotuneTest(unittest.TestCase):
    def test_score_rewards_geometry_and_recognition(self):
        quad_score = 0.8
        recognition = {"match_count": 24, "inlier_ratio": 0.75}

        score = score_snapshot_candidate(quad_score, recognition)

        self.assertGreater(score, 1.0)

    def test_score_penalizes_missing_recognition(self):
        score = score_snapshot_candidate(quad_score=0.9, recognition=None)

        self.assertLess(score, 0.9)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement `snapshot_autotune.py`**

Create `app_cv/tarotvision/snapshot_autotune.py`:

```python
def score_snapshot_candidate(quad_score, recognition):
    geometry = float(quad_score)
    if recognition is None:
        return geometry * 0.4
    match_count = float(recognition.get("match_count", 0))
    inlier_ratio = float(recognition.get("inlier_ratio", 0.0))
    recognition_score = min(match_count / 30.0, 1.0) * max(0.0, min(inlier_ratio, 1.0))
    return geometry * 0.45 + recognition_score * 1.10
```

- [ ] **Step 3: Add runtime config parameters for detector profiles**

In `runtime_config.py`, add:

```python
    "CARD_DETECT_MAX_CANDIDATES": TunableParameter("CARD_DETECT_MAX_CANDIDATES", 10.0, 1.0, 30.0, True),
    "CARD_DETECT_MIN_AREA_RATIO": TunableParameter("CARD_DETECT_MIN_AREA_RATIO", 0.001, 0.0001, 0.02, True),
```

Add tests in `app_cv/tests/test_runtime_config.py`:

```python
    def test_card_detector_parameters_are_exported(self):
        config = RuntimeConfig()
        metadata = config.metadata()

        self.assertIn("CARD_DETECT_MAX_CANDIDATES", metadata)
        self.assertIn("CARD_DETECT_MIN_AREA_RATIO", metadata)
```

- [ ] **Step 4: Extend offline autotuner scoring**

In `auto_tuner.py`, do not remove `tune_card_detection_params`. Add a new function:

```python
def tune_snapshot_detection_params(frame, recognize_crop, crop_card, search_space=None, max_iterations=250):
    base_result = tune_card_detection_params(
        frame,
        search_space=search_space,
        max_iterations=max_iterations,
    )
    recognition = None
    if base_result["best_candidate_bbox"] is not None:
        x, y, w, h = base_result["best_candidate_bbox"]
        quad = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]], dtype=np.int32)
        crop = crop_card(frame, quad)
        recognition = recognize_crop(crop)
    base_result["recognition"] = recognition
    from tarotvision.snapshot_autotune import score_snapshot_candidate
    base_result["recognition_aware_score"] = score_snapshot_candidate(
        base_result["best_score"],
        recognition,
    )
    return base_result
```

- [ ] **Step 5: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_snapshot_autotune app_cv.tests.test_auto_tuner app_cv.tests.test_runtime_config -v"
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add app_cv/tarotvision/snapshot_autotune.py app_cv/tarotvision/auto_tuner.py app_cv/tarotvision/runtime_config.py app_cv/tests/test_snapshot_autotune.py app_cv/tests/test_runtime_config.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj recognition-aware autotuning snapshotow"
```

---

## Task 8: Local Benchmark Script dla Talii i Mat

**Task ID:** `TASK-CV-SNAPSHOT-008`

**Files:**
- Create: `scripts/benchmark_snapshot_recognition.py`
- Create: `app_cv/tests/test_benchmark_snapshot_recognition.py`
- Modify: `README.md`

- [ ] **Step 1: Define fixture convention**

Use this directory convention for local, non-committed operator samples:

```text
testdata/snapshots/{deck_id}/{mat_id}/*.jpg
```

Example:

```text
testdata/snapshots/boski/dark_green/001.jpg
testdata/snapshots/magic/dark_green/001.jpg
testdata/snapshots/rider-waite-smith/dark_green/001.jpg
```

Do not commit physical camera samples unless Michał explicitly approves.

- [ ] **Step 2: Write script smoke test**

Create `app_cv/tests/test_benchmark_snapshot_recognition.py`:

```python
import unittest

from scripts.benchmark_snapshot_recognition import summarize_results


class BenchmarkSnapshotRecognitionTest(unittest.TestCase):
    def test_summarize_results_counts_success_rate(self):
        rows = [
            {"accepted": True, "deck_id": "boski"},
            {"accepted": False, "deck_id": "boski"},
            {"accepted": True, "deck_id": "magic"},
        ]

        summary = summarize_results(rows)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["accepted"], 2)
        self.assertAlmostEqual(summary["accept_rate"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Implement script**

Create `scripts/benchmark_snapshot_recognition.py`:

```python
import argparse
import csv
import glob
import json
import os
import sys


def summarize_results(rows):
    total = len(rows)
    accepted = sum(1 for row in rows if row.get("accepted"))
    return {
        "total": total,
        "accepted": accepted,
        "accept_rate": 0.0 if total == 0 else accepted / total,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    rows = []
    for path in sorted(glob.glob(os.path.join(args.input, "*", "*", "*.jpg"))):
        parts = os.path.normpath(path).split(os.sep)
        deck_id = parts[-3]
        mat_id = parts[-2]
        rows.append({
            "path": path,
            "deck_id": deck_id,
            "mat_id": mat_id,
            "accepted": False,
            "card_count": 0,
        })

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "deck_id", "mat_id", "accepted", "card_count"])
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps(summarize_results(rows), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

This first commit creates a stable CLI and output contract. A later patch wires it to real `SnapshotAnalyzer` after detector hardening is in place.

- [ ] **Step 4: Verify**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;. && python -m unittest app_cv.tests.test_benchmark_snapshot_recognition -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add scripts/benchmark_snapshot_recognition.py app_cv/tests/test_benchmark_snapshot_recognition.py README.md
git -C E:\Antigravity\Projekty\TAROT commit -m "test: dodaj kontrakt benchmarku snapshot recognition"
```

---

## Task 9: YOLO OBB Spike jako Osobny, Licencyjnie Bramkowany Plan

**Task ID:** `TASK-CV-OBB-SPIKE-001`

**Files:**
- Create: `docs/superpowers/plans/2026-06-01-yolo-obb-spike-plan.md`
- Modify: `.ai/TASKS_INDEX.md`

- [ ] **Step 1: Write separate spike plan**

Create `docs/superpowers/plans/2026-06-01-yolo-obb-spike-plan.md` with this scope:

```markdown
# YOLO OBB Spike Plan

Goal: Ocenić, czy OBB detector daje istotnie lepszą lokalizację kart niż OpenCV multi-profile detector na snapshotach z fizycznych talii i mat.

Hard Gate:
- Nie dodawać Ultralytics do runtime TarotVision.
- Nie commitować wag `.pt`, `.onnx` ani datasetu zdjęć bez zgody Michała.
- Nie integrować AGPL dependency z aplikacją produkcyjną bez decyzji licencyjnej.

Candidate Models:
- YOLO11n-obb
- YOLO26n-obb

Evaluation:
- Dataset lokalny: `testdata/snapshots/{deck_id}/{mat_id}/*.jpg`
- Etykiety OBB: jedna klasa `card`
- Metryki: card localization recall, false positives on empty mat, inference ms on CPU, inference ms on target GPU if available.

Exit Criteria:
- GREEN: OBB improves recall on dark decks/dark mats by at least 15 percentage points with acceptable latency and licensing path.
- YELLOW: OBB improves recall but license or latency blocks runtime use.
- RED: OpenCV multi-profile detector is close enough or better for current needs.
```

- [ ] **Step 2: Register spike in `.ai/TASKS_INDEX.md`**

Add row:

```markdown
| **TASK-CV-OBB-SPIKE-001** | `IN_PROGRESS` | `task/cv-obb-spike-001-yolo-eval` | Gemini/Codex | Licencyjnie odseparowana ewaluacja YOLO OBB dla lokalizacji kart | 2026-06-01 | Plan only |
```

- [ ] **Step 3: Commit**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT add docs/superpowers/plans/2026-06-01-yolo-obb-spike-plan.md .ai/TASKS_INDEX.md
git -C E:\Antigravity\Projekty\TAROT commit -m "docs: zaplanuj odseparowany spike yolo obb"
```

---

## Task 10: Full Verification, Handoff i Dokumentacja Sesji

**Task ID:** `TASK-CV-SNAPSHOT-009`

**Files:**
- Modify: `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`
- Modify: `.ai/PROJECT_STATE.md`
- Modify: `.ai/TASKS_INDEX.md`
- Create or modify task files under `.ai/tasks/TASK-CV-SNAPSHOT-*/`

- [ ] **Step 1: Run backend test suite**

Run:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Expected: all tests PASS. If failures are unrelated to the current branch, document exact failures in `TEST_REPORT.md` and do not claim full green.

- [ ] **Step 2: Run frontend build**

Run:

```powershell
cmd.exe /c npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: build PASS. Existing Vite warnings about chunk size and ineffective dynamic import are acceptable unless they change into errors.

- [ ] **Step 3: Update plan Session Status**

Append a concrete session block with real values from `git log --oneline -5` and the executed verification commands. Use this exact shape, replacing the sample commit hashes with the actual hashes from the current branch before committing:

```markdown
## Session Status (2026-06-01, Codex/Gemini)

Completed:
- abc1234: refactor: utrwal snapshot-first jako jedyny pipeline CV
- def5678: fix: laduj wzorce CV przez unicode-safe image io

Verification:
- `python -m unittest discover -s app_cv\tests -v` -> PASS/FAIL
- `npm --prefix app_ar run build` -> PASS/FAIL

Remaining:
- TASK-CV-SNAPSHOT-004: diagnostyka porażek snapshot-first
```

Do not commit the sample hashes above. They are examples of the required line format.

- [ ] **Step 4: Create Gemini handoff**

For each task directory under `.ai/tasks/TASK-CV-SNAPSHOT-XXX/`, include a handoff with concrete values. This is the required shape; fill it from the real branch state and test output before committing:

```markdown
# GEMINI HANDOFF — TASK-CV-SNAPSHOT-XXX

Base: real base commit hash from `git rev-parse HEAD~1`
Head: real head commit hash from `git rev-parse HEAD`
Zakres:
- Usunięto runtime legacy state-first z backendu.

Weryfikacja:
- `python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_pipelines_contract -v` => PASS

Ryzyka:
- Brak znanych ryzyk runtime poza koniecznością live smoke testu z kamerą.

Następny krok:
- Uruchomić TASK-CV-SNAPSHOT-002 i sprawdzić ładowanie talii Światło i Cień.
```

- [ ] **Step 5: Final status**

Run:

```powershell
git -C E:\Antigravity\Projekty\TAROT status --short --branch
git -C E:\Antigravity\Projekty\TAROT log --oneline -5
```

Expected: clean worktree after commit, unless there are explicitly documented uncommitted operator artifacts.

---

## Acceptance Criteria

- `StateFirstLegacyPipeline` no longer exists in production code, exports, runtime selection, or tests.
- `TAROTVISION_SNAPSHOT_FIRST` is no longer needed; snapshot-first is the only backend CV pipeline.
- `README.md` and `.ai/PROJECT_STATE.md` no longer present state-first as the active direction.
- Wzorce CV z polskimi ścieżkami, zwłaszcza `Światło_i_Cień`, loadują się przez Unicode-safe image I/O.
- Snapshot analysis uses ArUco-warped frame when calibration is available.
- Metrics expose at least: `snapshot_quads_found`, `snapshot_recognition_attempts`, `snapshot_recognition_rejections`, `snapshot_analysis_warped`.
- Multi-profile detector can detect synthetic dark card on dark green background.
- Optional background model can be captured and cleared through validated control messages.
- Autotuning scoring can include recognition quality, not only geometry.
- No Ultralytics/YOLO runtime dependency is added in this plan.
- Full backend tests and frontend build pass before final handoff.

## Out of Scope

- Training YOLO/OBB models.
- Adding Ultralytics as runtime dependency.
- Committing physical camera samples.
- Rewriting frontend Studio UI beyond minor metrics display needed for existing payload fields.
- Reintroducing continuous state-first recognition.

## Immediate Next Action

Start with `TASK-CV-SNAPSHOT-001`: remove legacy state-first from code, tests and docs. This prevents future agents from improving the wrong pipeline.
