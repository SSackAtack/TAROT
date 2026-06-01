# TASK-CV-SNAPSHOT-002: Unicode-safe image I/O i reference loader

## Cel

Naprawic ladowanie wzorcow CV ze sciezek zawierajacych polskie znaki oraz wyprowadzic duplikowana logike ladowania kart z `main.py` do modulu domenowego.

## Zakres

- `app_cv/tarotvision/image_io.py`
- `app_cv/tarotvision/reference_loader.py`
- `app_cv/tarotvision/card_recognition.py`
- `app_cv/main.py`
- `app_cv/tests/test_image_io.py`
- `app_cv/tests/test_reference_loader.py`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- `imread_grayscale_unicode()` czyta pliki JPG z polskimi znakami w sciezce.
- `load_active_reference_cards()` laduje aktywne talie z manifestu i zwraca diagnostyke pominietych plikow.
- `main.py` nie zawiera recznej petli ORB po plikach wzorcow.
- `card_recognition.load_reference_cards()` uzywa Unicode-safe loadera.
