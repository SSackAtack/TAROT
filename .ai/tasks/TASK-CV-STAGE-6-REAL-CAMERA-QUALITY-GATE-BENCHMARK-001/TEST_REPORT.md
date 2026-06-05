# TEST REPORT

## Benchmark

`python -m tools.cv_detection_lab.stage6_real_camera_quality_gate_benchmark ...` => PASS

| Metric | Result |
|---|---:|
| bad_crop_retry_recall | 1.0 |
| good_crop_false_retry_rate | 0.0 |
| good_crop_non_accept_rate | 0.0 |
| wrong_deck_false_retry_rate | 0.0 |
| ORB accuracy on ACCEPT subset | 1.0 |

## Review Pack

- `logs/offline_replay/stage6_real_camera_quality_gate_review_pack.zip`
- SHA-256: `EDE5B8387BB631F748DDF1D047A75C3C829C4FD90E22874EBB96BEF182B06647`

## Tests

- focused quality gate tests => PASS, 5 tests
- focused Stage 6 real-camera tests => PASS, 33 tests
- full backend suite => PASS, 420 tests
- py_compile => PASS

## Scope

Brak zmian runtime.
