# TEST REPORT

## Manual Review

Crop, `Gilded_45` i `Gilded_67` porównano wizualnie. Crop jednoznacznie
przedstawia `Gilded_67` (Cesarz).

## Reverification

- Stage 6 real-camera preflight => PASS
- Real-camera identification benchmark => PASS, 28 samples
- Error analysis => PASS, 3 remaining Top-1 errors

## New Metrics

| Method | Top1 | Top3 | Wrong-deck FAR |
|---|---:|---:|---:|
| ORB | 0.85 | 0.90 | 0.00 |
| AKAZE | 0.75 | 0.75 | 0.75 |

## Review Pack

- `logs/offline_replay/stage6_real_camera_error_analysis_review_pack.zip`
- SHA-256: `303A393C35EFD83A4B23063249AA42042D66974F4F4CF4DCF01204BA1532294D`

## Tests

- Focused Stage 6 real-camera tests => PASS, 28 tests
- Full backend suite => PASS, 415 tests
