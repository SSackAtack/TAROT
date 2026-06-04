# CHANGELOG

## 2026-06-04 — Phase A offline tooling

- Added aggregate fixture contract, stable IDs and read-only fingerprints.
- Added aggregate/ground-truth preflight.
- Added explicit manifest/ground-truth field consistency validation.
- Fixed blocked preflight Markdown to report errors without a false `None`.
- Added manual review pack generator.
- Added operator-assisted capture instructions.
- Kept task `PROVISIONAL_BLOCKED` pending 28 physical sessions.

## 2026-06-04 — ChatGPT Supervisor review

- Recorded `APPROVED_PHASE_A_BY_CHATGPT_SUPERVISOR` for commit `db744e74fbddbae2086f17c97acc962d379cf077`.
- Confirmed the whole task remains `PROVISIONAL_BLOCKED` until operator-assisted capture produces the required 28 physical sessions.
- Confirmed next action is operator capture, then preflight and manual review pack generation.

## 2026-06-04 — Manual capture wizard

- Added `tools/cv_detection_lab/stage6_real_camera_capture_wizard.py`.
- Wizard prints existing live capture env vars, guides the operator through the 28 required samples and records only complete, manually confirmed sessions.
- Added OpenCV-unavailable fallback for manual review pack generation in constrained test environments.
- Kept task `PROVISIONAL_BLOCKED` because physical sessions still have not been captured.

## 2026-06-04 — Capture wizard ground-truth fix

- Removed placeholder card IDs from `gilded_yellow` and `gilded_visually_similar` wizard plan steps.
- Added manual real-card-ID resolution requiring `Gilded_<number>` before recording those categories.
- Added preflight guard `INVALID_EXPECTED_CARD_ID_PLACEHOLDER` for blocked placeholder IDs.
- Kept runtime untouched and task `PROVISIONAL_BLOCKED` pending physical capture.
