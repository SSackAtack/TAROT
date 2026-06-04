# STATE — TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001

## Status

`PROVISIONAL_BLOCKED`

## Supervisor Review

`APPROVED_PHASE_A_BY_CHATGPT_SUPERVISOR` for commit
`db744e74fbddbae2086f17c97acc962d379cf077`.

The whole task remains `PROVISIONAL_BLOCKED` until the required minimum 28
physical real-camera sessions are captured and manually confirmed.

## Completed

- Implemented read-only aggregate manifest and ground-truth loader.
- Implemented stable sample IDs and session fingerprints.
- Implemented offline preflight with one-session-one-sample enforcement.
- Implemented manual review pack generator requiring preflight `PASS`.
- Added operator capture documentation.

## Blocking Condition

The required minimum 28 physical real-camera sessions have not been captured
and manually confirmed.

## Runtime Safety

- No `app_cv/main.py` changes.
- No `app_cv/tarotvision/*` changes.
- No `app_ar/*` changes.
- No live capture mechanism changes.
- No runtime threshold or ORB/AKAZE integration approval.

## Required Next Action

Operator-assisted capture according to:

`docs/operator/stage6_real_camera_fixture_capture.md`

After all 28 sessions and manual labels exist, run preflight and generate the
manual review pack.
