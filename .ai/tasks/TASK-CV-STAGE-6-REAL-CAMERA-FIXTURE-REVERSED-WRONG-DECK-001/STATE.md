# STATE — TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001

## Status

`DONE`

## Supervisor Review

`APPROVED_REAL_CAMERA_FIXTURE_OFFLINE_ONLY_BY_CHATGPT_SUPERVISOR`.

`PROVISIONAL_ACCEPTED_FOR_MANUAL_REVIEW` for capture complete commit
`5afe76308602ef74e8df45b9f0bb6a7777dd0811`.

The generated review pack was zipped for handoff:

`logs/offline_replay/stage6_real_camera_validation/stage6_real_camera_manual_review_pack.zip`

`APPROVED_PHASE_A_BY_CHATGPT_SUPERVISOR` for commit
`db744e74fbddbae2086f17c97acc962d379cf077`.

The required minimum 28 physical real-camera sessions have been captured,
manually confirmed by the operator, passed preflight and produced a manual
review pack.

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
- Changed the wizard default flow to camera snapshot mode: backend and Studio
  can stay off, Enter takes one OpenCV camera photo, and the operator can
  accept, repeat, skip or abort before the sample is recorded.
- Fixed camera snapshot capture to use the project `CameraSession`, so wizard
  photos use the same `1280x720` resolution and restored `logs/camera_settings.json`
  camera controls as the backend preview.
- Captured the required 28 physical real-camera sessions.
- Generated aggregate manifest and ground truth with 28 manually confirmed
  labels.
- Preflight result: `PASS`, `sample_count: 28`, `errors: []`, `warnings: []`.
- Generated manual review pack at
  `logs/offline_replay/stage6_real_camera_validation/manual_review_pack`.

## Review Condition

Manual review of the generated pack is complete. Fixture is approved for
offline Stage 6 validation only. This task does not approve runtime thresholds,
ORB/AKAZE runtime integration or app behavior changes.

## Runtime Safety

- No `app_cv/main.py` changes.
- No `app_cv/tarotvision/*` changes.
- No `app_ar/*` changes.
- No live capture mechanism changes.
- No runtime threshold or ORB/AKAZE integration approval.

## Required Next Action

Run `TASK-CV-STAGE-6-REAL-CAMERA-IDENTIFICATION-BENCHMARK-001` offline-only.
