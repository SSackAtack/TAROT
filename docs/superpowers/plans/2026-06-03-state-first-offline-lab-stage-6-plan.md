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
- [x] Supervisor zatwierdził `orb_bfmatcher_ratio_test` dla bieżącego offline lab fixture.
- [x] Uruchomiono deterministyczny synthetic validation benchmark na 192 próbkach.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001`: Research Gate Stage 6 Card Identification.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001`: izolowany preflight wejść Stage 6.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-DECK-PROFILE-GROUNDTRUTH-001`: uzupełnienie `deck_profile.json` i strukturalnego `ground_truth.json` dla fixture Stage 6.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001`: ręczne uzupełnienie realnych `expected_card_id`.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`: pierwsza fala benchmarku.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-REVIEW-PACK-001`: manual review i decyzja Supervisora.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-METHOD-APPROVAL-001`: dokumentacyjne utrwalenie decyzji Supervisora.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001`: syntetyczny validation benchmark ORB vs AKAZE.

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

Aktualizacja po decyzji Supervisora:
`APPROVED_STAGE_6_METHOD: orb_bfmatcher_ratio_test`.
Approved for current offline lab fixture only. No runtime integration approval.
Następny bezpieczny krok: przygotować szerszy Stage 6 validation benchmark.

## Session Status (2026-06-04 Codex Synthetic Validation)

Stan aktualny: `orb_bfmatcher_ratio_test` przeszedł syntetyczny validation
benchmark offline na 168 known i 24 wrong-deck samples.

Co zostało zrobione: dodano deterministyczny generator, reversed, trudne
warianty, wrong-deck rejection, porównanie z AKAZE, runtime local proxy oraz
raporty per method/category/orientation. ORB i AKAZE osiągnęły 100% top-1/top-3
i 0% wrong-deck FAR; ORB był szybszy.

Kolejne kroki: `TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001`.
Przed integracją runtime wymagany jest szerszy real-camera fixture. Offline
threshold i runtime integration pozostają niezatwierdzone.

Decyzja Supervisora: `APPROVED_BY_CHATGPT_SUPERVISOR`.
Status metody pozostaje `VALIDATION_PASS_OFFLINE_ONLY`.

## Session Status (2026-06-04 Codex Real-Camera Identification Benchmark)

Stan aktualny: zatwierdzony real-camera fixture został przetworzony przez
offline benchmark ORB vs AKAZE.

Co zostało zrobione: dodano deterministyczną ekstrakcję pojedynczej karty z
real-camera analysis frame, metryki per category i similarity group,
wrong-deck FAR oraz local runtime proxy. ORB osiągnął Top-1 `0.80`, Top-3
`0.85`, wrong-deck FAR `0.00`; AKAZE osiągnął Top-1/Top-3 `0.70` i FAR `0.75`.

Kolejne kroki: Supervisor ocenia wynik. Benchmark nie zatwierdza progu ani
integracji runtime; trudne próbki YELLOW pozostają głównym ograniczeniem
(ORB Top-1 `0.50`).

## Session Status (2026-06-04 Codex Real-Camera Error Analysis)

Stan aktualny: wykonano offline analizę czterech błędów Top-1 ORB.

Co zostało zrobione: wygenerowano review pack z pełnym `matrix.csv`, raportem
benchmarku, 28 extracted crops oraz czterema planszami porównującymi crop,
oczekiwaną referencję i predykcję. Trzy błędy mają bardzo słaby sygnał i są
związane z jakością obrazu/cropu. Dla próbki `f8d6d84b5ddb5729fa07` wykryto
podejrzenie błędnego ground truth: etykieta mówi `Gilded_45`, ale crop wizualnie
przedstawia `Gilded_67`, zgodnie z silną predykcją ORB.

Kolejne kroki: ręcznie potwierdzić podejrzaną etykietę przed ponownym
przeliczeniem metryk. Nie wolno zmieniać ground truth automatycznie ani
integrować metody z runtime.

## Session Status (2026-06-04 Codex Ground Truth Review)

Stan aktualny: podejrzana próbka `f8d6d84b5ddb5729fa07` została ręcznie
potwierdzona jako `Gilded_67` (Cesarz), nie `Gilded_45` (Sprawiedliwość).

Co zostało zrobione: skorygowano lokalny manifest i ground truth, uruchomiono
preflight (`PASS`), benchmark oraz error analysis ponownie. ORB osiąga teraz
Top-1 `0.85`, Top-3 `0.90`, wrong-deck FAR `0.00`. Pozostały trzy błędy Top-1,
wszystkie sklasyfikowane jako `image_quality_or_crop`.

Kolejne kroki: Supervisor zatwierdza korektę danych i nowe metryki offline-only.
Nadal brak zgody na runtime integration.

## Session Status (2026-06-04 Codex Quality Gate Design)

Stan aktualny: ground truth review został zatwierdzony przez Supervisora jako
`APPROVED_OFFLINE_GROUND_TRUTH_CORRECTION`. ORB pozostaje
`ORB_REAL_CAMERA_VALIDATED_OFFLINE_ONLY_AFTER_GT_FIX`.

Co zostało zrobione: przeanalizowano trzy pozostałe błędy jakości/cropu.
Istniejący Stage 5 quality suite nie wykrywa ich odblasków: raportuje
`overexposed_pixel_ratio = 0.0`, `top_reflection_score = 0.0` i wysokie
readiness. Zaprojektowano offline-only quality gate oparty o lokalne komponenty
specular highlight, occlusion ratio i usable detail poza odblaskiem.

Kolejne kroki: Supervisor ocenia projekt quality gate. Po akceptacji można
utworzyć mały benchmark offline-only, bez zmian runtime.

## Session Status (2026-06-04 Codex Quality Gate Benchmark)

Stan aktualny: offline quality gate benchmark został wykonany na 28 real-camera
crops.

Co zostało zrobione: zaimplementowano lokalne maski highlightu, occlusion ratio,
usable detail i decyzje ACCEPT / RETRY / MANUAL_REVIEW. Wszystkie trzy znane
błędy jakości zostały zatrzymane, bez false retry dla dobrych i wrong-deck
próbek. ORB accuracy na ACCEPT subset wynosi `1.0`.

Kolejne kroki: Supervisor ocenia review pack. Progi są benchmark-only i nie
mogą zostać przeniesione do runtime bez osobnej decyzji.

## Session Status (2026-06-04 Codex Real-Camera Fixture Phase A)

Stan aktualny: offline tooling real-camera aggregate jest gotowy, ale task
pozostaje `PROVISIONAL_BLOCKED`.

Co zostało zrobione: dodano read-only kontrakt manifestu/ground truth,
fingerprint sesji, preflight, manual review pack generator i instrukcję
operatorską.

Kolejne kroki: operator musi zebrać minimum 28 fizycznych sesji i ręcznie
potwierdzić ground truth. Bez tego nie wolno raportować `PASS`.
