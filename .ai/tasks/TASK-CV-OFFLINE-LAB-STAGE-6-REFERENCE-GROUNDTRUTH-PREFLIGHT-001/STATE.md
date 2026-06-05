# STATE

## Summary

Implemented isolated Stage 6 reference deck and ground truth preflight.

## Approved Stages

- Stage 1: `gray_absdiff_gaussian`
- Stage 2: `contour_external`
- Stage 3: `hybrid_edge_plus_contour`
- Stage 4: `quad_warp_perspective_fixed_aspect__resize_only_normalization`
- Stage 5: `quality_metric_suite_v1`

## Validated Inputs

- `fixture_dir`
- `reference_deck_dir`
- `deck_profile.json`
- reference image consistency
- `ground_truth.json`
- required state-first pairs
- deck profile compatibility
- Stage 5 output availability

## Decision

No Stage 6 identification benchmark implemented yet.

Missing Stage 5 output is treated as `WARNING`, not a hard blocker, because the future isolated Stage 6 benchmark can regenerate Stage 1-5 outputs if designed to do so.

## Real Preflight Result

Status: `PROVISIONAL_BLOCKED`

Reason: current real inputs do not yet provide the required `deck_profile.json` and `ground_truth.json` for Stage 6.

## Required Next Action

Create a small task to add or fix `deck_profile.json`, `reference_deck_dir` or `ground_truth.json`.

After preflight reaches `PASS`, create:

```text
TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001
```
