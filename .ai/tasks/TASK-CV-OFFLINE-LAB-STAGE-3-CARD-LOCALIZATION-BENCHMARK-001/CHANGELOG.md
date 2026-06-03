# CHANGELOG

## 2026-06-03 Codex

- Dodano `tools/cv_detection_lab/card_localization_methods.py` z metodami:
  - `bounding_rect_tight`
  - `contour_largest_inside_candidate`
  - `approx_poly_dp_quad`
  - `min_area_rect_candidate`
  - `projection_profile_tight_bbox`
  - `hybrid_contour_plus_min_area_rect`
  - `hybrid_edge_plus_contour`
- Dodano scoring geometrii:
  - aspect ratio i blad aspect ratio
  - area ratio
  - rectangularity
  - border score
  - edge support
  - corner score
  - angle stability
  - `geometry_confidence`
- Dodano `tools/cv_detection_lab/stage3_card_localization_benchmark.py`.
- Dodano testy `app_cv/tests/test_cv_detection_lab_stage3.py`.
- Zaktualizowano `.ai/TASKS_INDEX.md`.
- Zaktualizowano plan `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-3-plan.md`.

## Decyzje

- Pary `removed` uzywaja `previous` jako zrodla geometrii, poniewaz karta istnieje w klatce poprzedniej, a `current` jest pusta.
- Rekomendacja benchmarku ma status `PROVISIONAL_RECOMMENDED`, poniewaz finalna decyzja Stage 3 wymaga manualnej oceny overlayow.
- Benchmark nie generuje cropow ani deskew; to pozostaje poza zakresem Stage 3.
