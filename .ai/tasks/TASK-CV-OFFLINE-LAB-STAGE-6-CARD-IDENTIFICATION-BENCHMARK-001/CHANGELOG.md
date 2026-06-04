# CHANGELOG

## 2026-06-04 — Method approval

- Recorded Supervisor decision: `APPROVED_STAGE_6_METHOD: orb_bfmatcher_ratio_test`.
- Limited approval to the current offline lab fixture.
- Explicitly recorded that runtime integration is not approved.
- Set broader Stage 6 validation benchmark as the next action.

## 2026-06-04 — Manual review pack

- Prepared a six-scenario Supervisor review pack for `orb_bfmatcher_ratio_test`.
- Added an explicit zero-crop PASS sheet for `empty_to_empty`.
- Added benchmark reports, matrix and Supervisor instructions.

## TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001

- Added isolated Stage 6 card identification methods.
- Added first-wave Stage 6 benchmark with top1/top3, confidence gap and runtime metrics.
- Added Stage 6 benchmark unit tests.
- Ran benchmark against manually confirmed Gilded ground truth.
- Provisionally recommended `orb_bfmatcher_ratio_test`.
- Did not change runtime.
- Did not add dependencies.
