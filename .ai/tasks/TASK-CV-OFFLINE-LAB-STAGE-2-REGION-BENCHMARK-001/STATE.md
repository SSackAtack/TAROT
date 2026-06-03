# Stan Prac — TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001

## 1. Status Ogólny

* **Status:** `DONE`
* **Realizator (Owner):** Codex
* **Gałąź Git:** `task/cv-event-first-plan-001-clarify-autotune-runtime`
* **Data:** 2026-06-03

---

## TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001

### Summary

Implemented isolated Stage 2 Region Segmentation benchmark.

### Input

Stage 1 approved method: `gray_absdiff_gaussian`.

Fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

### Methods tested

- `baseline_components`
- `morph_close_components`
- `dilate_merge_components`
- `contour_external`
- `largest_contour_inside_region`
- `padding_tighten_by_mask`
- `projection_tightening`

### Benchmark result

- rows: `42`
- recommended_method: `contour_external`
- recommendation_status: `PROVISIONAL_RECOMMENDED`
- output path: `logs/offline_replay/stage2_region/`

### Decision

`PROVISIONAL_RECOMMENDED` only.
Waiting for Supervisor manual review.

### Required next action

Upload / review overlays from:

```text
logs/offline_replay/stage2_region/contour_external/*/candidate_overlay.png
```

Do not start Stage 3 before Supervisor review.

## Session Status (2026-06-03 Codex)

Stan aktualny: benchmark Stage 2 działa lokalnie i wygenerował komplet raportów/debug overlay.

Co zostało zrobione: dodano izolowany moduł metod regionów, CLI benchmarku Stage 2 oraz 7 testów jednostkowych. Nie zmieniono runtime, Studio, WebSocket ani frontendu.

Kolejne kroki: ręczny review overlay przez Supervisora. Dopiero po nim można zatwierdzić albo skorygować metodę Stage 2.
