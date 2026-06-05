# Research Report — Stage 4 Crop / Deskew / Normalize

## Goal

Stage 4 ma zbadac, jak z wyniku Stage 3 uzyskac stabilny obraz karty:

```text
Stage 3 geometry -> raw_card_crop / deskewed_card_crop / normalized_card_crop
```

Ten etap nie waliduje jeszcze jakosci cropa jako osobnego gate, nie identyfikuje kart i nie dotyka runtime. Jego celem jest przygotowanie materialu i metryk dla przyszlego Stage 5 Crop Quality Validation oraz Stage 6 Card Identification.

## Inputs from Approved Stages

Zatwierdzony pipeline:

```text
Stage 1: gray_absdiff_gaussian
previous_snapshot + current_snapshot -> difference mask

Stage 2: contour_external
difference mask -> candidate object/card regions

Stage 3: hybrid_edge_plus_contour
candidate region -> bbox / rotated_bbox / quad_points / ordered_quad_points / geometry_confidence
```

Wejscie przyszlego Stage 4:

```text
previous_snapshot
current_snapshot
stage1_mask
stage2_candidate_regions
stage3_geometries
ordered_quad_points / rotated_bbox / bbox
change_type: added / removed / no_change
```

Regula state-first:

- dla `added` crop wykonywac z `current_snapshot`,
- dla `removed` crop wykonywac z `previous_snapshot`,
- dla `no_change` oczekiwac zera cropow.

## Known Stage 3 Limitations

- Stage 3 zatwierdza geometrie, ale nie zatwierdza jeszcze gotowego cropa identyfikacyjnego.
- `ordered_quad_points` moga byc poprawne wizualnie jako obrys, ale Stage 4 musi sprawdzic, czy transformacja nie ucina karty.
- `rotated_bbox` jest stabilny dla lekkiej rotacji, ale moze zawierac tlo lub refleks.
- `bbox` jest szybkim fallbackiem, ale moze zawierac za duzo maty.
- Stage 3 nie mierzy jeszcze jakosci finalnego obrazu: ostrosci, kontrastu, widocznosci borderow, rozdzielczosci po transformacji ani efektu normalizacji.

## Research Questions

### 1. Jak najlepiej wykonac crop z geometrii Stage 3?

Najbardziej wartosciowy baseline to porownanie trzech klas wejsc:

- axis-aligned `bbox` crop,
- `rotated_bbox` z rotacja affine,
- `ordered_quad_points` z perspective transform.

`bbox` jest najprostszy i powinien pozostac fallbackiem diagnostycznym. Nie wymaga transformacji, ale przy obroconych kartach zawiera tlo i moze pogarszac identyfikacje.

`rotated_bbox` nadaje sie do stabilnego deskew przez `cv2.getRotationMatrix2D` + `cv2.warpAffine`, gdy karta jest prawie prostokatna i nie wymaga korekcji perspektywy. Ryzykiem jest obciecie rogów po rotacji, jezeli przed transformacja nie powiekszymy canvasu albo nie dodamy paddingu.

`ordered_quad_points` jest preferowanym wejsciem do `cv2.getPerspectiveTransform` + `cv2.warpPerspective`, bo daje bezposredni mapping czterech naroznikow do docelowego prostokata. Warunek krytyczny: kolejnosc punktow musi pozostac stabilna jako `top_left, top_right, bottom_right, bottom_left`.

Przed transformacja nalezy:

- walidowac liczbe i kolejnosc punktow,
- clampowac punkty do granic klatki,
- opcjonalnie rozszerzac quad o safe padding,
- zdefiniowac target size i aspect ratio,
- ustawic border handling tak, aby brakujace piksele nie tworzyly agresywnych czarnych ramek.

### 2. Kiedy uzywac bbox, rotated_bbox, a kiedy quad?

Rekomendowana hierarchia:

1. `ordered_quad_points`: preferowane wejscie do perspective transform, jezeli `geometry_confidence` jest wystarczajace, punkty sa kompletne i aspect ratio jest sensowne.
2. `rotated_bbox`: fallback dla lekkiej rotacji, gdy quad jest niestabilny albo pochodzi z `minAreaRect`.
3. `bbox`: fallback baseline i tryb awaryjny, gdy brak pewnego quada/rotated bbox.

Ryzyka:

- `bbox` moze zawierac za duzo tla, szczegolnie przy skosie.
- `rotated_bbox` moze objac refleks albo grafike, jezeli Stage 3 geometry bazowala na krawedziach wewnetrznych.
- `quad` moze zdeformowac crop, jezeli jeden naroznik jest bledny albo kolejnosc punktow jest niestabilna.

Benchmark musi raportowac, z ktorego zrodla geometrii korzysta kazdy crop.

### 3. Jaki target size i aspect ratio przyjac?

Karty tarota w tym labie powinny uzywac stalego target aspect ratio:

```text
height / width ~= 1.65
```

Proponowany rozmiar glowny do benchmarku:

```text
target_width: 300
target_height: 495
```

Uzasadnienie:

- 300x495 zachowuje aspect ratio 1.65.
- Jest wyraznie wiekszy niz miniaturowy crop, wiec zachowuje cechy dla pozniejszego ORB / feature matching / identyfikacji.
- Jest mniejszy niz 400x660, wiec koszt CPU i IO pozostaje rozsadny na HP EliteBook 830 G6.
- 256x422 jest szybkie, ale moze byc zbyt ubogie dla subtelnych detali kart.
- 360x594 i 400x660 warto oznaczyc jako `TEST_LATER` albo parametry stress-testu, nie jako pierwszy wariant.

Benchmark powinien zapisac `target_width`, `target_height`, `crop_width`, `crop_height`, `crop_aspect_ratio` i `aspect_ratio_error`.

### 4. Jak obsluzyc safe padding?

Safe padding powinien byc jawnie testowany, nie ukryty w transformacji.

Rekomendowane warianty:

- `padding_ratio=0.00` jako baseline,
- `padding_ratio=0.03` jako pierwszy wariant bezpieczny,
- `padding_ratio=0.05` jako wariant ochronny,
- opcjonalnie `padding_ratio=0.08` tylko do stress-testu.

Padding procentowy jest lepszy niz staly pikselowy, bo skaluje sie z rozmiarem karty. Dla bardzo malych cropow mozna dodac minimalny limit, np. 4-8 px, ale benchmark powinien raportowac faktyczny `padding_ratio`.

Padding powinien rozszerzac quad wzgledem jego srodka albo rozszerzac bbox/rotated rect przed transformacja. Po transformacji padding moze pozostac w cropie debugowym, ale przyszly Stage 5 musi ocenic, czy border i mata nie pogarszaja identyfikacji.

Ryzyko:

- za maly padding ucina krawedzie karty,
- za duzy padding wprowadza mate, markerowe tlo albo cien.

### 5. Jak wykonywac deskew / perspective normalization?

Preferowana metoda dla quada:

```text
src = ordered_quad_points
dst = [[0,0], [W-1,0], [W-1,H-1], [0,H-1]]
M = cv2.getPerspectiveTransform(src, dst)
crop = cv2.warpPerspective(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
```

`warpPerspective` jest naturalnym wyborem dla czworokatow i korekcji perspektywy. Dla `rotated_bbox` fallbackiem jest:

```text
M = cv2.getRotationMatrix2D(center, angle, 1.0)
rotated = cv2.warpAffine(...)
crop = axis-aligned crop from rotated frame
```

Interpolacja:

- `INTER_LINEAR`: domyslny `TEST_NOW`, dobry kompromis jakosc/koszt.
- `INTER_CUBIC`: `TEST_LATER`, potencjalnie lepszy obraz, drozszy CPU.
- `INTER_AREA`: sensowny przy downscale, ale nie zawsze najlepszy do perspektywy.

Border handling:

- `BORDER_REPLICATE`: preferowany baseline, bo unika czarnych ramek.
- `BORDER_CONSTANT`: przydatny diagnostycznie, ale czarna ramka moze zaburzac metryki i identyfikacje.

Normalizacja orientacji:

- crop finalny powinien byc portrait,
- jezeli transformacja daje width > height, obrocic wynik o 90 stopni i zapisac `orientation_normalized=true`,
- nie wykonywac identyfikacji kierunku karty w Stage 4.

### 6. Jak normalizowac obraz cropa?

Stage 4 powinien testowac normalizacje jako warianty, a nie jako jedna ukryta operacje.

Warianty:

- brak normalizacji jako baseline,
- resize only,
- grayscale conversion,
- CLAHE na kanale grayscale albo luminance,
- brightness/contrast normalization,
- gamma correction,
- white balance / gray world,
- denoise median/bilateral,
- unsharp mask / sharpening.

Rekomendacja pierwszego benchmarku:

- zachowac kolorowy crop `raw` i `deskewed`,
- generowac `normalized` jako wariant metody,
- nie laczyc zbyt wielu ulepszen naraz, bo trudno potem ocenic, co pomaga albo szkodzi.

Najwieksze ryzyko: normalizacja moze "upiększyc" obraz, ale usunac lokalne cechy tekstury, ramek i kontrastu potrzebne do pozniejszej identyfikacji. Dlatego baseline `resize_only_normalization` musi pozostac w `TEST_NOW`.

### 7. Jak mierzyc jakosc crop/deskew?

Stage 4 powinien raportowac metryki techniczne, ale nie podejmowac finalnej decyzji Stage 5.

Minimum:

```text
crop_width
crop_height
crop_aspect_ratio
aspect_ratio_error
crop_area_ratio
source_quad_area
target_size
padding_ratio
transform_valid
transform_matrix_condition_estimate
edge_cut_risk
border_visible_score
foreground_fill_ratio
blur_score
contrast_score
brightness_mean
normalized_contrast_score
runtime_ms
```

Metryki pomocnicze:

- `edge_cut_risk`: krawedzie karty bardzo blisko granicy cropa albo brak widocznego borderu po jednej stronie.
- `border_visible_score`: liczba/gestosc krawedzi w pasmach przy krawedziach cropa.
- `foreground_fill_ratio`: ile cropa zajmuje karta vs tlo.
- `blur_score`: wariancja Laplacianu.
- `contrast_score`: odchylenie standardowe luminance.
- `brightness_mean`: srednia luminance.
- `transform_matrix_condition_estimate`: przyblizona kondycja macierzy 3x3 lub sanity check determinanty podmacierzy.

### 8. Jak zachowac model state-first?

Stage 4 benchmark musi utrzymac te same pary:

- `empty_to_empty`
- `empty_to_one_card`
- `empty_to_three_cards`
- `one_card_to_three_cards`
- `one_card_to_empty`
- `three_cards_to_empty`

Warunek krytyczny:

- `added` -> crop z `current_snapshot`,
- `removed` -> crop z `previous_snapshot`,
- `one_card_to_three_cards` -> crop tylko dla nowych kart, bez destabilizacji znanej karty srodkowej.

W matrix nalezy zapisac `crop_source_frame`, analogicznie do `geometry_source_frame` w Stage 3.

## Candidate Techniques Matrix

| method_id | method_name | category | input | output | short_description | expected_strength | expected_weakness | cpu_cost_low_mid_high | dependencies | works_with_state_first_model | risk | recommended_status | benchmark_parameters | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bbox_crop_resize | Axis-aligned bbox crop + resize | crop baseline | `bbox`, source frame | raw crop resized to target | Wycina axis-aligned bbox i skaluje do targetu. | Najszybszy baseline, prosty fallback, dobry sanity check. | Za duzo tla przy rotacji, brak deskew. | low | OpenCV/NumPy | yes | low | TEST_NOW | target_size, clamp, border_mode | Baseline obowiazkowy. |
| rotated_rect_warp_affine | Rotated rect affine deskew | deskew fallback | `rotated_bbox`, source frame | deskewed crop | Obraca obraz wokol srodka prostokata i wycina karte. | Stabilny dla lekkiej rotacji, tanszy niz perspective. | Moze obciac rogi bez paddingu/canvas expansion. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | angle, padding_ratio, interpolation, border_mode | Fallback dla slabych quadow. |
| quad_warp_perspective | Quad perspective crop | perspective crop | `ordered_quad_points`, source frame | deskewed crop | Mapuje cztery punkty do docelowego prostokata. | Najlepsze dopasowanie geometrii Stage 3. | Bledny naroznik deformuje crop. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | target_size, interpolation, border_mode | Glowny kandydat Stage 4. |
| quad_warp_perspective_with_safe_padding | Quad perspective crop + safe padding | perspective crop | `ordered_quad_points`, source frame | padded deskewed crop | Rozszerza quad przed transformacja. | Chroni przed ucieciem krawedzi. | Nadmierny padding wprowadza mate. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | padding_ratio 0.03/0.05, target_size | Kluczowy wariant benchmarku. |
| quad_warp_perspective_fixed_aspect | Quad perspective fixed aspect | aspect normalization | `ordered_quad_points` | fixed aspect crop | Wymusza docelowe 300x495 albo warianty. | Spójne wejście dla Stage 5/6. | Moze lekko rozciagnac obraz przy blednej geometrii. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | target_width, target_height, aspect_ratio=1.65 | Testowac z tym samym targetem dla metod. |
| quad_warp_perspective_keep_border_margin | Quad perspective with retained border | crop policy | padded quad | crop with visible card border | Zachowuje minimalny margines borderu karty. | Pomaga Stage 5 wykrywac obciecie. | Moze dodac tlo i pogorszyc identyfikacje. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | border_margin_ratio, padding_ratio | Wazne dla edge_cut_risk. |
| resize_only_normalization | Resize only | normalization baseline | crop | normalized crop | Tylko resize do target size bez zmiany kolorow. | Neutralny baseline dla identyfikacji. | Nie kompensuje swiatla. | low | OpenCV/NumPy | yes | low | TEST_NOW | target_size, interpolation | Obowiazkowy baseline. |
| grayscale_normalization | Grayscale crop | normalization | crop | grayscale crop | Konwersja do grayscale. | Dobre pod ORB/edge metrics, tanie CPU. | Traci informacje koloru talii. | low | OpenCV/NumPy | yes | low-medium | TEST_NOW | color_conversion | Testowac jako wariant metryk i przyszlej identyfikacji. |
| clahe_normalization | CLAHE luminance normalization | normalization | crop | contrast-normalized crop | Lokalnie wzmacnia kontrast luminance. | Pomaga przy nierownym oswietleniu. | Moze uwypuklic szum i artefakty druku. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | clipLimit, tileGridSize | Testowac ostroznie, nie jako domyslne. |
| brightness_contrast_normalization | Linear brightness/contrast normalization | normalization | crop | adjusted crop | Skaluje srednia i kontrast luminance. | Proste, szybkie, debugowalne. | Moze przepalic jasne partie. | low | OpenCV/NumPy | yes | medium | TEST_NOW | alpha, beta, percentile_clip | Dobry wariant kontrolowany. |
| gamma_correction | Gamma correction | normalization | crop | gamma-adjusted crop | Koryguje jasnosc nieliniowo. | Pomaga przy niedoswietleniu/przeswietleniu. | Zle gamma zmienia cechy lokalne. | low | OpenCV/NumPy | yes | medium | TEST_LATER | gamma 0.8/1.2 | Lepsze po bazowym benchmarku. |
| white_balance_gray_world | Gray-world white balance | color normalization | color crop | color-balanced crop | Normalizuje balans kanalow. | Moze poprawic stale zafarby. | Ryzyko zmiany kolorystycznych cech talii. | low | OpenCV/NumPy | yes | medium | TEST_LATER | channel gains, clipping | Odlozyc do testow identyfikacji. |
| denoise_bilateral_or_median | Median/bilateral denoise | denoise | crop | denoised crop | Redukuje szum przed metrykami. | Median tani, bilateral zachowuje krawedzie. | Moze rozmyc drobne cechy kart, bilateral drozszy. | low-mid | OpenCV/NumPy | yes | medium | TEST_LATER | median_ksize, bilateral_d, sigma | Nie laczyc w pierwszym benchmarku. |
| unsharp_mask_sharpening | Unsharp mask sharpening | sharpening | crop | sharpened crop | Wzmacnia krawedzie po resize. | Moze poprawic cechy ORB. | Moze wzmacniac szum i artefakty. | low-mid | OpenCV/NumPy | yes | medium | TEST_LATER | blur_sigma, amount | Testowac dopiero po baseline. |
| orientation_portrait_normalization | Portrait orientation normalization | orientation | crop dimensions / transform metadata | portrait crop | Wymusza height > width po transformacji. | Zapewnia spójne wejście Stage 5/6. | Nie rozstrzyga karty odwróconej o 180 stopni. | low | OpenCV/NumPy | yes | low | TEST_NOW | portrait_required=true | Nie robi identyfikacji orientacji znaczeniowej. |
| adaptive_padding_by_confidence | Confidence-based safe padding | crop policy | geometry_confidence + quad/bbox | padded crop | Zwieksza padding przy nizszej pewnosci geometrii. | Chroni slabe geometrie przed ucieciem. | Moze ukrywac problemy Stage 3 i dodawac tlo. | low | OpenCV/NumPy | yes | medium | TEST_LATER | confidence_thresholds, padding_lut | Sensowne po pomiarze baseline paddingu. |
| super_resolution_or_ml_normalizer | ML normalizer / super-resolution | learned normalization | crop | enhanced crop | Potencjalnie poprawia detale. | Nowe zaleznosci, trening, koszt CPU/GPU, ryzyko halucynacji cech. | high | new model/deps | possible | high | REQUIRES_APPROVAL | model, runtime_budget | Nie pasuje do aktualnego offline gate. |
| template_guided_crop_refinement | Template/ORB-guided crop refinement | recognition-assisted crop | crop + templates | refined crop | Uzywa wzorcow kart do poprawy cropa. | Moze poprawic finalna identyfikacje. | Miesza Stage 4 ze Stage 6. | mid-high | OpenCV ORB + templates | partial | high | REJECT_FOR_NOW | n/a | Narusza separacje etapow. |

## Methods Recommended for TEST_NOW

Recommended `TEST_NOW` shortlist:

1. `bbox_crop_resize`
2. `rotated_rect_warp_affine`
3. `quad_warp_perspective`
4. `quad_warp_perspective_with_safe_padding`
5. `quad_warp_perspective_fixed_aspect`
6. `quad_warp_perspective_keep_border_margin`
7. `resize_only_normalization`
8. `grayscale_normalization`
9. `clahe_normalization`
10. `brightness_contrast_normalization`
11. `orientation_portrait_normalization`

Uzasadnienie: ta shortlista pokrywa baseline, fallback affine, preferowany perspective crop, bezpieczny padding, staly aspect ratio i minimalne warianty normalizacji. Wszystkie metody sa CPU-only, debugowalne i mieszczą się w OpenCV/NumPy.

## Methods Recommended for TEST_LATER

- `gamma_correction`
- `white_balance_gray_world`
- `denoise_bilateral_or_median`
- `unsharp_mask_sharpening`
- `adaptive_padding_by_confidence`

Uzasadnienie: te metody moga byc pomocne, ale latwo zmieniaja cechy obrazu albo dokladaja parametry. Najpierw trzeba ustalic, czy sam crop/deskew jest stabilny.

## Methods Rejected for Now

- `template_guided_crop_refinement`
- metody wymagajace identyfikacji karty przed cropem,
- metody laczace Stage 4 z ORB/FLANN decision logic.

Uzasadnienie: naruszaja separacje Stage 4 i Stage 6.

## Methods Requiring Approval

- `super_resolution_or_ml_normalizer`
- nowe modele ML,
- nowe zaleznosci poza OpenCV/NumPy,
- zmiany runtime albo integracja ze Studio.

## Proposed Stage 4 Benchmark

Nastepny task:

```text
TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001
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
```

Pary:

```text
empty_to_empty
empty_to_one_card
empty_to_three_cards
one_card_to_three_cards
one_card_to_empty
three_cards_to_empty
```

Proponowane metryki:

```text
method
pair
change_type
crop_source_frame
geometry_count
crop_count
expected_crop_count
crop_count_delta
target_width
target_height
crop_width_avg
crop_height_avg
crop_aspect_ratio_avg
aspect_ratio_error_avg
padding_ratio
border_visible_score_avg
edge_cut_risk_count
foreground_fill_ratio_avg
brightness_mean_avg
contrast_score_avg
blur_score_avg
normalization_variant
runtime_ms
reject_count
reject_reasons
verdict
verdict_basis
```

Output debug:

```text
logs/offline_replay/stage4_crop_deskew_normalize/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/stage3_geometry_overlay.png
  <method>/<pair>/crop_debug_sheet.png
  <method>/<pair>/crop_01_raw.png
  <method>/<pair>/crop_01_deskewed.png
  <method>/<pair>/crop_01_normalized.png
  <method>/<pair>/crop_debug.json
```

Werdykt benchmarku powinien byc `PROVISIONAL_RECOMMENDED` i wymagac manual review crop sheets przed zatwierdzeniem Stage 4.

## Recommended Next Action

Nie implementowac jeszcze Stage 4 benchmarku.

Supervisor powinien zaakceptowac albo skorygowac shortlistę `TEST_NOW`. Po akceptacji utworzyc:

```text
TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001
```

Benchmark powinien pozostac izolowany w `tools/cv_detection_lab/`, bez zmian runtime.

## Sources

- OpenCV geometric transforms, including `getPerspectiveTransform`, `warpPerspective`, `getRotationMatrix2D` and `warpAffine`: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html
- OpenCV affine transformations tutorial: https://docs.opencv.org/4.x/d4/d61/tutorial_warp_affine.html
- OpenCV image filtering functions, including Gaussian, median and bilateral filters: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html
- OpenCV histogram equalization tutorial and CLAHE usage: https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html
