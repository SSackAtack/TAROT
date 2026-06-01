# TASK-CV-SNAPSHOT-005: Wieloprofilowa detekcja kart

## Cel

Poprawic lokalizacje kart w snapshot-first dla ciemnych talii i ciemnych mat przez uruchomienie kilku profili detekcji OpenCV i deduplikacje wynikow.

## Zakres

- `app_cv/tarotvision/card_detection_profiles.py`
- `app_cv/tarotvision/snapshot_analyzer.py`
- `app_cv/tests/test_card_detection_profiles.py`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md`

## Kryteria akceptacji

- Detektor wykrywa syntetyczna ciemna karte na ciemnozielonym tle z jasniejsza ramka.
- Wyniki z kilku profili sa deduplikowane.
- `SnapshotAnalyzer` uzywa wieloprofilowego detektora domyslnie, ale zachowuje dependency injection `find_quads` dla testow.
- Debug zwraca liczby kandydatow per profil.
