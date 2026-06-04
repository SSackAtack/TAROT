# STATE

## Status

`APPROVED`

## Result

- `bad_crop_retry_recall`: `1.0`
- `good_crop_false_retry_rate`: `0.0`
- `good_crop_non_accept_rate`: `0.0`
- `wrong_deck_false_retry_rate`: `0.0`
- `orb_accuracy_on_accept_subset`: `1.0`
- Decisions: ACCEPT `18`, MANUAL_REVIEW `8`, RETRY_CAPTURE `2`

Trzy znane błędy jakości zostały zatrzymane:

- dwa YELLOW -> `RETRY_CAPTURE`,
- jeden upright z bardzo niskim sygnałem ORB -> `MANUAL_REVIEW`.

## Decision Boundary

- `APPROVED_OFFLINE_QUALITY_GATE_BENCHMARK_ONLY`
- `BENCHMARK_HEURISTIC_ONLY`
- `NO_RUNTIME_THRESHOLD_APPROVAL`
- `NO_RUNTIME_INTEGRATION`

## Required Next Action

Rozszerzyć real-camera fixture i kontynuować walidację offline przed
jakąkolwiek decyzją o progach lub integracji runtime.
