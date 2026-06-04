# NEXT ACTION AFTER RED LIVE SMOKE

## Status

**PROVISIONAL_BLOCKED**

Task 7 `Live Smoke` ma wynik RED. Nie wykonywać merge ani finalnego PR przed zielonym live smoke z fizyczną kamerą.

## Full Supervisor Review

Pełne review i wymagany następny task zapisano tutaj:

` .ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHATGPT_SUPERVISOR_REVIEW_TASK7_RED.md`

## Problem

`autotune_start empty` aktywuje `empty_reference_capture_active=true`, ale etap `Pusta mata` zostaje na `0/3`.

Zaobserwowane metryki live:

```text
empty_reference_capture_active=true
empty_reference_frame_count=0
background_reference_active=false
snapshot_samples_taken=1.0
snapshot_rejected_count=1.0
stable_for_ms=0.0
```

## Probable Cause

Najbardziej prawdopodobna przyczyna: snapshot pustej maty jest odrzucany przez `choose_best_snapshot()` / `score_snapshot()` przed wywołaniem recordera autotuningu.

Obecne progi jakości są sensowne dla snapshotów z kartami, ale mogą być zbyt rygorystyczne dla pustej maty, która może naturalnie mieć niski kontrast albo niski blur score.

## Required Next Task

`TASK-CV-EVENT-FIRST-LIVE-FIX-001 — Empty Reference Snapshot Quality Path`

Minimalny zakres:

1. Dodać osobną ścieżkę wyboru snapshotu dla `empty_reference_capture_active=True`.
2. Dla pustej maty poluzować `min_contrast` i `min_blur_score`, nie zmieniając normalnej ścieżki kart.
3. Dodać diagnostykę powodu odrzucenia snapshotu:
   - `snapshot_quality_reject_reason`,
   - `snapshot_quality_brightness`,
   - `snapshot_quality_contrast`,
   - `snapshot_quality_blur_score`.
4. Dodać test regresyjny: pusta niskokontrastowa mata przy `empty_reference_capture_active=True` nie może utknąć jako `all_samples_rejected`.
5. Po fixie powtórzyć pełny Task 7 live smoke.

## Do Not Do

- Nie zmieniać `ChangeDetector`.
- Nie zmieniać `SnapshotAnalyzer`.
- Nie zmieniać ORB/FLANN.
- Nie robić dużego refaktoru.
- Nie merge do `master`.
