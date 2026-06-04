# STATE — TASK-CV-OFFLINE-LAB-STAGE-6-DECK-PROFILE-GROUNDTRUTH-001

## Summary

Added Stage 6 input data required by preflight:

- `biblioteka_talii/gilded/deck_profile.json`
- `logs/live_fixtures/event_first_current_debug_verified/ground_truth.json`

## Deck Profile

Source:

- `biblioteka_talii/gilded/info.json`

Deck:

- deck_id: `gilded_scans`
- scope: `full_deck_78`
- card_count: `78`
- reference image count: `78`

The profile uses technical `card_name` values (`Gilded_00` ... `Gilded_77`) because no reliable card-name mapping for Gilded was found in repo.

## Ground Truth

Fixture:

- `logs/live_fixtures/event_first_current_debug_verified`

Label status:

- `unknown_labels_pending_manual_confirmation`

All non-empty labels use `UNKNOWN_DECK` because manual card identity is not confirmed yet.

## Important Limitation

If labels use `UNKNOWN_DECK`, Stage 6 benchmark can only test unknown/reject behavior, not top1/top3 accuracy.

Preflight can pass on `UNKNOWN_DECK` labels, but accuracy benchmarking requires a later manual-label confirmation task.

## Preflight Result

Status:

- `PASS`

Blocking errors, if any:

- none

## Required Next Action

Decision by Supervisor:

- create `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`, or
- create a manual-label confirmation task before the accuracy benchmark.
