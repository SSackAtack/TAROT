# STATE — TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001

## Summary

Implemented and ran the deterministic Stage 6 synthetic validation benchmark.

## Dataset

- Seed: `6042026`
- Known Gilded samples: `168`
- Unique Gilded cards: `24`
- Categories per Gilded card: `7`
- Wrong-deck samples: `24` (`12 Magic`, `12 Marchetti`)
- Total samples: `192`
- Manifest reproducibility: `PASS`

## Result

| Method | Top1 | Top3 | Wrong-deck FAR | Mean gap | Runtime mean | p50 | p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `orb_bfmatcher_ratio_test` | 1.000 | 1.000 | 0.000 | 0.579 | 573.463 ms | 572.140 ms | 622.677 ms |
| `akaze_bfmatcher` | 1.000 | 1.000 | 0.000 | 0.646 | 971.104 ms | 954.295 ms | 1114.510 ms |

Both methods achieved 100% top-1/top-3 on reversed and `yellow_combined`
samples. ORB remained materially faster. AKAZE retained a stronger mean
confidence gap.

## Decision

`VALIDATION_PASS_OFFLINE_ONLY: orb_bfmatcher_ratio_test`

The approved Stage 6 method remains the preferred offline candidate.

`APPROVED_BY_CHATGPT_SUPERVISOR`

## Limitations

- The dataset is synthetic and derived from reference images.
- Wrong-deck rejection uses an offline-only score threshold of `0.08`.
- The threshold is not approved for runtime.
- Runtime measurements are a local proxy, not a direct HP EliteBook 830 G6 measurement.
- No runtime integration approval is granted.

## Required Next Action

Prepare:

`TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001`

Before runtime integration, collect and validate a broader real-camera fixture
including upright, reversed, wrong-deck, difficult YELLOW crops and visually
similar cards. Include `ground_truth.json`, preflight and manual review pack.
