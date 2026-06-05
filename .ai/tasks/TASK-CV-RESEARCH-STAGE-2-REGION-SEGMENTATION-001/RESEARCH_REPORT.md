# Research Report — Stage 2 Region Segmentation / Region Refinement

## Goal

Wybrać metody do kolejnego benchmarku offline, który przekształci regiony zmiany ze Stage 1 w stabilniejsze regiony kart.

Stage 2 nie ma jeszcze rozpoznawać kart. Ma przygotować lepszy region wejściowy dla późniejszego cropowania, klasyfikacji i ewentualnego state update.

## Inputs from Stage 1

Zatwierdzona metoda Stage 1:

```text
APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
```

Wejście Stage 2:

```text
previous_snapshot
current_snapshot
stage1_diff
stage1_mask
stage1_regions
known_cards_state
pair_name
change_type
```

Obowiązkowe pary state-first:

- `empty -> empty`
- `empty -> one_card`
- `empty -> three_cards`
- `one_card -> three_cards`
- `one_card -> empty`
- `three_cards -> empty`

Najważniejsza para kaskadowa: `one_card -> three_cards`, bo Stage 2 musi znaleźć tylko nowe karty bez destabilizowania karty już znanej w stanie.

## Known Stage 1 Limitations

- Bbox Stage 1 opisuje region zmiany, nie finalny obrys karty.
- Przy trzech kartach jeden region może obejmować fragment tła albo refleks między kartami.
- Zmiana po usunięciu karty daje region ujemny semantycznie, ale geometrycznie nadal jest maską różnicy.
- Jeden fizyczny obiekt może zostać podzielony na kilka komponentów, jeśli maska diff ma dziury.
- Kilka blisko położonych kart może zostać złączonych przez morfologię albo przez odbicia na macie.

## Research Questions

### 1. How to make stable object region from change regions?

Najbardziej praktyczny kierunek to kaskada:

```text
stage1_mask -> morphology cleanup -> connected components/contours -> merge/split -> bbox tightening -> shape filters
```

Techniki warte testu:

- connected components jako mierzalny baseline regionów,
- contours `RETR_EXTERNAL` dla zewnętrznego obrysu maski,
- morphology open/close do usunięcia szumu i zamknięcia dziur,
- dilation/erosion jako kontrolowany merge/split,
- bbox merge/split na podstawie dystansu, overlapu i proporcji,
- convex hull jako stabilizacja poszarpanego obrysu,
- region growing tylko jako `TEST_LATER`, bo wymaga dodatkowej kontroli seedów,
- watershed i distance transform jako `TEST_LATER`, sensowne głównie przy sklejonych kartach, ale ryzykowne przy szumnej masce i droższe debugowo.

### 2. How distinguish card from reflection/background?

Stage 2 powinien filtrować kandydatów przez zestaw tanich cech geometryczno-obrazowych:

- area ratio względem kadru,
- bbox aspect ratio z tolerancją dla perspektywy i rotacji,
- foreground fill ratio w bboxie,
- edge density w regionie,
- border evidence na krawędziach bboxa,
- texture density wewnątrz regionu,
- mask compactness,
- rectangularity,
- solidity,
- extent.

Refleks zwykle ma nieregularny kształt, niski rectangularity/solidity albo słabe border evidence. Tło zwykle daje mały area ratio, niski foreground fill ratio albo brak spójnych krawędzi prostokąta.

### 3. How handle oversized bbox?

Oversized bbox powinien być korygowany po maskach, nie przez stałe przycinanie:

- mask-based bbox tightening do pikseli foreground,
- contour bbox zamiast bboxa całego regionu Stage 1,
- największy kontur wewnątrz regionu,
- foreground-only bounding box po lokalnym thresholdzie w regionie,
- edge-supported bbox refinement,
- projection profiles X/Y do obcięcia pustych marginesów,
- local threshold refinement inside Stage 1 region.

Stały padding może być użyty tylko jako ochrona przed zbyt agresywnym tighteniem, nie jako finalna geometria.

### 4. How handle split card?

Split card powinien być scalany warunkowo:

- merge komponentów po dystansie bboxów,
- merge po overlapie po krótkiej dylatacji,
- sprawdzenie pionowego/poziomego alignmentu,
- ocena combined aspect ratio po scaleniu,
- oczekiwany rozmiar karty względem fixture,
- zachowanie limitu liczby kart z pary testowej.

Scalanie musi być konserwatywne, bo w `empty -> three_cards` i `one_card -> three_cards` bliskie, ale osobne karty mogą wyglądać jak jeden obiekt.

### 5. How prepare Stage 2 for state-first?

Benchmark Stage 2 musi mierzyć pary przejść, nie pojedyncze zdjęcia:

- `empty -> one_card`: jeden nowy kandydat.
- `empty -> three_cards`: trzy nowe kandydaty.
- `one_card -> three_cards`: dwa nowe kandydaty, karta znana pozostaje stabilna.
- `one_card -> empty`: jeden region usunięcia, nie nowy crop rozpoznania.
- `three_cards -> empty`: trzy regiony usunięcia.

Stage 2 powinien raportować osobno `added_candidate_count`, `removed_candidate_count`, `kept_known_count` i `unknown_region_count`, bo to lepiej pasuje do modelu state-first niż zwykłe `region_count`.

## Candidate Techniques Matrix

| method_id | method_name | category | input | output | short_description | expected_strength | expected_weakness | cpu_cost_low_mid_high | dependencies | works_with_state_first_model | risk | recommended_status | benchmark_parameters | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| connected_components_filtered | Connected components with filters | segmentation | stage1_mask | components + bbox | Komponenty 8-connectivity z filtrami area/aspect/fill. | Prosty baseline, łatwy raport CSV. | Dziurawe maski dzielą kartę. | low | OpenCV/NumPy | yes | low | TEST_NOW | min_area_ratio, max_area_ratio, connectivity, fill_ratio_min | Punkt odniesienia dla pozostałych metod. |
| contour_external_bbox | External contour bbox | segmentation | stage1_mask | contour bbox | `findContours(RETR_EXTERNAL)` i bbox konturu zewnętrznego. | Lepsze dla nieregularnych masek niż stats bbox. | Może łączyć obiekty po cienkich mostkach. | low | OpenCV/NumPy | yes | low | TEST_NOW | retrieval_mode, approx_mode, min_contour_area | Szczególnie ważne przy oversized bbox. |
| contour_largest_inside_region | Largest contour inside region | refinement | stage1_region + stage1_mask | refined bbox | W regionie Stage 1 wybiera największy kontur foreground. | Odcina szum i małe refleksy. | Może zgubić fragment karty przy podzielonej masce. | low | OpenCV/NumPy | yes | medium | TEST_NOW | min_area_ratio, local_padding_px, contour_area_ratio_min | Dobry kandydat na tightening. |
| morph_close_then_components | Morph close then components | cleanup + segmentation | stage1_mask | components | Closing zamyka dziury przed connected components. | Stabilizuje split wynikający z dziur w masce. | Może sklejać bliskie karty. | low | OpenCV/NumPy | yes | medium | TEST_NOW | close_kernel, iterations, min_area_ratio | Priorytet dla Stage 2. |
| dilate_then_merge_components | Dilate then merge components | merge | stage1_mask/components | merged components | Krótka dylatacja albo merge bboxów po overlapie. | Łączy fragmenty jednej karty. | Może połączyć osobne karty w trzech kartach. | low | OpenCV/NumPy | yes | medium | TEST_NOW | dilate_kernel, merge_padding_px, max_combined_aspect_error | Testować na `one_card -> three_cards`. |
| bbox_padding_then_tighten_by_mask | Padding then mask tightening | refinement | stage1_region + mask | tightened bbox | Dodaje lokalny margines, potem zawęża bbox do foreground. | Chroni przed ucięciem krawędzi i redukuje oversized bbox. | Zależne od jakości maski. | low | OpenCV/NumPy | yes | low | TEST_NOW | padding_px, min_foreground_px, tighten_axis_threshold | Praktyczny wrapper dla cropów. |
| convex_hull_region | Convex hull region | shape refinement | contour | hull + bbox | Buduje convex hull dla poszarpanego konturu. | Stabilniejszy obrys przy dziurach. | Może zawyżać bbox i pochłaniać refleks. | low | OpenCV/NumPy | yes | medium | TEST_LATER | hull_area_ratio_max, solidity_min | Sensowne jako backup, nie pierwszy benchmark. |
| min_area_rect_on_contour | Min area rect on contour | rotated geometry | contour | rotated rect | Dopasowuje obracany prostokąt do konturu. | Przygotowuje pod karty lekko obrócone. | Na poszarpanej masce może zwrócić niestabilny kąt. | low | OpenCV/NumPy | yes | medium | TEST_LATER | min_area, angle_tolerance, rect_area_ratio | Obecnie fixture są w analysis frame, więc axis-aligned może wystarczyć. |
| foreground_projection_tightening | Foreground projection tightening | refinement | local mask | tightened bbox | Profile sum pikseli foreground po X/Y obcinają puste marginesy. | Bardzo dobre do oversized bboxów. | Wrażliwe na dziury w masce. | low | OpenCV/NumPy | yes | low | TEST_NOW | projection_threshold, min_band_width, padding_px | Mocny kandydat do benchmarku Stage 2. |
| edge_density_filter | Edge density filter | filter | current ROI + candidate bbox | score/pass | Canny/Sobel density w ROI rozróżnia kartę od płaskiego refleksu. | Pomaga odrzucić refleksy bez prostokątnych krawędzi. | Tekstura maty lub karta z bogatą grafiką może zaburzać wynik. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | canny_low, canny_high, density_min, density_max | Filter, nie samodzielna segmentacja. |
| rectangularity_filter | Rectangularity filter | filter | contour/bbox | score/pass | Porównuje area konturu/maski do area bbox/rect. | Dobrze odrzuca nieregularne plamy. | Uszkodzona maska karty może mieć niski wynik. | low | OpenCV/NumPy | yes | low | TEST_NOW | rectangularity_min, bbox_aspect_range | Kluczowy filtr kart. |
| solidity_extent_filter | Solidity and extent filter | filter | contour | score/pass | Solidity = contour_area/hull_area, extent = contour_area/bbox_area. | Prosty filtr refleksów i tła. | Karty częściowo zakryte mogą przejść gorzej. | low | OpenCV/NumPy | yes | low | TEST_NOW | solidity_min, extent_min, extent_max | Powinien być raportowany w CSV. |
| expected_card_size_filter | Expected card size filter | filter | candidate bbox | score/pass | Odrzuca kandydatów poza spodziewanym zakresem rozmiaru. | Stabilizuje false positives i oversized bbox. | Zbyt ciasne progi mogą odrzucić prawdziwą kartę przy zmianie setupu. | low | none | yes | medium | TEST_NOW | min_width_ratio, max_width_ratio, min_height_ratio, max_height_ratio | Używać jako miękkiego score, nie twardej reguły początkowej. |
| local_threshold_refinement | Local threshold refinement inside region | refinement | ROI previous/current | local mask | Ponownie progowuje diff lokalnie w regionie Stage 1. | Może poprawić maskę dla oversized bboxa. | Więcej parametrów i ryzyko overfitu. | low-mid | OpenCV/NumPy | yes | medium | TEST_LATER | local_threshold, adaptive/otsu flag, padding_px | Dobre po baseline Stage 2, nie jako pierwszy zestaw. |
| watershed_split | Watershed split for merged cards | split | mask + distance transform | separated masks | Próbuje rozdzielić sklejone karty. | Przydatne, gdy trzy karty zlewają się w jeden region. | Wrażliwe na markery i kosztowne debugowo. | mid | OpenCV/NumPy | yes | high | TEST_LATER | distance_threshold, marker_min_area, close_kernel | Tylko jeśli `empty -> three_cards` failuje po prostszych merge/split. |
| region_growing_from_edges | Region growing from edge seeds | segmentation | ROI + seeds | grown mask | Rozszerza region od seedów związanych z krawędziami. | Może odzyskać kartę z fragmentarycznej maski. | Trudny dobór seedów, ryzyko zalania tła. | mid | OpenCV/NumPy | partial | high | REQUIRES_APPROVAL | seed_strategy, grow_threshold, max_area_ratio | Zbyt złożone na pierwszy Stage 2 benchmark. |
| learned_segmentation_model | ML segmentation model | segmentation | image ROI | mask | Model ML do segmentacji kart. | Potencjalnie mocny w trudnych warunkach. | Nowe dane, nowe zależności, ryzyko runtime i utrzymania. | high | new deps/model | possible | high | REJECT_FOR_NOW | n/a | Nie pasuje do aktualnej bramki offline CPU-only. |

## Methods Recommended for TEST_NOW

Rekomendowana shortlista do przyszłego `TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001`:

1. `connected_components_filtered`
2. `morph_close_then_components`
3. `dilate_then_merge_components`
4. `bbox_padding_then_tighten_by_mask`
5. `contour_external_bbox`
6. `contour_largest_inside_region`
7. `foreground_projection_tightening`
8. `rectangularity_filter`
9. `solidity_extent_filter`
10. `expected_card_size_filter`
11. `edge_density_filter`

Proponowana kolejność benchmarku:

```text
baseline components
-> morphology/merge variants
-> bbox tightening variants
-> shape/edge/size filters
```

## Methods Recommended for TEST_LATER

- `convex_hull_region`
- `min_area_rect_on_contour`
- `local_threshold_refinement`
- `watershed_split`
- distance transform as support for watershed/split
- region growing only after simpler methods fail

Powód: te metody mogą pomóc, ale zwiększają liczbę parametrów i trudność interpretacji debug overlay.

## Methods Rejected for Now

- ML segmentation model.
- Nowe biblioteki poza OpenCV/NumPy.
- Pełne edge-first segmentation jako główna metoda Stage 2.

Powód: aktualna strategia wymaga małego, debugowalnego, CPU-only benchmarku na zatwierdzonych fixture.

## Methods Requiring Approval

- `region_growing_from_edges`, jeśli miałby być czymś więcej niż eksperymentem diagnostycznym.
- ML / learned segmentation.
- Dodanie zależności poza aktualnym stackiem.
- Zmiana scope z offline labu na runtime.

## Proposed Stage 2 Benchmark

### Input

Użyć outputu Stage 1 dla zatwierdzonej metody:

```text
gray_absdiff_gaussian
```

oraz par fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

### Output

```text
logs/offline_replay/stage2_region/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/stage1_mask.png
  <method>/<pair>/candidate_mask.png
  <method>/<pair>/candidate_overlay.png
  <method>/<pair>/tightened_overlay.png
```

### Required Metrics

- `candidate_count`
- `expected_candidate_count`
- `candidate_count_delta`
- `added_candidate_count`
- `removed_candidate_count`
- `kept_known_count`
- `unknown_region_count`
- `bbox_area_ratio`
- `mask_area_ratio`
- `foreground_fill_ratio`
- `rectangularity`
- `solidity`
- `extent`
- `edge_density`
- `aspect_ratio`
- `oversized_bbox_flag`
- `split_card_flag`
- `merge_card_flag`
- `runtime_ms`
- `verdict`

### Verdict Criteria

Minimalne kryteria `PASS`:

- `empty -> empty`: zero kandydatów.
- `empty -> one_card`: jeden kandydat, bez oversized bbox.
- `empty -> three_cards`: trzy kandydaty albo jawnie oznaczony split/merge do manual review.
- `one_card -> three_cards`: dwa nowe kandydaty i brak destabilizacji znanej karty.
- `one_card -> empty`: jeden region usunięcia, bez traktowania go jako nowy crop.
- `three_cards -> empty`: trzy regiony usunięcia.

### Debug Review

Supervisor powinien oceniać overlaye co najmniej dla:

- candidate bbox,
- tightened bbox,
- mask foreground,
- odrzuconych kandydatów z powodem odrzucenia.

## Recommended Next Action

Nie implementować jeszcze Stage 2.

Najpierw Supervisor musi zaakceptować shortlistę `TEST_NOW`. Po akceptacji utworzyć osobny task:

```text
TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001
```

Ten przyszły task powinien implementować tylko izolowany benchmark offline w `tools/cv_detection_lab/`, bez zmian runtime.

## Sources

- OpenCV connected components, contours, convex hull, minAreaRect: https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
- OpenCV morphological transformations: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
- OpenCV watershed and distance transform tutorial: https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html
- OpenCV Canny edge detection: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html
- OpenCV contour features: https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html
