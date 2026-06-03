# TEST_REPORT

## Data

2026-06-03

## Wynik

`PASS`

## Komendy

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage3 -v"
```

Wynik:

```text
Ran 8 tests in 0.265s
OK
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -m unittest app_cv.tests.test_cv_detection_lab_stage1 app_cv.tests.test_cv_detection_lab_stage2 -v"
```

Wynik:

```text
Ran 15 tests in 0.308s
OK
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -B -m py_compile tools\cv_detection_lab\card_localization_methods.py tools\cv_detection_lab\stage3_card_localization_benchmark.py app_cv\tests\test_cv_detection_lab_stage3.py"
```

Wynik:

```text
PASS
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python tools\cv_detection_lab\stage3_card_localization_benchmark.py --fixture logs\live_fixtures\event_first_current_debug_verified --output logs\offline_replay\stage3_card_localization"
```

Wynik:

```json
{
  "recommended_method": "hybrid_edge_plus_contour",
  "rows": 42
}
```

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv;.&& python -m unittest discover -s app_cv\tests -v"
```

Wynik:

```text
Ran 339 tests in 9.873s
OK
```

## Frontend

`NOT_RUN` - task nie zmienia `app_ar/` ani frontendowego runtime.

## Manual review

Wymagane przed zatwierdzeniem Stage 3:

```text
logs/offline_replay/stage3_card_localization/hybrid_edge_plus_contour/*/card_geometry_overlay.png
```
