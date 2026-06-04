# STATE — TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001

## Status

`PROVISIONAL_BLOCKED`

## Supervisor Review

`APPROVED_PHASE_A_BY_CHATGPT_SUPERVISOR` for commit
`db744e74fbddbae2086f17c97acc962d379cf077`.

The whole task remains `PROVISIONAL_BLOCKED` until the required minimum 28
physical real-camera sessions are captured and manually confirmed.

`CHANGES_REQUESTED_BY_CHATGPT_SUPERVISOR` for capture wizard commit
`5f784a63e5d83fe6313356fab08747952a65414c`: fixed by requiring real
`Gilded_<number>` card IDs for `gilded_yellow` and `gilded_visually_similar`
before recording manual-confirmed ground truth.

## Completed

- Implemented read-only aggregate manifest and ground-truth loader.
- Implemented stable sample IDs and session fingerprints.
- Implemented offline preflight with one-session-one-sample enforcement.
- Implemented manual review pack generator requiring preflight `PASS`.
- Added operator capture documentation.
- Added a manual operator wizard that guides the 28-session capture process
  without changing runtime or auto-starting the backend.
- Added guards so the wizard and preflight reject placeholder card IDs such as
  `Gilded_YELLOW_*` and `Gilded_SIM_*`.
- Added root launcher `stage6_capture_wizard.bat` so the operator can start the
  wizard without typing the long Python path.
- Added capture diagnostics so missing session files explain whether backend
  env vars, scenario folder or required snapshot files are missing.

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

Operator-assisted capture with the wizard:

`stage6_capture_wizard.bat`

Detailed procedure:

`docs/operator/stage6_real_camera_fixture_capture.md`

After all 28 sessions and manual labels exist, run preflight and generate the
manual review pack.
