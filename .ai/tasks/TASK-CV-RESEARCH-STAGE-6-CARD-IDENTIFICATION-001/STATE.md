# Stan Prac — TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001

## Summary

Prepared Research Gate for Stage 6 Card Identification in the isolated state-first offline lab.

## Input

Approved upstream pipeline:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
Stage 3: hybrid_edge_plus_contour
Stage 4: quad_warp_perspective_fixed_aspect__resize_only_normalization
Stage 5: quality_metric_suite_v1
```

## Key Constraint

All real Stage 5 crop samples in the current fixture are `YELLOW`, not `PASS`.

Stage 6 must therefore handle medium-quality crops and carry Stage 5 quality context into identification reports.

## Output

Created:

```text
.ai/tasks/TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001/RESEARCH_REPORT.md
docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md
```

## Decision

Research complete; pending Supervisor shortlist approval.

No final Stage 6 method is approved yet.

## Recommended TEST_NOW Shortlist

1. `orb_bfmatcher_ratio_test`
2. `orb_flann_lsh`
3. `akaze_bfmatcher`
4. `brisk_bfmatcher`
5. `histogram_similarity_hsv`
6. `edge_layout_similarity`
7. `ssim_like_luma`
8. `hybrid_orb_plus_histogram`
9. `hybrid_akaze_plus_histogram`
10. `top_k_vote_ensemble`

## Required Next Action

Supervisor accepts or corrects the `TEST_NOW` shortlist. Only after that, create:

```text
TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001
```
