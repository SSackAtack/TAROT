# TEST REPORT: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## Testy automatyczne

Targeted tests:

```text
$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_card_recognition.RecognizeCardCropTest.test_debug_reports_best_rejected_match_when_good_matches_below_threshold -v
=> PASS

$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer.SnapshotAnalyzerTest.test_records_recognition_debug_for_rejected_crop -v
=> PASS

$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_autotune_pipeline_sample_capture.TestAutotunePipelineSampleCapture.test_collects_unrecognized_one_card_sample -v
=> PASS
```

Module tests:

```text
$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_card_recognition -v
$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_snapshot_analyzer -v
$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_autotune_pipeline_sample_capture -v
=> PASS
```

Camera hotfix tests:

```text
$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_camera_session -v
=> PASS

$env:PYTHONPATH='app_cv'; python -m unittest app_cv.tests.test_autotune_pipeline_sample_capture -v
=> PASS
```

Current session verification:

```text
cd app_cv
python -m unittest tests.test_camera_session tests.test_studio_launcher_static
=> PASS (15 tests)

python -m unittest discover tests
=> PASS (431 tests)
```

## Smoke / diagnostyka fizyczna

Punkt wejścia z poprzedniego taska:

- Physical deck: Gilded.
- Active runtime deck: `gilded`.
- `empty`: PASS.
- `one_card` geometry: PASS, `detected_count=1` dla 3/3 próbek.
- `one_card` acceptance: FAIL, `accepted_total=1/3`.
- `three_cards`: NOT_RUN.

Current diagnostic run:

- Backend restarted with current branch code.
- Runtime active deck: `gilded`.
- Camera opened: 1280x720.
- Studio CV Explain showed one candidate and one accepted card before starting the wizard.
- `one_card` stage started, but no new sample was collected without a fresh physical motion/snapshot trigger.
- Required next manual action: move hand/card over the table and place the Gilded card stable for 2-3 seconds, then inspect `recognition_debug` in the new `one_card` autotune JSON.

MSMF camera issue:

- Operator reported repeated `CvCapture_MSMF::grabFrame ... can't grab frame` after closing windows and restarting `.bat`.
- Backend restarted after DirectShow-first hotfix.
- Runtime log: `Kamera otwarta przez backend DirectShow`.
- Runtime log after hotfix did not show new MSMF `grabFrame` warnings in the checked window.
- DirectShow raw resolution check: camera reported 1920x1080 despite requested 1280x720.
- Runtime resize check: after resize fallback, log reported `Kamera 0 otwarta. Rozdzielczość: 1280x720`.
- Port conflict check: `WinError 10048` was caused by two local `python main.py` processes; after stopping both, backend listened on `8765` normally.

No-image / black preview issue:

- MJPEG endpoint check before camera backend fallback: endpoint returned valid JPEG frames, but first frame was fully black (`mean_gray=0.0`, min/max `0/0`).
- Local backend comparison:
  - `CAP_ANY`: opened, 1280x720, `mean_gray=58.08`.
  - `CAP_DSHOW`: opened, 1920x1080, `mean_gray=0.0`.
  - `CAP_MSMF`: opened, 1280x720, `mean_gray=53.65`.
- After DirectShow-black fallback and backend restart:
  - MJPEG first frame: 960x540, `mean_gray=53.8`, min/max `0/246`.
  - Studio preview rendered real camera image in PiP.
- Launcher regression covered by static test: ports `5173`, `8765`, `8766` are checked together.

## Zakres

- `app_ar/public/active_decks.json`: poza zakresem, nie commitować.
- Frontend build: NOT_RUN — frontend not changed.
