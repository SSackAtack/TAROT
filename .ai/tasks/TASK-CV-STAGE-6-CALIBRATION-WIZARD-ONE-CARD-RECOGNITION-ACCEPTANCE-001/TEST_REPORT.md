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

## Zakres

- `app_ar/public/active_decks.json`: poza zakresem, nie commitować.
- Frontend build: NOT_RUN — frontend not changed.
