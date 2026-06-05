# STATE: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-GEOMETRY-STABILIZATION-001

## Status

GEOMETRY_VERIFIED_RECOGNITION_FOLLOWUP_REQUIRED

## Branch

`task/cv-stage-6-calibration-wizard-one-card-geometry-stabilization-001`

## Stan aktualny

Faza 3 została wdrożona. Włączono fallback `min_area_rect` dla obu profili adaptacyjnych w `app_cv/tarotvision/card_detection_profiles.py`.
Uruchomiono pełny pakiet testów jednostkowych (423/423 PASS) — potwierdzono brak regresji w kodzie backendu CV.

Smoke test potwierdził istotny postęp: `empty` pozostaje czyste, a `one_card` w trzech zebranych próbkach miało stabilne `detected_count=1`. Problem geometrii został więc zweryfikowany jako poprawiony do poziomu dalszej diagnostyki.

Cały krok `one_card` nadal nie przechodzi jako gotowy etap kalibracji, ponieważ acceptance/recognition zaakceptowało tylko 1 z 3 próbek (`accepted_total=1/3`). Task nie jest gotowy do PR jako pełny sukces. Następny blocker jest poza geometrią: konfiguracja aktywnej talii albo recognition acceptance.

## Session Status (2026-06-05)

- Wdrożono poprawkę w profilach detekcji.
- Przeprowadzono pomyślną weryfikację jednostkową (wszystkie 423 testy zielone).
- Wykonano smoke test po poprawce:
  - `empty`: PASS.
  - `one_card` geometria: PASS (`detected_count=1` dla 3/3 próbek).
  - `one_card` acceptance: FAIL (`accepted_total=1/3`).
  - `three_cards`: NOT_RUN.
- Sprawdzono konfigurację talii w czasie testu: runtime i Studio wskazywały aktywną talię `gilded`; Michał potwierdził, że fizyczna talia użyta w smoke teście to Gilded.
- Zaktualizowano status zadania w `STATE.md`, `CHANGELOG.md`, `TEST_REPORT.md` i `.ai/TASKS_INDEX.md`.

## Kolejne kroki

1. Nie kontynuować strojenia geometrii w `card_detection_profiles.py` bez nowych dowodów.
2. Rozpocząć osobny follow-up recognition acceptance, ponieważ fizyczna talia i aktywna talia runtime były zgodne (`Gilded`).
3. Następny task: `TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001`.
