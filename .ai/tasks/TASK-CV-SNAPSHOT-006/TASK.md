# TASK-CV-SNAPSHOT-006: Model pustej maty

## Cel

Dodać opcjonalny model pustej maty, który może wspierać detekcję kart przez `background_diff` przy słabym kontraście talii względem maty.

## Zakres

- `app_cv/tarotvision/background_model.py`
- `app_cv/tarotvision/card_detection_profiles.py`
- `app_cv/tarotvision/snapshot_analyzer.py`
- `app_cv/tarotvision/tuning_protocol.py`
- `app_cv/main.py`
- `app_cv/tests/test_background_model.py`
- `app_cv/tests/test_card_detection_profiles.py`
- `app_cv/tests/test_tuning_protocol.py`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- `BackgroundModel` po `capture()` zwraca maskę foreground dla karty dodanej do pustej maty.
- Parser WebSocket akceptuje `background_capture` i `background_clear`.
- `main.py` przechwytuje model pustej maty z kolejnej klatki, a `background_clear` go dezaktywuje.
- `find_card_quads_multi_profile()` dodaje profil `background_diff` tylko wtedy, gdy model tła jest aktywny.
