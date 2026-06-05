# STATE

## Status

`DONE`

## Manual Decision

`f8d6d84b5ddb5729fa07`: confirmed as `Gilded_67`.

## Verification Result

- Preflight: `PASS`.
- ORB Top-1: `0.85` (wcześniej `0.80`).
- ORB Top-3: `0.90` (wcześniej `0.85`).
- ORB wrong-deck FAR: `0.00`.
- Remaining ORB Top-1 errors: `3`.
- Remaining error causes: `image_quality_or_crop = 3`.

## Required Next Action

Supervisor zatwierdza ręczną korektę i nowe metryki offline-only.

## Supervisor Decision

`APPROVED_OFFLINE_GROUND_TRUTH_CORRECTION`.

Status ORB: `ORB_REAL_CAMERA_VALIDATED_OFFLINE_ONLY_AFTER_GT_FIX`.
Brak zgody na runtime threshold i runtime integration.
