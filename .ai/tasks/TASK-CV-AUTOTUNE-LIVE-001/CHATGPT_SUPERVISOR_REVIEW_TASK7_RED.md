# CHATGPT_SUPERVISOR_REVIEW — TASK 7 / RED LIVE SMOKE

## Date

2026-06-03

## Reviewed Commit

`0a044c2597b5ced4c86c7818ff6cdb32fc51152a`

## Summary

Task 7 live smoke został zapisany poprawnie jako RED. Automatyczna weryfikacja przeszła:

- targeted event-first suite: PASS, 47 testów,
- full backend suite: PASS, 300 testów,
- frontend build: PASS, tylko znane ostrzeżenia Vite.

Live smoke zatrzymał się na pierwszym kroku: `Pusta mata` po `autotune_start empty` została na `0/3`.

Zaobserwowany stan live:

```text
empty_reference_capture_active=true
empty_reference_frame_count=0
background_reference_active=false
snapshot_samples_taken=1.0
snapshot_rejected_count=1.0
stable_for_ms=0.0
marker_ids=[] później w metrykach
```

Log sesji zawierał tylko `empty_stage_started`; nie powstały `sample_collected` ani `stage_completed`.

## Decision

**PROVISIONAL_BLOCKED**

Nie przechodzić do merge ani PR finalnego. Nie uznawać Task 7 za zakończony. Najpierw potrzebny jest mały fix diagnostyczno-jakościowy dla ścieżki `Pusta mata`.

## Risk Level

**HIGH**

Bez poprawnego `empty_reference` cały event-first pipeline nie ma stabilnej podstawy. Dopóki `Pusta mata` nie zbierze `3/3` i nie ustawi `background_reference_active=true`, nie wolno uznawać event-first runtime za gotowy.

## Probable Root Cause

Najbardziej prawdopodobny problem nie leży w `ChangeDetector` ani w `empty_reference_capture_active`, tylko wcześniej: w jakościowej selekcji snapshotu.

W `SnapshotFirstPipeline` po pobraniu próbek wykonywane jest:

```python
selected = choose_best_snapshot(samples)
if selected is None:
    self.snapshot_gate.mark_rejected()
    layout_snapshot["snapshot_reject_reason"] = "all_samples_rejected"
    self.runtime_metrics.add("snapshot_rejected_count", 1)
```

Jeżeli `choose_best_snapshot()` odrzuci próbkę, pipeline kończy cykl przed `_record_autotune_sample()` i przed dodaniem klatki do `empty_reference_frames`.

To pasuje do obserwacji live:

```text
snapshot_samples_taken=1.0
snapshot_rejected_count=1.0
empty_reference_capture_active=true
empty_reference_frame_count=0
```

## Technical Cause Candidate

`choose_best_snapshot()` używa `score_snapshot()`, które odrzuca ramkę przez:

- `too_dark`,
- `too_bright`,
- `low_contrast`,
- `blurry`.

Dla pustej maty taki filtr może być zbyt rygorystyczny. Pusta mata może być prawidłową referencją właśnie wtedy, gdy jest mało kontrastowa i ma mało tekstury.

Obecny filtr jakości jest sensowny dla snapshotów z kartami, ale niekoniecznie dla etapu `Pusta mata`.

## Required Next Task

Utworzyć mały fix-task:

**TASK-CV-EVENT-FIRST-LIVE-FIX-001 — Empty Reference Snapshot Quality Path**

### Goal

Odblokować live smoke `Pusta mata`, aby etap `empty` mógł zebrać `3/3` ramek referencyjnych w realnych warunkach kamery/maty, bez przywracania globalnej detekcji kart.

### Scope

- `app_cv/tarotvision/pipelines/snapshot_first.py`
- `app_cv/tarotvision/snapshot_quality.py` tylko jeśli konieczne
- `app_cv/tests/test_pipelines_contract.py`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`

### Out of Scope

- Nie zmieniać `ChangeDetector`.
- Nie zmieniać `SnapshotAnalyzer`.
- Nie zmieniać ORB/FLANN.
- Nie zmieniać Studio UI.
- Nie implementować nowych funkcji CV.
- Nie merge do `master`.

## Recommended Implementation

Dodać osobną ścieżkę wyboru snapshotu dla `empty_reference_capture_active=True`.

Najprostszy wariant:

```python
if self.empty_reference_capture_active:
    selected = choose_best_snapshot(
        samples,
        min_contrast=0.0,
        min_blur_score=0.0,
    )
else:
    selected = choose_best_snapshot(samples)
```

Bezpieczniejszy wariant MVP:

```python
if self.empty_reference_capture_active:
    selected = choose_best_snapshot(
        samples,
        min_brightness=10.0,
        max_brightness=250.0,
        min_contrast=0.0,
        min_blur_score=0.0,
    )
else:
    selected = choose_best_snapshot(samples)
```

Ta zmiana ma dotyczyć wyłącznie etapu `Pusta mata`, nie normalnej analizy kart.

## Required Diagnostics

Dodać metryki lub layout diagnostics pokazujące powód odrzucenia snapshotu, przynajmniej na czas live smoke:

```text
snapshot_quality_reject_reason
snapshot_quality_brightness
snapshot_quality_contrast
snapshot_quality_blur_score
```

`score_snapshot()` już zwraca `reject_reason`, więc nie trzeba wymyślać nowej diagnostyki od zera.

## Required Tests

Dodać test regresyjny:

```python
def test_empty_reference_capture_accepts_low_contrast_empty_mat_snapshot(self):
    # arrange:
    # - empty_reference_capture_active=True
    # - samples zawierają pustą/niskokontrastową matę
    # - normalny choose_best_snapshot odrzuciłby ją przez low_contrast albo blurry
    #
    # act:
    # - process_frame(...)
    #
    # assert:
    # - recorder dostaje próbkę
    # - empty_reference_frames rośnie
    # - snapshot_reject_reason != "all_samples_rejected"
```

Dodać test diagnostyczny:

```python
def test_snapshot_rejection_exposes_quality_reason(self):
    # arrange:
    # - sample odrzucony przez score_snapshot
    #
    # assert:
    # - metrics/layout zawiera reject reason oraz brightness/contrast/blur_score
```

## Acceptance Criteria

- `autotune_start empty` nie zostaje na `0/3` z powodu `all_samples_rejected` przy stabilnej pustej macie.
- `empty_reference_frame_count` rośnie do `3/3`.
- Po trzeciej próbce wykonywane jest `BackgroundModel.capture_many()`.
- `background_reference_active=true` po udanej finalizacji.
- `BackgroundModel.changed_ratio(current_empty_frame, threshold=20)` jest wywołane.
- Normalna ścieżka rozpoznawania kart nadal używa dotychczasowych progów jakości.
- Full backend tests PASS.
- Po fixie powtórzyć pełny Task 7 live smoke.

## Required Next Action

Nie kontynuować dużych zmian. Następna sesja powinna zacząć się od małego taska `TASK-CV-EVENT-FIRST-LIVE-FIX-001`, potem powtórzyć Task 7 od początku:

1. `Pusta mata` — 3/3 i aktywna referencja,
2. stabilna pusta mata — brak false positives,
3. jedna karta,
4. trzy karty,
5. no-change hold previous,
6. removal,
7. global shift / warning.
