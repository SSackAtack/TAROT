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

## Session Status (2026-06-04 Codex Stage 6 Card Identification Benchmark)

Stan aktualny: zaimplementowano i uruchomiono pierwszą falę offline benchmarku Stage 6 Card Identification.

Co zostało zrobione: porównano `orb_bfmatcher_ratio_test`, `akaze_bfmatcher`, `histogram_similarity_hsv`, `ssim_like_luma` i `hybrid_orb_plus_histogram`. ORB, AKAZE i hybryda osiągnęły 100% top1/top3 na 10 ręcznie potwierdzonych etykietach. Histogram i SSIM-like osiągnęły 0%.

Kolejne kroki: przygotować manual review Stage 6 i decyzję Supervisora. `orb_bfmatcher_ratio_test` jest `PROVISIONAL_RECOMMENDED`, ale nie wolno jeszcze integrować go z runtime.

## Session Status (2026-06-04 Codex Stage 6 Reference/Ground Truth Preflight)

Stan aktualny: zaimplementowano izolowany preflight Stage 6 dla `reference_deck_dir`, `deck_profile.json` i `ground_truth.json`.

Co zostało zrobione: dodano `tools/cv_detection_lab/stage6_preflight.py`, testy jednostkowe oraz dokumentację taska `TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001`. Preflight sprawdza fixture, profil talii, obrazy referencyjne, ground truth, wymagane pary state-first, zgodność profilu i dostępność outputów Stage 5.

Kolejne kroki: realny preflight jest `PROVISIONAL_BLOCKED`, dopóki repo nie zawiera wymaganego `deck_profile.json` i `ground_truth.json` dla fixture Stage 6. Po usunięciu blokady można utworzyć benchmark Stage 6 Card Identification.

## Session Status (2026-06-04 Codex Stage 6 Deck Profile + Ground Truth)

Stan aktualny: dodano dane wejściowe wymagane przez preflight Stage 6 dla talii Gilded.

Co zostało zrobione: utworzono `biblioteka_talii/gilded/deck_profile.json` na podstawie `biblioteka_talii/gilded/info.json` oraz `logs/live_fixtures/event_first_current_debug_verified/ground_truth.json` z kompletem sześciu par state-first. Ponieważ ręczne tożsamości kart nie są potwierdzone, wszystkie niepuste etykiety używają `UNKNOWN_DECK`.

Kolejne kroki: preflight może przejść do `PASS`, ale benchmark Stage 6 będzie mierzył tylko unknown/reject behavior, dopóki Michał nie uzupełni ręcznych `expected_card_id`.

## Session Status (2026-06-04 Codex Stage 6 Manual Label Confirmation)

Stan aktualny: Stage 6 ground truth został ręcznie potwierdzony na podstawie debug sheetów Stage 5 i referencji Gilded.

Co zostało zrobione: zastąpiono `UNKNOWN_DECK` etykietami `Gilded_34`, `Gilded_54` i `Gilded_73` dla 10 cropów. `ground_truth.json` ma teraz `label_status: manual_confirmed`.

Kolejne kroki: można utworzyć `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`, ponieważ preflight i ręczne etykiety są gotowe do pomiaru top1/top3 accuracy.

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
- [x] Dodano `deck_profile.json` i strukturalny `ground_truth.json` dla Gilded.
- [x] Ręcznie potwierdzono etykiety Stage 6 i usunięto `UNKNOWN_DECK` z ground truth.
- [x] Uruchomiono pierwszą falę benchmarku Stage 6 Card Identification.
- [x] Przygotowano sześcioscenariuszową paczkę manual review dla `orb_bfmatcher_ratio_test`.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001`: Research Gate Stage 6 Card Identification.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001`: izolowany preflight wejść Stage 6.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-DECK-PROFILE-GROUNDTRUTH-001`: uzupełnienie `deck_profile.json` i strukturalnego `ground_truth.json` dla fixture Stage 6.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001`: ręczne uzupełnienie realnych `expected_card_id`.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`: pierwsza fala benchmarku.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-REVIEW-PACK-001`: manual review i decyzja Supervisora.

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

Aktualizacja po benchmarku: `orb_bfmatcher_ratio_test` jest `PROVISIONAL_RECOMMENDED`; następny bezpieczny krok to manual review Stage 6, bez integracji runtime.

Aktualizacja po przygotowaniu paczki: artefakt
`logs/offline_replay/stage6_manual_review_pack_orb_bfmatcher_ratio_test.zip`
jest gotowy do decyzji Supervisora.
