# TEST_REPORT

## TDD

Initial RED:

```text
ModuleNotFoundError: tools.cv_detection_lab.stage6_real_camera_fixture
```

## Focused Tests

```text
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v
PASS - 9 tests
```

## Regression Tests

```text
python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v
PASS - 20 tests

python -B -m py_compile tools/cv_detection_lab/stage6_real_camera_fixture.py tools/cv_detection_lab/stage6_real_camera_preflight.py tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py app_cv/tests/test_cv_detection_lab_stage6_real_camera_fixture.py
PASS

$env:PYTHONPATH='app_cv'; python -m unittest discover -s app_cv/tests -v
PASS - 396 tests
```

Initial full discovery without `PYTHONPATH=app_cv` failed during collection because
`tarotvision` was not importable. The configured full backend command above passed.

Frontend build: `NOT_RUN` - no `app_ar` changes.

## Scope

- Runtime files: unchanged.
- Live fixture capture mechanism: unchanged.
- Physical capture: not performed.
- Expected task status: `PROVISIONAL_BLOCKED`.

## Supervisor Review

ChatGPT Supervisor approved Phase A for commit
`db744e74fbddbae2086f17c97acc962d379cf077`.

The review accepted focused tests, Stage 6 regression tests, py_compile and full
backend discovery with `PYTHONPATH=app_cv`. Frontend build remains `NOT_RUN`
because there were no `app_ar` changes.

## Capture Wizard Verification

```text
Initial RED:
ModuleNotFoundError: tools.cv_detection_lab.stage6_real_camera_capture_wizard

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v"
PASS - 13 tests

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -B -m py_compile tools\cv_detection_lab\stage6_real_camera_fixture.py tools\cv_detection_lab\stage6_real_camera_preflight.py tools\cv_detection_lab\stage6_real_camera_manual_review_pack.py tools\cv_detection_lab\stage6_real_camera_capture_wizard.py app_cv\tests\test_cv_detection_lab_stage6_real_camera_fixture.py"
PASS

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python tools\cv_detection_lab\stage6_real_camera_capture_wizard.py --print-plan"
PASS - printed 28 planned capture steps
```

During verification, the existing `C:\tmp\tarot_pydeps` cache exposed empty
namespace imports for `numpy`/`cv2`. A fresh `C:\tmp\tarot_pydeps_stage6`
dependency target was installed for test execution, and manual review pack
generation now has a fallback when OpenCV is unavailable.

Stage 6 regression command:

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v"
FAIL during import before tests - local dependency target imports `numpy` as an empty namespace, so `np.ndarray` is missing in `tools/cv_detection_lab/methods.py`.
```

This is an environment/dependency-target issue, not a wizard behavior failure.

## Capture Wizard Ground-Truth Fix Verification

```text
Initial RED:
ImportError: cannot import name 'resolve_manual_card_identity'

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v"
PASS - 16 tests

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -B -m py_compile tools\cv_detection_lab\stage6_real_camera_fixture.py tools\cv_detection_lab\stage6_real_camera_preflight.py tools\cv_detection_lab\stage6_real_camera_manual_review_pack.py tools\cv_detection_lab\stage6_real_camera_capture_wizard.py app_cv\tests\test_cv_detection_lab_stage6_real_camera_fixture.py"
PASS

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python tools\cv_detection_lab\stage6_real_camera_capture_wizard.py --print-plan"
PASS - printed 28 planned capture steps with manual labels for YELLOW and visually similar categories
```

Added checks:

- wizard plan does not prefill `expected_card_id` for `gilded_yellow` and `gilded_visually_similar`,
- wizard requires real `Gilded_<number>` before recording those categories,
- visually similar samples require a non-empty `similarity_group`,
- preflight blocks placeholder IDs with `INVALID_EXPECTED_CARD_ID_PLACEHOLDER`.

Stage 6 regression command was retried:

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_preflight app_cv.tests.test_cv_detection_lab_stage6_identification app_cv.tests.test_cv_detection_lab_stage6_synthetic_validation -v"
FAIL during import before tests - the local dependency target still imports `numpy` as an empty namespace, so `np.ndarray` is missing in `tools/cv_detection_lab/methods.py`.
```

## Root Launcher Verification

```text
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && stage6_capture_wizard.bat plan"
PASS - printed 28 planned capture steps
```

## Capture Wizard Diagnostics Verification

```text
Initial RED:
ImportError: cannot import name 'capture_status_message'

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v"
PASS - 18 tests
```

Added checks:

- missing session folder explains that backend did not write the session and shows env vars,
- incomplete `one_card` capture lists missing required files,
- retry prompt now offers explicit choices instead of a blind Enter loop.

## Camera Snapshot Wizard Mode Verification

```text
Initial RED:
ImportError: cannot import name 'write_camera_snapshot_session'

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v"
PASS - 19 tests

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -B -m py_compile tools\cv_detection_lab\stage6_real_camera_capture_wizard.py app_cv\tests\test_cv_detection_lab_stage6_real_camera_fixture.py"
PASS

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && stage6_capture_wizard.bat plan"
PASS - printed 28 planned capture steps
```

Added checks:

- wizard can write a complete camera snapshot fixture session without backend output,
- session includes `raw_frame_1.png`, `analysis_frame_1.png`, `payload.json`,
  `metrics.json`, `roi_diagnostics.json` and session `manifest.json`,
- payload and metrics mark `capture_mode: camera_snapshot`.

Physical camera capture was not run automatically; it still requires operator
setup of the real camera, mat and cards.

## Camera Snapshot Settings Parity Verification

```text
Initial RED:
TypeError: capture_frame_from_camera() got an unexpected keyword argument 'log_dir'

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture.TestStage6RealCameraFixture.test_capture_wizard_uses_project_camera_session_settings -v"
PASS

cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps_stage6;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage6_real_camera_fixture -v"
PASS - 20 tests
```

Root cause from the operator screenshot: wizard snapshot capture used plain
`cv2.VideoCapture`, while backend preview used `CameraSession`, which requests
`1280x720` and restores `logs/camera_settings.json`. Wizard capture now uses
`CameraSession` too.

## Physical Capture And Preflight Verification

Operator capture completed through `stage6_capture_wizard.bat`.

Generated reports:

```text
logs/live_fixtures/stage6_real_camera_validation/manifest.json
logs/live_fixtures/stage6_real_camera_validation/ground_truth.json
logs/offline_replay/stage6_real_camera_validation/preflight_report.json
logs/offline_replay/stage6_real_camera_validation/preflight_report.md
logs/offline_replay/stage6_real_camera_validation/manual_review_pack/
```

Preflight report:

```json
{
  "stage": "stage6_real_camera_fixture_preflight",
  "status": "PASS",
  "sample_count": 28,
  "errors": [],
  "warnings": [],
  "required_next_action": "Generate manual review pack."
}
```

Manual review pack check:

```text
manual_review_pack/samples contains 28 PNG files
category_index.json contains all required categories
similarity_groups.json contains similar-1 and similar-2 with 2 samples each
README_FOR_SUPERVISOR.md reports Samples: 28
```

The task is no longer blocked by missing physical capture data. Remaining
action is manual review of the generated pack; runtime threshold and runtime
integration approval remain out of scope.

## Manual Review ZIP Verification

Created ZIP:

```text
logs/offline_replay/stage6_real_camera_validation/stage6_real_camera_manual_review_pack.zip
```

ZIP content check:

```text
README_FOR_SUPERVISOR.md
manifest.json
ground_truth.json
preflight_report.json
category_index.json
similarity_groups.json
samples/*.png = 28 files
```

SHA256:

```text
F323748FC49AB6D71BE3A8190F9E356B5A405854383F4E28BD1C5A6F24EA10E9
```
