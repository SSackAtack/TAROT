# Research Report — Stage 5 Crop Quality Validation

## Goal

Stage 5 ma ocenic, czy crop z Stage 4 jest jakosciowo gotowy do przyszlej identyfikacji karty.

Ten etap nie rozpoznaje, jaka karta znajduje sie na cropie. Nie uzywa ORB, FLANN, template matching, OCR ani bazy wzorcow. Wynikiem Stage 5 ma byc tylko decyzja jakosciowa:

```text
crop nadaje sie / wymaga uwagi / nie nadaje sie do identyfikacji
```

## Inputs from Approved Stages

Zatwierdzony pipeline wejscia:

```text
Stage 1: gray_absdiff_gaussian
previous_snapshot + current_snapshot -> difference mask

Stage 2: contour_external
difference mask -> candidate card regions

Stage 3: hybrid_edge_plus_contour
candidate region -> card geometry

Stage 4: quad_warp_perspective_fixed_aspect__resize_only_normalization
card geometry -> raw_crop / deskewed_crop / normalized_crop
```

Wejscie przyszlego Stage 5:

```text
raw_crop
deskewed_crop
normalized_crop
crop_metadata
crop_transform_matrix
change_type: added / removed / no_change
crop_source_frame: current / previous
```

Regula state-first:

- `added` -> oceniac crop z `current_snapshot`,
- `removed` -> oceniac crop z `previous_snapshot`,
- `no_change` / `empty_to_empty` -> oczekiwac zera cropow i statusu PASS/no-crops.

## Known Stage 4 Limitations

Stage 4 zatwierdza sposob wygenerowania cropa, ale nie zatwierdza automatycznej jakosci cropa.

Znane obszary ryzyka:

- krawedz karty moze byc zbyt blisko granicy cropa,
- crop moze zawierac za duzo maty albo tlo nad karta,
- jasny refleks nad karta moze wygladac jak element obrazu,
- crop moze byc nieostry, zbyt ciemny, zbyt jasny albo o niskim kontrascie,
- crop moze miec dobry geometrycznie obrys, ale malo cech wizualnych potrzebnych do przyszlego Stage 6.

Stage 5 ma mierzyc te problemy liczbowo, a nie poprawiac obraz.

## Research Questions

### 1. Jak wykrywac uciecie karty?

Najbardziej praktyczne metryki to `edge_cut_risk`, `border_visible_score`, `border_continuity_score`, `missing_border_score`, `corner_visibility_score` i `card_edge_proximity_to_crop_edge`.

Proponowana logika:

- analizowac pasy przy krawedziach cropa, np. 3-8% szerokosci/wysokosci;
- liczyc gestosc krawedzi Canny/Sobel w pasach brzegowych;
- szukac ciaglosci borderu osobno dla gornej, dolnej, lewej i prawej strony;
- oceniac, czy silna krawedz karty lezy zbyt blisko granicy cropa;
- oznaczac `EDGE_CUT_RISK`, gdy border jest nieciagly albo krawedz dotyka granicy cropa.

To nie wymaga znajomosci konkretnej karty. Metryki opieraja sie na geometrii cropa, krawedziach i pasach brzegowych.

### 2. Jak mierzyc nadmiar tla / marginesu?

Najwazniejsze metryki to `background_margin_score`, `mat_background_ratio`, `card_fill_ratio`, `foreground_fill_ratio`, `crop_to_card_area_ratio`, `top_margin_ratio`, `bottom_margin_ratio`, `left_margin_ratio` i `right_margin_ratio`.

Praktyczny baseline:

- znalezc przyblizony foreground karty przez krawedzie, gradient i/lub maski jasnosciowe w cropie;
- wyznaczyc tight bbox foregroundu wewnatrz cropa;
- policzyc wypelnienie cropa karta jako `foreground_bbox_area / crop_area`;
- osobno raportowac marginesy z kazdej strony.

`top_margin_ratio` powinien byc osobna metryka pierwszej klasy, bo Stage 4 manual review wskazal jasny fragment/refleks nad karta. Nadmierny top margin nie zawsze jest fail, ale powinien dawac warning `TOO_MUCH_BACKGROUND` albo `TOP_MARGIN_RISK`.

### 3. Jak wykrywac refleksy i przeswietlenia?

Metryki do testu:

- `highlight_ratio`,
- `overexposed_pixel_ratio`,
- `top_reflection_score`,
- `specular_highlight_score`,
- `saturation_clip_ratio`,
- `local_brightness_outlier_score`.

Proponowana separacja przypadkow:

- refleks poza karta: wysoki highlight w obszarze marginesu, szczegolnie nad tight bbox karty;
- refleks na karcie: wysoki highlight wewnatrz foreground/card area;
- jasny element grafiki karty: lokalny highlight bez duzego clip ratio i z zachowanymi krawedziami/tekstura wokol.

Stage 5 nie musi rozwiazac tego idealnie. W pierwszym benchmarku powinien raportowac osobno `top_reflection_score`, `overexposed_pixel_ratio` i polozenie highlightu wzgledem szacowanego obszaru karty.

### 4. Jak mierzyc ostrosc?

Metody CPU-only warte testu:

- `variance_of_laplacian`,
- `tenengrad_score`,
- `sobel_energy`,
- `edge_density_score`,
- `motion_blur_risk`.

`variance_of_laplacian` jest najprostsza i szybka, ale bywa wrazliwa na szum i grafike karty. `tenengrad_score` jest stabilniejszy jako energia gradientu Sobela. `edge_density_score` pomaga wykryc cropy z bardzo mala iloscia cech, ale moze mylic gladkie partie grafiki z rozmyciem. Pierwszy benchmark powinien testowac Laplacian + Tenengrad + edge density jako wspolny obraz ostrosci.

### 5. Jak mierzyc kontrast i jasnosc?

Metryki:

- `brightness_mean`,
- `brightness_std`,
- `contrast_score`,
- `histogram_spread`,
- `dynamic_range_score`,
- `underexposed_ratio`,
- `overexposed_ratio`.

Rekomendacja:

- liczyc luminance/grayscale na `normalized_crop`,
- raportowac srednia, odchylenie standardowe i percentyle, np. P2/P98,
- traktowac bardzo wysokie `overexposed_ratio` i bardzo niskie `underexposed_ratio` jako flagi, nie jako automatyczne progi finalne,
- nie poprawiac obrazu w Stage 5.

### 6. Jak mierzyc kompletnosc i czytelnosc karty?

Metryki:

- `card_fill_ratio`,
- `border_visible_score`,
- `corner_visibility_score`,
- `crop_completeness_score`,
- `texture_density_score`,
- `internal_detail_score`.

`crop_completeness_score` powinien laczyc sygnaly geometryczne i wizualne: widocznosc borderow, widocznosc naroznikow, wypelnienie cropa karta oraz brak nadmiernego tla. `texture_density_score` i `internal_detail_score` mierza tylko obecnosc cech wizualnych, nie zgodnosc z konkretna karta.

### 7. Jak zbudowac jeden wynik jakosci?

Proponowane wyjscia:

```text
crop_quality_status: PASS / YELLOW / FAIL
crop_quality_score: 0.0-1.0
identification_readiness_score: 0.0-1.0
reject_reason
warning_reason
quality_flags[]
quality_metrics{}
```

Proponowane flagi:

```text
EDGE_CUT_RISK
TOO_MUCH_BACKGROUND
TOP_REFLECTION_RISK
LOW_CONTRAST
TOO_DARK
TOO_BRIGHT
BLURRY
LOW_DETAIL
BAD_ASPECT
UNEXPECTED_SIZE
```

`crop_quality_score` powinien mocno karac uciecie krawedzi, zly aspect ratio i brak borderow. `identification_readiness_score` powinien mocniej uwzgledniac ostrosc, kontrast, teksture i brak przeswietlen. Te dwa wyniki sa bliskie, ale nie identyczne.

### 8. Jak ustalic progi?

Nie nalezy wybierac finalnych progow runtime w researchu.

Proponowane podejscie:

- zaczac od heurystycznych pasm PASS/YELLOW/FAIL dla kazdej metryki;
- policzyc statystyki na zatwierdzonych fixture;
- porownac wyniki z manual review crop sheets;
- oznaczyc progi jako benchmark-only;
- dopiero po Stage 5 benchmarku zdecydowac, ktore progi wejda do kolejnego etapu.

To ogranicza ryzyko przestrojenia na malej liczbie obrazow.

### 9. Jak zachowac model state-first?

Benchmark Stage 5 musi pracowac na tych samych parach:

```text
empty_to_empty
empty_to_one_card
empty_to_three_cards
one_card_to_three_cards
one_card_to_empty
three_cards_to_empty
```

Dla `added` jakosc cropow oceniamy z `current_snapshot`. Dla `removed` jakosc cropow oceniamy z `previous_snapshot`. `empty_to_empty` powinno dac `crop_count=0`, `quality_pass_count=0`, `quality_fail_count=0` i verdict PASS/no-crops.

Najwazniejsza para to `one_card_to_three_cards`, bo sprawdza, czy system ocenia jakosc nowych cropow bez destabilizacji znanej juz karty.

### 10. Jak nie pomieszac Stage 5 ze Stage 6?

Granica jest obowiazkowa:

- Stage 5 nie rozpoznaje, jaka to karta.
- Stage 5 nie ocenia zgodnosci cropa z baza kart.
- Stage 5 nie uzywa ORB/FLANN/template matching.
- Stage 5 tylko mowi, czy crop nadaje sie jakosciowo do pozniejszej identyfikacji.

Metody wykorzystujace wzorce kart, embeddingi, klasyfikatory lub dopasowanie cech nalezy oznaczyc jako `REJECT_FOR_NOW` albo `REQUIRES_APPROVAL`, bo naleza do Stage 6 lub pozniejszej integracji.

## Candidate Techniques Matrix

| method_id | method_name | category | input | output | short_description | expected_strength | expected_weakness | cpu_cost_low_mid_high | dependencies | works_with_state_first_model | risk | recommended_status | benchmark_parameters | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| edge_cut_risk_score | Edge cut risk score | edge/crop completeness | normalized_crop, crop_metadata | risk score + flag | Mierzy, czy krawedzie karty leza zbyt blisko granicy cropa albo znikaja w pasach brzegowych. | Bezposrednio odpowiada na ryzyko ucietej karty. | Wymaga stabilnego wykrycia krawedzi na roznych grafikach. | low | OpenCV/NumPy | yes | medium | TEST_NOW | edge_band_ratio, canny thresholds, proximity_px | Kluczowy gate jakosci. |
| border_visible_score | Border visible score | border quality | normalized_crop | score per side + avg | Liczy widocznosc krawedzi/borderu w pasach przy brzegach. | Latwy debug overlay, dobrze wykrywa brak borderu. | Talie bez wyraznej ramki moga miec nizszy wynik. | low | OpenCV/NumPy | yes | medium | TEST_NOW | band_ratio, gradient threshold | Raportowac per side. |
| border_continuity_score | Border continuity score | border quality | normalized_crop | continuity score | Mierzy ciaglosc linii borderu po czterech stronach. | Lepiej wykrywa przerwane/uciete krawedzie niz sama gestosc. | Trudniejszy do stabilnego progowania. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | hough/canny optional, min_line_coverage | Testowac jako ostrzezenie, nie twardy fail. |
| corner_visibility_score | Corner visibility score | border/corner quality | normalized_crop | score + visible_corner_count | Szuka cech naroznikow w czterech rogach cropa. | Dobre dla kompletności karty. | Zaokraglone albo jasne rogi moga byc trudne. | low | OpenCV/NumPy | yes | medium | TEST_NOW | corner_patch_ratio, gradient thresholds | Nie uzywac jako jedynego kryterium. |
| missing_border_score | Missing border score | border quality | normalized_crop | missing-side count | Wykrywa strony bez widocznego borderu. | Prosty sygnal FAIL/YELLOW. | Moze mylic border z tlem przy jasnej macie. | low | OpenCV/NumPy | yes | medium | TEST_NOW | min_side_score, side_weights | Pochodna border_visible/continuity. |
| card_edge_proximity_to_crop_edge | Card edge proximity | edge/crop completeness | normalized_crop | min distance metrics | Estymuje minimalny dystans krawedzi karty do granicy cropa. | Bezposredni sygnal uciecia lub za malego paddingu. | Wymaga estymacji krawedzi karty w cropie. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | min_margin_px, min_margin_ratio | Wazne przy top/bottom margin. |
| card_fill_ratio_score | Card fill ratio score | margin/fill | normalized_crop | fill ratio + score | Mierzy, jaka czesc cropa zajmuje szacowany obszar karty. | Wykrywa za duzo tla i za maly crop. | Foreground moze obejmowac refleks lub cien. | low | OpenCV/NumPy | yes | medium | TEST_NOW | foreground method, target range | Raportowac razem z marginesami. |
| background_margin_score | Background margin score | margin/fill | normalized_crop | score + margin flags | Mierzy nadmiar tła poza karta. | Dobre dla Stage 4 top background issue. | Segmentacja foregroundu moze byc niedokladna. | low | OpenCV/NumPy | yes | medium | TEST_NOW | max_margin_ratio, side weights | Szczegolnie top margin. |
| top_margin_ratio_score | Top margin ratio score | margin/fill | normalized_crop | top margin ratio + flag | Osobno mierzy margines nad karta. | Bezposrednio adresuje jasny fragment/refleks nad karta. | Wymaga ustalenia, gdzie konczy sie karta. | low | OpenCV/NumPy | yes | medium | TEST_NOW | top_band_ratio, warning threshold | Pierwszoplanowa metryka Stage 5. |
| side_margin_ratios | Side margin ratios | margin/fill | normalized_crop | top/bottom/left/right ratios | Raportuje marginesy po kazdej stronie. | Pomaga interpretowac debug sheet. | Nie daje jednej decyzji bez agregacji. | low | OpenCV/NumPy | yes | low | TEST_NOW | foreground bbox method | Zasilenie composite score. |
| overexposed_pixel_ratio | Overexposed pixel ratio | exposure/highlight | normalized_crop | ratio | Liczy piksele bliskie bieli lub saturacji. | Bardzo tanie i debugowalne. | Jasne grafiki kart moga podbijac wynik. | low | OpenCV/NumPy | yes | medium | TEST_NOW | luminance threshold, saturation threshold | Laczyc z lokalizacja highlightu. |
| underexposed_pixel_ratio | Underexposed pixel ratio | exposure | normalized_crop | ratio | Liczy piksele bliskie czerni. | Wykrywa niedoswietlone cropy. | Ciemne talie moga naturalnie miec wysoki udzial czerni. | low | OpenCV/NumPy | yes | medium | TEST_NOW | luminance threshold | Interpretowac z kontrastem. |
| top_reflection_score | Top reflection score | highlight/location | normalized_crop, estimated card bbox | score + flag | Szuka jasnych obszarow w gornym marginesie albo przy gornej krawedzi. | Celuje w znane ryzyko Stage 4. | Moze mylic jasny border lub grafike z refleksem. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | top_band_ratio, local outlier threshold | Osobny debug overlay wymagany. |
| specular_highlight_score | Specular highlight score | highlight | normalized_crop | score | Wykrywa male, bardzo jasne, nisko-teksturalne plamy. | Pomaga odroznic refleks od zwyklej jasnosci. | Trudne przy jasnych ilustracjach kart. | low-mid | OpenCV/NumPy | yes | medium | TEST_LATER | connected highlight components | Najpierw prostszy overexposed/top reflection. |
| local_brightness_outlier_score | Local brightness outlier score | highlight | normalized_crop | score | Porownuje lokalne jasne plamy do otoczenia. | Lepsze niz globalny prog jasnosci. | Wiecej parametrow i ryzyko false positives. | mid | OpenCV/NumPy | yes | medium | TEST_LATER | tile size, percentile delta | Dobre po baseline highlight metrics. |
| brightness_mean_score | Brightness mean score | brightness | normalized_crop | brightness mean + score | Mierzy srednia luminancje i pasma TOO_DARK/TOO_BRIGHT. | Szybkie, stabilne, czytelne. | Sama srednia nie wykrywa lokalnych problemow. | low | OpenCV/NumPy | yes | low | TEST_NOW | pass/yellow/fail bands | Obowiazkowy baseline. |
| contrast_stddev_score | Contrast stddev score | contrast | normalized_crop | stddev + score | Mierzy odchylenie standardowe luminancji. | Tani proxy kontrastu. | Zalezy od grafiki karty. | low | OpenCV/NumPy | yes | low | TEST_NOW | stddev bands | Laczyc z histogram spread. |
| histogram_spread_score | Histogram spread score | contrast/dynamic range | normalized_crop | percentile spread | Mierzy zakres P2-P98 luminancji. | Odporniejsze na pojedyncze przepalenia niz min/max. | Nadal zalezne od talii. | low | OpenCV/NumPy | yes | low | TEST_NOW | low/high percentiles | Dobre do debug report. |
| dynamic_range_score | Dynamic range score | contrast/dynamic range | normalized_crop | score | Ocenia uzyteczny zakres tonalny. | Pomaga przy plaskim, malo czytelnym cropie. | Moze karac celowo pastelowe talie. | low | OpenCV/NumPy | yes | low-medium | TEST_NOW | percentile spread target | Pochodna histogramu. |
| variance_of_laplacian_blur_score | Variance of Laplacian blur score | sharpness | normalized_crop | blur/sharpness score | Klasyczny szybki pomiar ostrosci przez wariancje Laplacianu. | Bardzo tani CPU-only baseline. | Wrazliwy na szum i typ ilustracji. | low | OpenCV/NumPy | yes | low-medium | TEST_NOW | laplacian ksize, pass bands | Raportowac jako blur_score. |
| tenengrad_sharpness_score | Tenengrad sharpness score | sharpness | normalized_crop | sharpness score | Liczy energie gradientu Sobela. | Stabilny sygnal ostrosci i detalu. | Wiecej kosztu niz Laplacian, ale nadal tani. | low | OpenCV/NumPy | yes | low-medium | TEST_NOW | sobel ksize, gradient threshold | Dobry drugi sygnal ostrosci. |
| sobel_energy_score | Sobel energy score | sharpness/edge | normalized_crop | gradient energy | Mierzy ogolna energie krawedzi. | Tani i prosty. | Naklada sie z Tenengrad. | low | OpenCV/NumPy | yes | low | TEST_LATER | sobel ksize | Moze zostac backupiem. |
| edge_density_score | Edge density score | detail/readiness | normalized_crop | edge density | Liczy udzial pikseli krawedziowych. | Wykrywa cropy gladkie albo bez cech. | Ciemne/jasne grafiki moga znieksztalcac wynik. | low | OpenCV/NumPy | yes | medium | TEST_NOW | canny thresholds | Przydatne po problemach `not_enough_crop_descriptors`. |
| texture_density_score | Texture density score | detail/readiness | normalized_crop | density score | Mierzy lokalna zmiennosc/teksture bez identyfikacji karty. | Wykrywa cropy o malej liczbie cech. | Moze karac minimalistyczne ilustracje. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | local variance window | Przydatne dla Stage 6 readiness. |
| internal_detail_score | Internal detail score | detail/readiness | normalized_crop | score | Mierzy szczegoly wewnatrz obszaru karty, z pomniejszeniem borderow/marginesow. | Lepszy proxy identyfikowalnosci niz global edge density. | Wymaga estymacji obszaru karty. | low-mid | OpenCV/NumPy | yes | medium | TEST_NOW | inner_crop_ratio, edge/variance metrics | Nie porownuje do wzorcow kart. |
| aspect_ratio_error_score | Aspect ratio error score | geometry sanity | crop_metadata | error + score | Porownuje crop aspect ratio do oczekiwanego formatu tarota. | Bardzo stabilny sanity check. | Nie wykrywa problemow wizualnych. | low | NumPy | yes | low | TEST_NOW | expected_ratio=495/300, yellow/fail bands | Twardy sygnal BAD_ASPECT. |
| crop_size_score | Crop size score | geometry sanity | crop_metadata | size score | Sprawdza, czy crop ma oczekiwany rozmiar i minimalna liczbe pikseli. | Chroni Stage 6 przed za malym inputem. | Przy fixed target zwykle bedzie stale PASS. | low | NumPy | yes | low | TEST_NOW | target_w/h, min dimensions | Wazne dla fallbackow. |
| crop_completeness_score | Crop completeness score | composite/completeness | quality metrics | score | Laczy border, corners, fill ratio i edge cut risk. | Jeden czytelny wynik kompletności. | Zalezy od jakosci metryk skladowych. | low | NumPy | yes | medium | TEST_NOW | metric weights, fail overrides | Nie zastępuje metryk szczegolowych. |
| identification_readiness_score | Identification readiness score | composite/readiness | quality metrics | score | Laczy ostrosc, kontrast, teksture, ekspozycje i kompletność. | Daje Stage 6 prosty gate wejsciowy. | Moze sugerowac identyfikacje, choc jej nie wykonuje. | low | NumPy | yes | medium | TEST_NOW | metric weights, fail overrides | Nazwa musi jasno znaczyc readiness, nie recognition. |
| composite_crop_quality_score | Composite crop quality score | composite | quality metrics | score + PASS/YELLOW/FAIL | Agreguje kluczowe metryki w finalny status Stage 5. | Najlatwiejszy do raportu i matrix.csv. | Ryzyko zbyt wczesnego ustalenia wag. | low | NumPy | yes | medium | TEST_NOW | weights, hard fail flags | Wagi benchmark-only. |
| ml_quality_classifier | Learned crop quality classifier | ML quality | crop + labels | class/score | Uczony klasyfikator jakosci cropow. | Potencjalnie dobre po zebraniu datasetu. | Nowe zaleznosci, labelowanie, ryzyko overfitu. | high | new ML deps | possible | high | REQUIRES_APPROVAL | model, labels, hardware budget | Nie teraz. |
| template_similarity_readiness | Template similarity as readiness | recognition-adjacent | crop + card templates | similarity score | Uzywa podobienstwa do bazy kart jako proxy jakosci. | Moze korelowac z identyfikacja. | Narusza granice Stage 5/6. | mid-high | OpenCV/templates | partial | high | REJECT_FOR_NOW | n/a | To jest Stage 6, nie Stage 5. |
| orb_keypoint_count_score | ORB keypoint count | recognition-adjacent | crop | keypoint count | Liczy punkty ORB bez dopasowania do kart. | Bezposrednio zwiazane z przyszlym ORB. | Wprowadza zaleznosc od metody identyfikacji i miesza etapy. | low-mid | OpenCV ORB | yes | medium | TEST_LATER | nfeatures, thresholds | Tylko po decyzji, czy Stage 6 nadal bazuje na ORB. |

## Methods Recommended for TEST_NOW

Recommended `TEST_NOW` shortlist:

1. `edge_cut_risk_score`
2. `border_visible_score`
3. `border_continuity_score`
4. `corner_visibility_score`
5. `missing_border_score`
6. `card_edge_proximity_to_crop_edge`
7. `card_fill_ratio_score`
8. `background_margin_score`
9. `top_margin_ratio_score`
10. `side_margin_ratios`
11. `overexposed_pixel_ratio`
12. `underexposed_pixel_ratio`
13. `top_reflection_score`
14. `brightness_mean_score`
15. `contrast_stddev_score`
16. `histogram_spread_score`
17. `dynamic_range_score`
18. `variance_of_laplacian_blur_score`
19. `tenengrad_sharpness_score`
20. `edge_density_score`
21. `texture_density_score`
22. `internal_detail_score`
23. `aspect_ratio_error_score`
24. `crop_size_score`
25. `crop_completeness_score`
26. `identification_readiness_score`
27. `composite_crop_quality_score`

Uzasadnienie: shortlista pokrywa kompletność cropa, marginesy, refleksy, ekspozycję, ostrość, kontrast, detal i agregację do statusu. Wszystkie metody sa CPU-only, oparte o OpenCV/NumPy, bez nowych zaleznosci i bez identyfikacji kart.

## Methods Recommended for TEST_LATER

- `specular_highlight_score`
- `local_brightness_outlier_score`
- `sobel_energy_score`
- `orb_keypoint_count_score`

Uzasadnienie: te metryki moga byc pomocne, ale dokladaja wiecej parametrow albo zblizaja sie do Stage 6. W pierwszym benchmarku lepiej zmierzyc prostsze, bardziej debugowalne sygnaly.

## Methods Rejected for Now

- `template_similarity_readiness`
- kazda metoda uzywajaca bazy kart do oceny cropa,
- ORB/FLANN matching do wzorcow,
- OCR nazw lub symboli kart,
- klasyfikacja konkretnej karty.

Uzasadnienie: te podejscia mieszaja Stage 5 Crop Quality Validation ze Stage 6 Card Identification.

## Methods Requiring Approval

- `ml_quality_classifier`
- nowe modele ML,
- nowe zaleznosci poza OpenCV/NumPy,
- metody wymagajace labelowania wiekszego datasetu,
- integracja runtime albo Studio UI.

## Proposed Stage 5 Benchmark

Nastepny task:

```text
TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001
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

Proponowane kolumny `matrix.csv`:

```text
method
pair
change_type
crop_source_frame
crop_count
expected_crop_count
quality_pass_count
quality_yellow_count
quality_fail_count
crop_quality_score_avg
identification_readiness_score_avg
edge_cut_risk_count
background_margin_score_avg
top_margin_ratio_avg
top_reflection_score_avg
border_visible_score_avg
border_continuity_score_avg
corner_visibility_score_avg
card_fill_ratio_avg
brightness_mean_avg
contrast_score_avg
blur_score_avg
texture_density_score_avg
aspect_ratio_error_avg
reject_count
reject_reasons
warning_flags
runtime_ms
verdict
verdict_basis
```

Proponowane outputy:

```text
logs/offline_replay/stage5_crop_quality_validation/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/crop_quality_debug_sheet.png
  <method>/<pair>/quality_debug.json
  <method>/<pair>/crop_01_quality_overlay.png
  <method>/<pair>/crop_01_metrics.json
```

Benchmark moze lokalnie uzyc cropow Stage 4 albo odtworzyc pipeline Stage 1-4 i dopiero potem ocenic cropy. Outputow z `logs/offline_replay/` nie commitowac.

Werdykt benchmarku powinien pozostac `PROVISIONAL_RECOMMENDED` do czasu manualnego review debug sheetow i statystyk.

## Recommended Next Action

Nie implementowac jeszcze benchmarku Stage 5.

Supervisor powinien zaakceptowac albo skorygowac shortlistę `TEST_NOW`. Po akceptacji utworzyc:

```text
TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001
```

Benchmark Stage 5 musi pozostac izolowany w `tools/cv_detection_lab/`, bez runtime, bez Studio i bez identyfikacji kart.

## Sources

- OpenCV Canny edge detector: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html
- OpenCV Sobel derivatives: https://docs.opencv.org/4.x/d2/d2c/tutorial_sobel_derivatives.html
- OpenCV histograms: https://docs.opencv.org/4.x/d1/db7/tutorial_py_histogram_begins.html
- OpenCV thresholding: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
