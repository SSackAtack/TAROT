# STATE: TASK-CV-GEOMETRY-FALLBACK-001

## Status

DONE

## Branch

`codex/snapshot-first-recognition-hardening`

## Stan aktualny

Wdrożono kontrolowany fallback `minAreaRect` dla poszarpanych konturów kart oraz stabilny kontrakt diagnostyki detekcji. `SnapshotAnalyzer` ponownie respektuje dependency injection, a produkcyjny runtime może opcjonalnie pobierać pełny wynik `find_card_quads_multi_profile` z debugiem. Status kalibracji stołu filtruje markery spoza zestawu `10-13`, więc wzory z kart nie powinny trafiać do listy markerów stołu.

## Co zostało zrobione

- Dodano `tarotvision/detection_diagnostics.py`.
- Dodano profil `min_area_rect` i liczniki `min_area_rect_candidates` / `min_area_rect_accepted`.
- Dodano testy pustej maty, poszarpanego konturu, kontraktu analizatora i filtra ArUco.
- Obrazy debug cropów są domyślnie wyłączone i wymagają `TAROTVISION_DEBUG_IMAGES=1`.

## Kolejne kroki

1. Gemini/Michał wykonują live retest: pusta mata, Gilded na ciemnej macie, karta z odblaskiem.
2. Analizować nowe metryki `snapshot_detection_*` w `logs/cv_metrics.jsonl`.
3. Jeżeli `minAreaRect` nie wystarczy, uruchomić osobny Hough diagnostics spike przed wdrożeniem rekonstrukcji 3/2/1-edge.
