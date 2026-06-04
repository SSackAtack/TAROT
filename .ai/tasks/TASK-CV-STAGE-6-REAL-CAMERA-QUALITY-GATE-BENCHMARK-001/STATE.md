# STATE

## Status

`DONE`

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

Wszystkie progi są `BENCHMARK_HEURISTIC_ONLY`. Brak zgody na runtime.

## Required Next Action

Supervisor ocenia wyniki i review pack przed jakąkolwiek kolejną decyzją.
