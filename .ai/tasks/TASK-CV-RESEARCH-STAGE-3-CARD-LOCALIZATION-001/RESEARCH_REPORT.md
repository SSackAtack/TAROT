# Research Report — Stage 3 Card Localization / Geometry Extraction

## Goal

Wybrać metody do przyszłego benchmarku Stage 3, który z zatwierdzonego regionu kandydata Stage 2 wyznaczy geometrię fizycznej karty.

Stage 3 nie robi jeszcze cropowania, deskew ani identyfikacji kart. Jego wynik ma przygotować dane geometryczne dla Stage 4:

```text
candidate region -> card_bbox / rotated_card_bbox / card_quad_points / geometry_confidence
```

## Inputs from Approved Stages

Zatwierdzony pipeline wejściowy:

```text
Stage 1: gray_absdiff_gaussian
previous_snapshot + current_snapshot -> difference mask

Stage 2: contour_external
difference mask -> candidate object/card regions
```

Wejście Stage 3:

```text
previous_snapshot
current_snapshot
stage1_mask
stage2_candidate_regions
pair_name
change_type
known_cards_state
```

Wyjście przyszłego Stage 3:

```text
card_bbox
rotated_card_bbox
card_quad_points
ordered_quad_points
card_geometry_confidence
localization_reject_reason
debug overlay
```

## Known Stage 2 Limitations

- Stage 2 bbox oznacza region kandydata obiektu/karty, nie finalny obrys karty.
- Bbox może zawierać tło, refleks, cień albo fragment maty.
- Bbox Stage 2 jest axis-aligned, nawet jeśli karta jest lekko obrócona.
- Stage 2 nie zwraca `quad_points`, orientacji karty ani geometrii gotowej do perspektywicznego cropowania.
- Nie wolno używać `contour_external` bbox bezpośrednio jako finalnego cropa.

## Research Questions

### 1. Jak znaleźć właściwy obrys karty wewnątrz regionu kandydata?

Najbezpieczniejszy kierunek to lokalna analiza wewnątrz ROI Stage 2:

```text
stage2_candidate_roi -> local edges/contours -> candidate geometry -> quality scoring
```

Techniki do rozważenia:

- kontury wewnątrz Stage 2 candidate region,
- największy kontur po lokalnym thresholdzie albo Canny,
- `approxPolyDP` do próby uzyskania czworokąta,
- `minAreaRect` jako stabilny rotated rectangle fallback,
- `boundingRect` / tight bbox jako baseline,
- convex hull jako stabilizacja poszarpanego konturu,
- edge-supported rectangle, czyli bbox/quad potwierdzany przez krawędzie,
- line detection przez Hough lines,
- LSD line detector, jeśli `cv2.createLineSegmentDetector` jest dostępny w aktualnym OpenCV.

W praktyce pierwszy benchmark powinien testować metody łatwe do debugowania: kontur, `approxPolyDP`, `minAreaRect` i hybrydy kontur + rect. Hough/LSD są sensowne jako warianty późniejsze albo diagnostyczne, bo wymagają więcej parametrów.

### 2. Jak odróżnić właściwą kartę od tła/refleksu w regionie?

Stage 3 powinien oceniać geometrię przez cechy, które mają sens dla fizycznej karty:

- border evidence na czterech bokach,
- edge density along candidate borders,
- rectangularity,
- aspect ratio consistency względem kart tarota,
- foreground fill,
- texture difference między wnętrzem karty i tłem,
- contrast on card border,
- dark/light border detection,
- corner evidence.

Refleks może mieć lokalnie wysoką jasność, ale zwykle nie ma czterech stabilnych boków, narożników i poprawnego aspect ratio. Karta może mieć słabą maskę diff, ale powinna mieć spójne border/corner evidence w obrazie aktualnym albo poprzednim, zależnie od `change_type`.

### 3. Jak obsłużyć kartę lekko obróconą?

`minAreaRect` i ordered quad points są kluczowe, bo Stage 2 bbox jest axis-aligned. Stage 3 powinien raportować:

- rotated bbox,
- angle,
- angle stability score,
- ordered corner points,
- geometry confidence,
- angle threshold do wykrywania niestabilnych wyników.

`approxPolyDP` może dać bezpośrednie quad points, ale przy poszarpanym konturze bywa niestabilny. `minAreaRect` jest bardziej odporny jako fallback, choć może zawyżać obrys przy refleksach.

### 4. Jak przygotować geometrię pod przyszły crop/deskew?

Stage 3 powinien dostarczyć dane, ale nie wykonywać cropowania:

- `ordered_quad_points`,
- `target_aspect_ratio`,
- `card_orientation`,
- `safe_padding`,
- `crop_margin`.

Najbardziej przyszłościowe metody to te, które zwracają albo quad, albo rotated rectangle łatwy do zamiany na ordered quad. Benchmark powinien jawnie mierzyć, czy metoda nadaje się do Stage 4 perspective transform.

### 5. Jak mierzyć jakość lokalizacji?

Proponowane metryki:

- `quad_area_ratio`,
- `bbox_area_ratio`,
- `aspect_ratio_error`,
- `rectangularity_score`,
- `border_score`,
- `corner_score`,
- `edge_support_score`,
- `angle_stability_score`,
- `candidate_to_stage2_area_ratio`,
- `geometry_confidence`,
- `localization_reject_reason`,
- `runtime_ms`.

Werdykt nie powinien bazować wyłącznie na liczbie geometrii. Trzeba raportować powód odrzucenia: brak konturu, zły aspect ratio, brak border evidence, zbyt niski confidence, zbyt niestabilny angle.

### 6. Jak zachować model state-first?

Benchmark Stage 3 nadal musi pracować na parach:

- `empty_to_empty`
- `empty_to_one_card`
- `empty_to_three_cards`
- `one_card_to_three_cards`
- `one_card_to_empty`
- `three_cards_to_empty`

Najważniejsza para: `one_card_to_three_cards`. Stage 3 ma lokalizować tylko nowe kandydaty kart dla `added` regions i regiony usunięcia dla `removed` regions, bez destabilizacji znanej karty. Dla `removed` geometrię należy wyznaczać ostrożnie, bo aktualny obraz zawiera tło po usunięciu; czasem lepszym obrazem referencyjnym do geometrii będzie `previous_snapshot`, nie `current_snapshot`.

## Candidate Techniques Matrix

| method_id | method_name | category | input | output | short_description | expected_strength | expected_weakness | cpu_cost_low_mid_high | dependencies | works_with_state_first_model | risk | recommended_status | benchmark_parameters | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| contour_largest_inside_candidate | Largest contour inside Stage 2 candidate | contour geometry | stage2 ROI + mask/edges | tight bbox + contour | Wybiera największy lokalny kontur w regionie kandydata. | Prosty, szybki, debugowalny. | Może wybrać refleks albo fragment grafiki, jeśli krawędź karty jest słaba. | low | OpenCV/NumPy | yes | low | TEST_NOW | local_threshold, canny_low/high, min_area_ratio | Dobry baseline Stage 3. |
| approx_poly_dp_quad | approxPolyDP quad | quad extraction | contour | quad points | Aproksymuje kontur do wielokąta i akceptuje 4 wierzchołki. | Daje bezpośrednie quad points pod Stage 4. | Wrażliwe na poszarpane kontury i zły epsilon. | low | OpenCV/NumPy | yes | medium | TEST_NOW | epsilon_ratio, min_area, aspect_tolerance | Testować jako metoda pierwszej klasy, ale z fallbackiem. |
| min_area_rect_candidate | minAreaRect candidate | rotated rectangle | contour/edge mask | rotated bbox + angle | Dopasowuje obrócony prostokąt do konturu. | Stabilny fallback dla lekko obróconej karty. | Może objąć tło przy zbyt dużym konturze. | low | OpenCV/NumPy | yes | low-medium | TEST_NOW | min_area, max_area, angle_threshold, aspect_tolerance | Priorytet do Stage 3. |
| bounding_rect_tight | Tight boundingRect | axis-aligned baseline | foreground/edge mask | bbox | Klasyczny tight bbox na foreground/edge. | Bardzo szybki baseline i dobry punkt porównania. | Nie obsługuje rotacji jako finalnej geometrii. | low | OpenCV/NumPy | yes | low | TEST_NOW | padding_px, min_fill, max_bbox_ratio | Baseline, nie finalna metoda przy rotacji. |
| edge_supported_bbox | Edge supported bbox | scoring/refinement | ROI + bbox/quad | bbox + score | Ocenia, ile boków boksu ma realne krawędzie. | Pomaga odróżnić kartę od refleksu. | Wymaga dobrania pasm i progów edge density. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | border_band_px, min_edge_support, canny thresholds | Bardzo ważny scoring jakości. |
| hough_lines_rectangle | Hough lines rectangle | line geometry | edge image | lines + rectangle | Wykrywa linie i próbuje złożyć prostokąt. | Może potwierdzić border przy słabym konturze. | Parametryczne, podatne na linie grafiki na karcie. | mid | OpenCV/NumPy | yes | medium-high | TEST_LATER | rho, theta, threshold, min_line_length, max_gap | Dobry wariant diagnostyczny po baseline. |
| lsd_lines_rectangle | LSD line detector rectangle | line geometry | grayscale ROI | segments + rectangle | Używa Line Segment Detector do znalezienia boków. | Precyzyjne krótkie segmenty bez akumulatora Hough. | Dostępność zależy od builda OpenCV; więcej logiki łączenia segmentów. | mid | OpenCV/NumPy if available | yes | medium-high | TEST_LATER | scale, sigma_scale, quant, min_segment_length | Sprawdzić `hasattr(cv2, "createLineSegmentDetector")`. |
| convex_hull_quad | Convex hull quad | contour refinement | contour | hull/quad | Stabilizuje poszarpany kontur przez convex hull. | Może poprawić contour-first przy dziurach. | Hull może wciągnąć refleks/tło i zawyżyć geometrię. | low | OpenCV/NumPy | yes | medium | TEST_LATER | hull_area_ratio, approx_epsilon | Backup do approxPolyDP. |
| corner_detection_good_features | goodFeaturesToTrack corners | corner evidence | grayscale ROI | corner points + score | Szuka narożników metodą Shi-Tomasi/Harris. | Dobre jako scoring corner evidence. | Narożniki grafiki karty mogą konkurować z narożnikami krawędzi. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | max_corners, quality_level, min_distance, border_mask | Używać jako scoring, nie samodzielna geometria. |
| border_evidence_scoring | Border evidence scoring | quality scoring | candidate geometry + edges | border_score | Mierzy krawędzie/kontrast w pasmach boków. | Silny filtr karta vs refleks/tło. | Wymaga wyboru szerokości pasma i obsługi jasnych/ciemnych bordów. | low | OpenCV/NumPy | yes | low-medium | TEST_NOW | band_px, edge_density_min, contrast_min | Kluczowy scoring dla Stage 3. |
| projection_profile_tight_bbox | Projection profile tight bbox | bbox refinement | local edge/foreground mask | tight bbox | Profile X/Y przycinają puste marginesy w ROI. | Proste i szybkie zawężenie geometrii. | Nie zwraca rotacji ani quad points. | low | OpenCV/NumPy | yes | low | TEST_NOW | projection_threshold, padding_px, min_band_width | Dobry baseline refinement. |
| hybrid_contour_plus_min_area_rect | Contour + minAreaRect hybrid | hybrid geometry | contour + ROI | rotated bbox + confidence | Największy kontur -> minAreaRect -> scoring aspect/border. | Dobra równowaga prostoty, rotacji i debugowalności. | Nadal zależy od jakości lokalnej maski/edge. | low-mid | OpenCV/NumPy | yes | low-medium | TEST_NOW | canny thresholds, min_area, aspect_tolerance, border_score_min | Rekomendowany główny wariant TEST_NOW. |
| hybrid_edge_plus_contour | Edge + contour hybrid | hybrid geometry | Canny ROI + contours | quad/rotated bbox | Łączy krawędzie z konturem, żeby nie bazować tylko na diff mask. | Lepsze przy słabej masce Stage 1/2. | Może złapać grafikę wewnątrz karty. | mid | OpenCV/NumPy | yes | medium | TEST_NOW | canny thresholds, morphology_close, contour_filter | Warto testować obok contour-first. |
| threshold_local_card_border | Local border threshold | local segmentation | ROI grayscale/color | border mask | Lokalnie progowuje kontrast bordera karty. | Może pomóc przy jasnych/ciemnych ramkach kart. | Zależne od talii i oświetlenia. | low-mid | OpenCV/NumPy | yes | medium | TEST_LATER | threshold_mode, adaptive_block_size, color_channel | Odłożyć po pierwszym benchmarku. |
| template_orb_geometry | ORB-assisted geometry | feature geometry | ROI + card templates | homography/quad | Używa cech wzorca do geometrii. | Może dać precyzyjną geometrię dla znanych kart. | Miesza Stage 3 z identyfikacją; ryzyko scope creep. | mid-high | existing OpenCV ORB | partial | high | REJECT_FOR_NOW | n/a | Stage 3 ma być przed identyfikacją. |
| learned_keypoint_detector | ML keypoint/corner detector | learned geometry | ROI | card corners | Potencjalnie najlepsze przy trudnym świetle. | Nowe dane, trening, zależności i runtime risk. | high | new deps/model | possible | high | REQUIRES_APPROVAL | model type, training data | Nie pasuje do aktualnego CPU-only offline gate. |

## Methods Recommended for TEST_NOW

Recommended `TEST_NOW` shortlist:

1. `contour_largest_inside_candidate`
2. `approx_poly_dp_quad`
3. `min_area_rect_candidate`
4. `bounding_rect_tight`
5. `edge_supported_bbox`
6. `border_evidence_scoring`
7. `projection_profile_tight_bbox`
8. `corner_detection_good_features`
9. `hybrid_contour_plus_min_area_rect`
10. `hybrid_edge_plus_contour`

Uzasadnienie: te metody są CPU-only, mieszczą się w OpenCV/NumPy, są debugowalne overlayami i dają jasne metryki geometrii. `hybrid_contour_plus_min_area_rect` powinien być testowany jako kandydat praktyczny, ale benchmark musi porównać go z prostszymi baseline'ami.

## Methods Recommended for TEST_LATER

- `hough_lines_rectangle`
- `lsd_lines_rectangle`
- `convex_hull_quad`
- `threshold_local_card_border`

Uzasadnienie: metody liniowe i hull mogą być wartościowe, ale zwiększają liczbę parametrów i ryzyko łapania grafiki na karcie zamiast krawędzi fizycznej. Najpierw trzeba mieć baseline kontur/rect/scoring.

## Methods Rejected for Now

- `template_orb_geometry`
- pełne feature matching / homography na kartach,
- metody wymagające rozpoznania tożsamości karty przed geometrią.

Uzasadnienie: mieszałyby Stage 3 z późniejszą identyfikacją i naruszały separację pipeline.

## Methods Requiring Approval

- `learned_keypoint_detector`
- ML card corner detector,
- nowe zależności poza OpenCV/NumPy,
- zmiana scope z offline labu na runtime.

## Proposed Stage 3 Benchmark

Następny task:

```text
TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001
```

### Input

Fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

Zatwierdzony pipeline wejściowy:

```text
Stage 1: gray_absdiff_gaussian
Stage 2: contour_external
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

### Metrics

```text
method
pair
candidate_count
localized_card_count
expected_localized_count
localization_delta
quad_count
bbox_count
rotated_bbox_count
aspect_ratio_avg
aspect_ratio_error_avg
quad_area_ratio_avg
border_score_avg
edge_support_score_avg
corner_score_avg
geometry_confidence_avg
reject_count
reject_reasons
runtime_ms
verdict
verdict_basis
```

### Output Debug

```text
logs/offline_replay/stage3_card_localization/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/stage2_candidate_overlay.png
  <method>/<pair>/card_geometry_overlay.png
  <method>/<pair>/edge_debug.png
  <method>/<pair>/contour_debug.png
  <method>/<pair>/geometry_debug.json
```

### Verdict Direction

Minimalny `PASS` powinien wymagać:

- `empty_to_empty`: zero zlokalizowanych geometrii,
- `empty_to_one_card`: jedna geometria z poprawnym aspect ratio i confidence,
- `empty_to_three_cards`: trzy geometrie,
- `one_card_to_three_cards`: dwie nowe geometrie bez destabilizacji znanej karty,
- `one_card_to_empty`: jedna geometria regionu usunięcia,
- `three_cards_to_empty`: trzy geometrie regionów usunięcia,
- brak agresywnego crop/deskew/identification.

## Recommended Next Action

Nie implementować jeszcze Stage 3 benchmarku.

Najpierw Supervisor powinien zaakceptować albo skorygować shortlistę `TEST_NOW`. Po akceptacji utworzyć:

```text
TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001
```

Benchmark powinien pozostać izolowany w `tools/cv_detection_lab/`, bez zmian runtime.

## Sources

- OpenCV shape analysis, contours, `approxPolyDP`, `boundingRect`, `minAreaRect`, `convexHull`: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
- OpenCV contour features tutorial: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html
- OpenCV Hough Line Transform tutorial: https://docs.opencv.org/4.x/d9/db0/tutorial_hough_lines.html
- OpenCV Line Segment Detector API: https://docs.opencv.org/4.x/db/d73/classcv_1_1LineSegmentDetector.html
- OpenCV `goodFeaturesToTrack`: https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html
