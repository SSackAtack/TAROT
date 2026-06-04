# STATE — TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001

## Summary

Implemented and ran the first-wave isolated Stage 6 Card Identification benchmark.

## Inputs

- Fixture: `logs/live_fixtures/event_first_current_debug_verified`
- Reference deck: `biblioteka_talii/gilded/produkcja/wzorce_cv`
- Deck profile: `biblioteka_talii/gilded/deck_profile.json`
- Ground truth: `logs/live_fixtures/event_first_current_debug_verified/ground_truth.json`
- Labels: 10 manually confirmed

## Result

| Method | Top1 | Top3 | Ambiguous | Mean gap | Runtime ms |
|---|---:|---:|---:|---:|---:|
| `orb_bfmatcher_ratio_test` | 1.000 | 1.000 | 0.000 | 0.268 | 523.651 |
| `akaze_bfmatcher` | 1.000 | 1.000 | 0.000 | 0.528 | 1165.146 |
| `hybrid_orb_plus_histogram` | 1.000 | 1.000 | 0.000 | 0.172 | 574.877 |
| `histogram_similarity_hsv` | 0.000 | 0.000 | 1.000 | 0.012 | 72.610 |
| `ssim_like_luma` | 0.000 | 0.000 | 1.000 | 0.003 | 38.113 |

## Decision

`APPROVED_STAGE_6_METHOD: orb_bfmatcher_ratio_test`

Reason:

- 100% top1 and top3 on current 10-label fixture,
- lower runtime than AKAZE,
- stronger result than global-only histogram and SSIM-like methods.
- Supervisor manual review approved the method for the current offline lab fixture.

AKAZE remains a strong fallback candidate because it produced a larger confidence gap, but its runtime was approximately 2.2 times higher.

## Limitations

- Approved for current offline lab fixture only. No runtime integration approval.
- Current fixture contains only three unique cards repeated across state-first pairs.
- All real crops have Stage 5 status `YELLOW`.
- No unknown-deck or reversed card cases are included in the current accuracy fixture.

## Required Next Action

Prepare a broader Stage 6 validation benchmark. Do not integrate the method into runtime yet.
