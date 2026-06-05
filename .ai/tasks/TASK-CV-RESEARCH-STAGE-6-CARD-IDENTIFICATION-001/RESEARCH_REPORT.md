# Research Report — Stage 6 Card Identification

## Goal

Stage 6 ma zidentyfikowac, jaka karta znajduje sie w cropie wygenerowanym przez Stage 4 i ocenionym przez Stage 5.

Ten research wybiera metody do przyszlego benchmarku. Nie zatwierdza finalnej metody identyfikacji kart, nie implementuje benchmarku i nie zmienia runtime.

## Inputs from Approved Stages

Zatwierdzony pipeline wejscia:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
Stage 3: hybrid_edge_plus_contour
Stage 4: quad_warp_perspective_fixed_aspect__resize_only_normalization
Stage 5: quality_metric_suite_v1
```

Wejscie przyszlego Stage 6:

```text
normalized_crop
crop_quality_status
quality_flags
identification_readiness_score
warning_reason
reject_reason
crop_metadata
reference_deck_dir
deck_profile.json
ground_truth.json
```

Wyjscie przyszlego Stage 6:

```text
predicted_card_id
predicted_card_name
confidence_score
top_k_candidates
match_evidence
reject_reason
warning_flags
identification_method
runtime_ms
```

## Known Stage 5 Limitations

Stage 5 zatwierdzil `quality_metric_suite_v1`, ale z waznym ograniczeniem:

```text
All real crop samples in the current fixture are YELLOW, not PASS.
```

Konsekwencje dla Stage 6:

- identyfikacja musi dzialac na cropach sredniej jakosci,
- metoda nie moze zakladac wysokiej ostrosci ani idealnego kontrastu,
- wynik identyfikacji musi raportowac `crop_quality_status`, `quality_flags` i `identification_readiness_score`,
- niski readiness powinien obnizac zaufanie, zwiekszac ryzyko `AMBIGUOUS_MATCH` albo prowadzic do `LOW_CONFIDENCE`,
- Stage 6 nie powinien wymuszac predykcji, gdy dowody sa slabe.

## Reference Deck Requirements

Stage 6 bez poprawnej bazy referencyjnej nie moze wiarygodnie identyfikowac kart.

Wymagane minimum:

- `reference_deck_dir` wskazujacy folder obrazow referencyjnych, np. `biblioteka_talii/<deck>/produkcja/wzorce_cv`,
- `deck_profile.json` opisujacy `deck_id`, `display_name`, `prefix`, liczbe kart, zakres kart, sciezki i wersje profilu,
- stabilne `card_id`, np. `RWS_00`, `RWS_17`, `Gilded_17`,
- czytelne `card_name`, mapowane osobno od technicznego `card_id`,
- informacja, czy deck ma rewers (`has_back`) i jak rozpoznawac front/back,
- polityka orientacji: `upright`, `reversed`, `unknown_orientation`,
- informacja, czy benchmark ogranicza sie do 22 Major Arcana czy do pelnych 78 kart,
- wersjonowanie profilu decku, np. `deck_profile_version: 1`.

W repo istnieje manifest talii `app_ar/public/decks_manifest.json`, aktywne talie `app_ar/public/active_decks.json` i foldery `biblioteka_talii/*/produkcja/wzorce_cv`. Obecny runtime ma `reference_loader.py`, ktory laduje obrazy referencyjne i deskryptory ORB. Stage 6 benchmark moze inspirowac sie tym ksztaltem danych, ale powinien miec wlasny jawny input `reference_deck_dir` oraz `deck_profile.json`, zeby wynik offline byl reprodukowalny.

Krytyczne rozroznienie:

- docelowy minimalny zakres produktu: 22 karty Wielkich Arkanow Rider-Waite-Smith,
- aktualne live fixture: cropy moga pochodzic z innej talii albo z innego zakresu kart.

Nie wolno zakladac, ze aktualne cropy sa zgodne z baza 22 RWS Major Arcana, dopoki `ground_truth.json` i `deck_profile.json` tego nie potwierdza.

## Ground Truth Requirements

Benchmark Stage 6 wymaga etykiet. Bez nich mozna mierzyc tylko techniczne score, ale nie skutecznosc identyfikacji.

Proponowany plik:

```text
logs/live_fixtures/event_first_current_debug_verified/ground_truth.json
```

Proponowany format:

```json
{
  "deck_profile_id": "rider-waite-smith",
  "deck_profile_version": 1,
  "pairs": {
    "empty_to_one_card": [
      {
        "crop_index": 1,
        "expected_card_id": "RWS_17",
        "expected_card_name": "Gwiazda",
        "orientation": "upright"
      }
    ],
    "empty_to_three_cards": [
      {
        "crop_index": 1,
        "expected_card_id": "UNKNOWN_DECK",
        "expected_card_name": null,
        "orientation": "unknown"
      }
    ]
  }
}
```

Dla `removed` etykieta dotyczy cropa z `previous_snapshot`. Dla `one_card_to_three_cards` etykietujemy tylko nowe karty wykryte przez state-first diff, a nie karte juz obecną w poprzednim stanie.

Ground truth musi umiec zapisac:

- poprawna karte,
- `unknown_deck`,
- `not_in_reference_scope`,
- orientacje `upright` / `reversed` / `unknown`,
- opcjonalna adnotacje manualna dla niepewnych cropow.

## Research Questions

### 1. Jaka baze referencyjna musi miec Stage 6?

Stage 6 potrzebuje jawnego `reference_deck_dir`, profilu decku i mapowania `card_id -> card_name`. Jeden obraz referencyjny na karte wystarczy do pierwszego benchmarku, ale wiele wariantow na karte bedzie lepsze dla realnej odporności: skan referencyjny, wariant jasnosci/kontrastu, wariant 180 stopni albo wariant rewersu.

Front/back detection powinien byc osobnym wynikiem pomocniczym. Rewers nie jest karta do interpretacji; jesli crop pasuje do back texture, wynik powinien byc `CARD_BACK_DETECTED` albo `NO_FRONT_CARD`.

### 2. Jak rozpoznawac karty klasycznie, bez ML?

Najbardziej praktyczne sa metody lokalnych cech i metody globalnego podobienstwa:

- ORB + BFMatcher ratio test: szybki baseline, zgodny z OpenCV, dobry CPU-only,
- ORB + FLANN LSH: potencjalnie szybszy przy wielu referencjach,
- AKAZE / BRISK: alternatywy binarne, czesto stabilniejsze przy innym typie tekstury,
- SIFT: dobry jakosciowo, ale wymaga potwierdzenia dostepnosci w buildzie OpenCV i akceptacji kosztu CPU,
- template matching multiscale: proste, ale kruche wobec perspektywy i jasnosci,
- histogram HSV: tani sygnal deck/card-family, ale zbyt slaby jako jedyna identyfikacja,
- edge/layout similarity: odporniejsze na kolor, ale nie rozroznia podobnych kart samodzielnie,
- perceptual hash / SSIM-like luma: dobre jako tanie sanity/reranking bez nowych zaleznosci.

### 3. Jak rozpoznawac karty przy sredniej jakosci cropach?

Dla cropow `YELLOW` Stage 6 powinien:

- laczyc metody lokalnych cech z globalnym podobienstwem,
- stosowac top-k, a nie tylko top-1,
- raportowac `confidence_gap`,
- odrzucac wyniki z mala liczba dobrych dopasowan albo z malym gapem,
- obnizac confidence, gdy `identification_readiness_score` jest niski,
- porownywac crop normalny i obrocony o 180 stopni,
- nie mylic paddingu/czarnego tla z cechami karty.

Praktyczny baseline: ORB/AKAZE jako dowod lokalny plus histogram/edge/SSIM-like jako reranking lub ensemble.

### 4. Jak obslugiwac top-k zamiast jednej odpowiedzi?

Kazda metoda powinna zwracac:

```text
top_1
top_3
confidence_score
confidence_gap
ambiguous_match
reject_if_low_confidence
manual_review_if_ambiguous
```

Regula benchmarkowa:

- jesli `top1_score` jest niski: `LOW_CONFIDENCE`,
- jesli `top1 - top2` jest maly: `AMBIGUOUS_MATCH`,
- jesli `top3` zawiera expected, ale top1 nie: `top3_contains_expected=True`, `top1_correct=False`,
- jesli referencji brak albo talia nie pasuje: `NO_REFERENCE_MATCH` albo `UNKNOWN_DECK`.

### 5. Jak wykrywac reversed / upside-down?

Najprostszy benchmark:

- uruchomic matching dla cropa normalnego,
- uruchomic matching dla cropa obroconego o 180 stopni,
- porownac `upright_score` i `reversed_score`,
- zapisac `reversed_candidate=True`, gdy reversed score ma istotna przewage,
- nie integrowac jeszcze reversed z runtime ani AR.

Jesli metoda jest orientacyjnie niewrazliwa, reversed nadal musi byc raportowane przez osobne porownanie wynikow lub przez orientation evidence.

### 6. Jak obsluzyc brak zgodnosci decku?

Wymagane statusy:

```text
UNKNOWN_DECK
NO_REFERENCE_MATCH
LOW_CONFIDENCE
AMBIGUOUS_MATCH
```

Jesli crop pochodzi z talii spoza `reference_deck_dir`, prawidlowym zachowaniem jest odrzucenie albo oznaczenie niepewnosci, nie wymuszenie najblizszej karty RWS.

### 7. Jak mierzyc skutecznosc benchmarku Stage 6?

Proponowane metryki:

- `accuracy_top1`,
- `accuracy_top3`,
- `unknown_reject_rate`,
- `false_positive_rate`,
- `confidence_gap`,
- `mean_runtime_ms`,
- `per_card_success`,
- `per_quality_status_success`,
- `per_warning_flag_success`,
- `reversed_detection_accuracy`,
- `ambiguous_match_rate`.

Do tych metryk wymagane sa ground truth labels.

### 8. Jak przygotowac ground truth?

Ground truth powinien byc para-centric, bo state-first benchmark operuje na parach zmian. Kluczowe jest `crop_index`, `expected_card_id`, `expected_card_name`, `orientation` i deck profile. Jesli obecna talia nie jest RWS Major Arcana, etykiety musza wskazac poprawny deck albo `unknown_deck`.

### 9. Jak zachowac model state-first?

Benchmark Stage 6 dziala na tych samych parach:

```text
empty_to_empty
empty_to_one_card
empty_to_three_cards
one_card_to_three_cards
one_card_to_empty
three_cards_to_empty
```

Dla `removed` identyfikujemy karte z `previous_snapshot`. Dla `one_card_to_three_cards` identyfikujemy tylko nowe karty wynikajace z diffu, nie istniejaca juz karte srodkowa.

### 10. Jak nie pomieszac Stage 6 z runtime?

Stage 6 benchmark dziala offline. Nie zmienia WebSocket payload, Studio UI, publikacji layoutu ani runtime. Nie dotyka `SnapshotFirstPipeline`, `ChangeDetector`, ArUco ani aktywnego stanu stolika.

## Candidate Techniques Matrix

| method_id | method_name | category | input | output | short_description | expected_strength | expected_weakness | cpu_cost_low_mid_high | dependencies | works_with_state_first_model | works_with_yellow_crops | requires_reference_deck | requires_ground_truth | risk | recommended_status | benchmark_parameters | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orb_bfmatcher_ratio_test | ORB + BFMatcher ratio test | local features | normalized_crop, references | top_k, matches, confidence | ORB descriptors matched with Hamming BF and ratio test. | Fast, existing repo already uses ORB references, debug-friendly. | Can fail on blurry/low-detail YELLOW crops. | low-mid | OpenCV/NumPy | yes | partial | yes | yes | medium | TEST_NOW | nfeatures, ratio, min_good_matches, gap_threshold | First baseline. |
| orb_flann_lsh | ORB + FLANN LSH | local features | normalized_crop, references | top_k, matches, confidence | Binary descriptors matched via FLANN LSH. | Better scaling for many references. | More parameters, can be less predictable than BF on small sets. | mid | OpenCV/NumPy | yes | partial | yes | yes | medium | TEST_NOW | table_number, key_size, multi_probe_level, ratio | Compare to BF. |
| akaze_bfmatcher | AKAZE + BFMatcher | local features | normalized_crop, references | top_k, matches, confidence | AKAZE binary features with Hamming BF. | Often robust to nonlinear blur/texture changes. | Slower than ORB, fewer features on flat art. | mid | OpenCV/NumPy | yes | partial-good | yes | yes | medium | TEST_NOW | threshold, descriptor_size, ratio, min_matches | Strong alternative to ORB. |
| brisk_bfmatcher | BRISK + BFMatcher | local features | normalized_crop, references | top_k, matches, confidence | BRISK binary features with BF matching. | CPU-only and available in OpenCV. | Can be noisy; may underperform on resized tarot art. | mid | OpenCV/NumPy | yes | partial | yes | yes | medium | TEST_NOW | threshold, octaves, ratio, min_matches | Include as comparator. |
| sift_bfmatcher_if_available | SIFT + BFMatcher/FLANN | local features | normalized_crop, references | top_k, matches, confidence | Float descriptors with SIFT if available in local OpenCV build. | Stronger under scale/lighting changes. | Higher CPU, availability must be checked, not baseline for HP G6. | high | OpenCV contrib/build-dependent | yes | good | yes | yes | medium-high | REQUIRES_APPROVAL | nfeatures, contrastThreshold, ratio | Test only after approval. |
| template_matching_multiscale | Multiscale template matching | direct similarity | normalized_crop, references | top_k, max_corr | Resize/scale search with cv2.matchTemplate. | Simple and explainable. | Brittle to perspective, crop offset, illumination and deck mismatch. | mid-high | OpenCV/NumPy | yes | weak-partial | yes | yes | high | TEST_LATER | scales, mask_border, method | Useful fallback for controlled RWS only. |
| histogram_similarity_hsv | HSV histogram similarity | global color/layout | normalized_crop, references | top_k, histogram distance | Compares HSV histograms. | Very cheap, robust to mild blur. | Not discriminative enough alone. | low | OpenCV/NumPy | yes | good | yes | yes | medium | TEST_NOW | bins_hsv, compare_method, crop_inner_ratio | Use as reranker/ensemble signal. |
| edge_layout_similarity | Edge/layout similarity | structural global | normalized_crop, references | top_k, edge distance | Compare Canny/Sobel edge maps after normalization. | Less color-sensitive, useful for layouts. | Similar cards can collide; sensitive to crop shift. | low-mid | OpenCV/NumPy | yes | partial-good | yes | yes | medium | TEST_NOW | canny thresholds, resize size, inner_crop | Good non-feature signal. |
| perceptual_hash_opencv | Perceptual hash via OpenCV/NumPy | global hash | normalized_crop, references | hamming distance top_k | DCT/average-hash style fingerprint without new dependency. | Very cheap, good for near-identical reference/crop. | Weak under perspective, deck mismatch and lighting. | low | OpenCV/NumPy/stdlib | yes | partial | yes | yes | medium | TEST_LATER | hash_size, dct_size, luma_only | Backup sanity check. |
| ssim_like_luma | SSIM-like luma similarity | direct similarity | normalized_crop, references | top_k, similarity | Lightweight luminance structural similarity approximation. | Debuggable, no new dependency, good reranking. | Not invariant to local crop shifts and deck mismatch. | mid | OpenCV/NumPy | yes | partial-good | yes | yes | medium | TEST_NOW | resize, gaussian_window, inner_crop | Good complement to ORB/AKAZE. |
| hybrid_orb_plus_histogram | ORB plus HSV histogram | hybrid | normalized_crop, references, Stage 5 metrics | top_k, confidence, evidence | Combine local ORB evidence with histogram reranking and readiness penalty. | Better on YELLOW crops than ORB alone. | Requires careful weights and calibration. | mid | OpenCV/NumPy | yes | good | yes | yes | medium | TEST_NOW | orb_weight, hist_weight, readiness_penalty, gap | Primary hybrid candidate. |
| hybrid_akaze_plus_histogram | AKAZE plus HSV histogram | hybrid | normalized_crop, references, Stage 5 metrics | top_k, confidence, evidence | AKAZE local evidence plus color/global reranking. | Robust alternative when ORB descriptors are sparse. | Slower than ORB hybrid. | mid-high | OpenCV/NumPy | yes | good | yes | yes | medium | TEST_NOW | akaze_weight, hist_weight, min_matches | Important comparator. |
| top_k_vote_ensemble | Top-k vote ensemble | ensemble | method scores | final top_k, confidence, ambiguity | Combines ORB/AKAZE/hist/edge/SSIM rankings. | Best failure handling and ambiguity detection. | More complex; depends on calibrated component scores. | mid-high | OpenCV/NumPy | yes | good | yes | yes | medium | TEST_NOW | method_weights, min_votes, confidence_gap | Benchmark as ensemble, not final runtime yet. |
| ml_classifier_external | ML classifier / embeddings | ML | crop, model | predicted class | Learned model or embedding similarity. | Could improve long-term robustness. | New deps, model training/selection, data need, approval needed. | high | new ML deps/model | yes | possible | yes | yes | high | REQUIRES_APPROVAL | model_name, labels, hardware | Not for this offline gate. |
| ocr_card_title | OCR title/text recognition | OCR | crop | text candidates | Read card title or symbols. | Useful for decks with clear titles. | New deps or weak OCR; fails on stylized cards and Polish/English variants. | high | new OCR deps likely | yes | weak | yes | yes | high | REJECT_FOR_NOW | n/a | Out of current no-new-deps scope. |

## Methods Recommended for TEST_NOW

Recommended TEST_NOW shortlist:

1. `orb_bfmatcher_ratio_test`
2. `orb_flann_lsh`
3. `akaze_bfmatcher`
4. `brisk_bfmatcher`
5. `histogram_similarity_hsv`
6. `edge_layout_similarity`
7. `ssim_like_luma`
8. `hybrid_orb_plus_histogram`
9. `hybrid_akaze_plus_histogram`
10. `top_k_vote_ensemble`

Uzasadnienie: wszystkie sa CPU-only, moga dzialac na OpenCV/NumPy/stdlib, nie wymagaja trenowania modelu i daja sie debugowac na HP EliteBook 830 G6. Shortlista zawiera metody lokalnych cech, metody globalne oraz hybrydy potrzebne dla cropow `YELLOW`.

## Methods Recommended for TEST_LATER

- `template_matching_multiscale` — proste, ale ryzykowne przy nieidealnych cropach; warto dopiero po baseline feature matching.
- `perceptual_hash_opencv` — dobry tani sanity check, ale za slaby jako samodzielny kandydat pierwszej fali.

## Methods Rejected for Now

- `ocr_card_title` — nie dodajemy OCR ani nowych zaleznosci, a tytuly kart moga byc stylizowane, zasloniete albo w innym jezyku.

## Methods Requiring Approval

- `sift_bfmatcher_if_available` — wymaga potwierdzenia dostepnosci w lokalnym buildzie OpenCV i akceptacji wyzszego CPU cost.
- `ml_classifier_external` — wymaga nowych zaleznosci/modelu/datasetu i osobnej decyzji architektonicznej.

## Proposed Stage 6 Benchmark

Nastepny task:

```text
TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001
```

Fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

Zatwierdzony pipeline wejscia:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
Stage 3: hybrid_edge_plus_contour
Stage 4: quad_warp_perspective_fixed_aspect__resize_only_normalization
Stage 5: quality_metric_suite_v1
```

Wymagane dodatkowe wejscia:

```text
reference_deck_dir
deck_profile.json
ground_truth.json
```

Pary testowe:

```text
empty_to_empty
empty_to_one_card
empty_to_three_cards
one_card_to_three_cards
one_card_to_empty
three_cards_to_empty
```

Proponowane kolumny `matrix.csv`:

```text
method
pair
crop_index
change_type
crop_source_frame
crop_quality_status
identification_readiness_score
expected_card_id
predicted_card_id
top1_correct
top3_contains_expected
confidence_score
confidence_gap
ambiguous_match
reject_reason
warning_flags
unknown_deck_flag
reference_match_count
good_match_count
inlier_count
runtime_ms
verdict
verdict_basis
```

Proponowane outputy:

```text
logs/offline_replay/stage6_card_identification/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/identification_debug_sheet.png
  <method>/<pair>/crop_01_matches.png
  <method>/<pair>/crop_01_candidates.json
  <method>/<pair>/identification_debug.json
```

Werdykt benchmarku:

- `PASS`, gdy top1/top3 i confidence spelniaja zalozone progi dla etykiet znanych,
- `YELLOW`, gdy expected jest w top3, ale top1 jest bledny albo confidence gap jest maly,
- `FAIL`, gdy top-k nie zawiera expected albo metoda wymusza bledna predykcje,
- `PASS_UNKNOWN_REJECT`, gdy ground truth oznacza `unknown_deck` i metoda odmawia identyfikacji.

## Recommended Next Action

Supervisor powinien zaakceptowac albo skorygowac shortlistę `TEST_NOW`.

Po akceptacji utworzyc:

```text
TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001
```

Benchmark Stage 6 musi pozostac izolowany w `tools/cv_detection_lab/`, bez runtime, bez Studio i bez WebSocket.
