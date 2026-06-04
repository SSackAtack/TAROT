# State-First Offline Lab Stage 6 Plan

## Status ogólny

Zatwierdzony pipeline wejściowy:

```text
Stage 1 approved: gray_absdiff_gaussian.
Stage 2 approved: contour_external.
Stage 3 approved: hybrid_edge_plus_contour.
Stage 4 approved: quad_warp_perspective_fixed_aspect__resize_only_normalization.
Stage 5 approved: quality_metric_suite_v1.
```

Stage 6 Card Identification research has been prepared. Benchmark Stage 6 must not begin until Supervisor accepts the `TEST_NOW` shortlist.

## Session Status (2026-06-04 Codex Stage 6 Reference/Ground Truth Preflight)

Stan aktualny: zaimplementowano izolowany preflight Stage 6 dla `reference_deck_dir`, `deck_profile.json` i `ground_truth.json`.

Co zostało zrobione: dodano `tools/cv_detection_lab/stage6_preflight.py`, testy jednostkowe oraz dokumentację taska `TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001`. Preflight sprawdza fixture, profil talii, obrazy referencyjne, ground truth, wymagane pary state-first, zgodność profilu i dostępność outputów Stage 5.

Kolejne kroki: realny preflight jest `PROVISIONAL_BLOCKED`, dopóki repo nie zawiera wymaganego `deck_profile.json` i `ground_truth.json` dla fixture Stage 6. Po usunięciu blokady można utworzyć benchmark Stage 6 Card Identification.

## Session Status (2026-06-04 Codex Stage 6 Research Gate)

Stan aktualny: przygotowano research summary dla Stage 6 Card Identification.

Co zostało zrobione: utworzono `TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001`, zapisano macierz kandydatów, wymagania reference deck, wymagania ground truth i shortlistę metod `TEST_NOW`.

Kolejne kroki: Supervisor powinien zaakceptować albo skorygować shortlistę `TEST_NOW`. Po akceptacji należy utworzyć `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`.

## Co zostało zrobione

- [x] Potwierdzono wejście ze Stage 1: `gray_absdiff_gaussian`.
- [x] Potwierdzono wejście ze Stage 2: `contour_external`.
- [x] Potwierdzono wejście ze Stage 3: `hybrid_edge_plus_contour`.
- [x] Potwierdzono wejście ze Stage 4: `quad_warp_perspective_fixed_aspect__resize_only_normalization`.
- [x] Potwierdzono wejście ze Stage 5: `quality_metric_suite_v1`.
- [x] Zidentyfikowano ograniczenie Stage 5: realne cropy fixture są `YELLOW`, nie `PASS`.
- [x] Przeanalizowano ORB, FLANN LSH, AKAZE, BRISK, SIFT, template matching, histogram, edge/layout, hash, SSIM-like i hybrydy.
- [x] Wskazano shortlistę `TEST_NOW`.
- [x] Dodano preflight wymaganych wejść Stage 6: reference deck, `deck_profile.json`, `ground_truth.json`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001`: Research Gate Stage 6 Card Identification.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001`: izolowany preflight wejść Stage 6.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-DATA-001`: uzupełnienie realnego `deck_profile.json` i `ground_truth.json` dla fixture Stage 6.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`: benchmark po akceptacji shortlisty.

## Shortlista TEST_NOW

- `orb_bfmatcher_ratio_test`
- `orb_flann_lsh`
- `akaze_bfmatcher`
- `brisk_bfmatcher`
- `histogram_similarity_hsv`
- `edge_layout_similarity`
- `ssim_like_luma`
- `hybrid_orb_plus_histogram`
- `hybrid_akaze_plus_histogram`
- `top_k_vote_ensemble`

## Wymagane wejścia do benchmarku

```text
reference_deck_dir
deck_profile.json
ground_truth.json
```

## Kolejne kroki

Natychmiastowy następny krok dla kolejnego modelu: przekazać shortlistę `TEST_NOW` Supervisorowi. Po akceptacji dopiero wtedy utworzyć i zaimplementować offline benchmark Stage 6 w izolowanym `tools/cv_detection_lab/`, bez zmian runtime.

Aktualizacja po preflight: przed benchmarkiem trzeba dodać lub naprawić realny `deck_profile.json` i `ground_truth.json`, a następnie ponownie uruchomić preflight do statusu `PASS`.
