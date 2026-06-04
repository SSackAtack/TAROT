# Research Report — Stage 1 Difference Detection

## Cel

Wybrać techniki do pierwszego benchmarku offline dla nowego silnika state-first TarotVision. Stage 1 ma wykrywać różnice między stabilnymi snapshotami i klasyfikować je na poziomie regionów, bez rozpoznawania kart.

Wejściowy model:

```text
empty_reference + previous_snapshot + current_snapshot + known_cards
```

Testowe fixture:

```text
logs/live_fixtures/event_first_current_debug_verified/
```

Pary obowiązkowe:

```text
empty -> empty
empty -> one_card
empty -> three_cards
one_card -> three_cards
one_card -> empty
three_cards -> empty
```

## Źródła

- OpenCV thresholding: https://docs.opencv.org/3.4/d7/d4d/tutorial_py_thresholding.html
- OpenCV background subtraction MOG2/KNN: https://docs.opencv.org/3.4/d1/dc5/tutorial_background_subtraction.html
- OpenCV ECC alignment API: https://docs.opencv.org/4.x/javadoc/org/opencv/video/Video.html
- scikit-image SSIM API: https://scikit-image.org/docs/stable/api/skimage.metrics.html

## Założenia sprzętowe i projektowe

- Docelowy laptop operatorski: HP EliteBook 830 G6, więc preferowane są metody CPU-only, szybkie i łatwe do debugowania.
- Aktualne zależności projektu obejmują OpenCV i NumPy. Metody wymagające nowych paczek są oznaczane jako `REQUIRES_APPROVAL`.
- Fixture są ręcznie zatwierdzone jako prawda fizyczna, nawet jeśli payload runtime raportował błędny wynik.
- Pierwszy benchmark ma preferować prostotę, mierzalność i obrazy debug nad “inteligentnymi” metodami trudnymi do interpretacji.

## Candidate Techniques Matrix

| Metoda | Status | Powód | Ryzyko | Metryki w benchmarku |
|---|---|---|---|---|
| Grayscale `absdiff` + fixed threshold | `TEST_NOW` | Najprostszy baseline, szybki, obecne zależności wystarczą. | Wrażliwy na światło i autoekspozycję. | `changed_area_ratio`, `region_count`, `runtime_ms`, false positives. |
| Grayscale `absdiff` + Gaussian blur | `TEST_NOW` | Tani sposób redukcji szumu przed progowaniem. | Może sklejać bliskie regiony. | region count quality, mask stability, runtime. |
| Grayscale `absdiff` + median blur | `TEST_NOW` | Dobry kandydat na punktowe refleksy i szum impulsowy. | Może zjadać cienkie krawędzie kart. | ignored small count, region shape stability. |
| LAB difference, kanał L + a/b | `TEST_NOW` | Oddziela jasność od składowych barwnych; sensowne przy matach i kartach o podobnej luminancji. | Konwersja i agregacja kanałów wymagają ostrożnego benchmarku. | local/global difference score, region quality. |
| HSV difference, V/S weighted | `TEST_NOW` | Może lepiej odróżniać kartę od tła przy zmianach nasycenia. | Hue niestabilny przy niskim nasyceniu. | false positives on empty, region count. |
| Otsu threshold na diff | `TEST_NOW` | Automatyczny próg bez strojenia jednej wartości na ślepo. | Przy małej zmianie histogram może dobrać próg zbyt agresywnie. | threshold value, false negative rate. |
| Adaptive threshold na diff | `TEST_LATER` | Może pomóc przy nierównym świetle. | Może produkować poszatkowane maski, trudniejsze do debugowania. | mask fragmentation, connected components. |
| Morphology open/close post-process | `TEST_NOW` | Niezbędne do stabilnych regionów po baseline diff. | Złe jądro może łączyć osobne karty. | region merge/split quality. |
| Connected components | `TEST_NOW` | Prosty, mierzalny sposób liczenia regionów. | Słabszy dla dziurawych masek bez morfologii. | region_count, bbox, area ratios. |
| Contour-based regions | `TEST_NOW` | Naturalny OpenCV path, łatwy debug overlay. | Kontury mogą być niestabilne przy fragmentacji. | contour count, bbox quality. |
| Canny / edge difference | `TEST_LATER` | Może wykrywać granice kart przy słabym kontraście wypełnienia. | Krawędzie z maty i wzorów kart mogą generować szum. | edge density, false positives. |
| Sobel / gradient difference | `TEST_LATER` | Alternatywa dla edge-first bez progów Canny. | Wrażliwy na teksturę i odblaski. | gradient mask area, stability. |
| Morphological gradient | `TEST_LATER` | Może podkreślić obwód obiektu. | Raczej pomocnicze niż główna detekcja zmiany. | boundary continuity. |
| MOG2 background subtractor | `TEST_LATER` | Dostępne w OpenCV, znane do tła wideo. | Nasz model opiera się na stabilnych snapshotach, nie ciągłym video learningu; ryzyko nadmiernej złożoności. | adaptation behavior, false positives. |
| KNN background subtractor | `TEST_LATER` | Alternatywa OpenCV dla MOG2. | Podobne ryzyko jak MOG2; może być mniej przejrzyste niż absdiff. | runtime, region stability. |
| SSIM difference | `REQUIRES_APPROVAL` | Potencjalnie dobre dla zmian strukturalnych i luminancji. | Wymaga `scikit-image`, której nie ma w aktualnym minimalnym stacku. | DSSIM map quality, runtime. |
| Illumination normalization | `TEST_NOW` | Potrzebne do rozróżnienia lokalnej karty od globalnej zmiany światła. | Zbyt agresywna normalizacja może ukryć realną kartę. | global_shift_score, empty->empty stability. |
| Shadow/highlight suppression | `TEST_LATER` | Może pomóc przy odblaskach i cieniach ręki po motion gate. | Na Stage 1 nie chcemy projektować pod ruch ręki jako normalny input. | false positives from bright regions. |
| ECC alignment fallback | `TEST_LATER` | Może kompensować drobny shift warpu/kamery. | Koszt CPU i ryzyko maskowania realnej zmiany; tylko fallback diagnostyczny. | alignment time, shift score reduction. |

## Rekomendowana shortlista `TEST_NOW`

Pierwszy benchmark powinien testować małą, mierzalną rodzinę metod bez nowych zależności:

1. `gray_absdiff_fixed`
2. `gray_absdiff_gaussian`
3. `gray_absdiff_median`
4. `lab_absdiff_weighted`
5. `hsv_absdiff_weighted`
6. `gray_absdiff_otsu`
7. `illumination_normalized_gray_absdiff`

Każda metoda powinna używać wspólnego post-processingu:

```text
threshold -> morphology open/close -> connected components -> contour/bbox overlay
```

## Metody odłożone

`TEST_LATER`: adaptive threshold, Canny, Sobel, morphological gradient, MOG2, KNN, shadow/highlight suppression, ECC fallback.

Uzasadnienie: są potencjalnie użyteczne, ale zwiększają liczbę wariantów. Stage 1 powinien najpierw zbudować baseline i format raportu.

## Metody wymagające akceptacji

`REQUIRES_APPROVAL`: SSIM / DSSIM.

Uzasadnienie: obecny projekt nie powinien dodawać `scikit-image` bez decyzji Michała/Supervisora. Jeżeli baseline OpenCV/NumPy nie da dobrych wyników, SSIM może wrócić jako osobny research spike.

## Benchmark Plan

### Wejście

Używać `analysis_frame_*.png`, bo są już sprowadzone do przestrzeni analizy po ArUco i są właściwsze do porównań pikselowych niż surowe `raw_frame_*.png`.

```text
empty/analysis_frame_0.png
one_card/analysis_frame_1.png
three_cards/analysis_frame_3.png
```

### Oczekiwane wyniki

| Para | Oczekiwane regiony | Typ |
|---|---:|---|
| empty -> empty | 0 | no_change |
| empty -> one_card | 1 | added |
| empty -> three_cards | 3 albo logiczne regiony 3 kart | added |
| one_card -> three_cards | 2 nowe + zachowanie starej karty | added |
| one_card -> empty | 1 | removed |
| three_cards -> empty | 3 | removed |

### Output benchmarku

```text
logs/offline_replay/stage1_diff/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/diff.png
  <method>/<pair>/mask.png
  <method>/<pair>/regions_overlay.png
```

### Metryki

- `runtime_ms`
- `changed_area_ratio`
- `region_count`
- `expected_region_count`
- `region_count_delta`
- `global_shift_score`
- `ignored_small_count`
- `ignored_large_count`
- `false_positive`
- `false_negative`
- `verdict`: `PASS`, `YELLOW`, `FAIL`

### Kryterium decyzji Stage 1

Metoda może dostać rekomendację `APPROVED_STAGE_METHOD`, jeżeli:

- `empty -> empty` daje 0 istotnych regionów,
- `empty -> one_card` daje 1 region,
- `one_card -> three_cards` wykrywa dodane regiony bez kasowania istniejącej karty,
- `three_cards -> empty` wykrywa usunięcia jako regiony o sensownym rozmiarze,
- runtime pojedynczej pary pozostaje praktyczny na CPU,
- debug overlay jasno pokazuje, dlaczego metoda działa albo zawodzi.

## Decyzja Research Gate

Rekomenduję przejść do `TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001` z metodami `TEST_NOW` i bez nowych zależności.

Nie rekomenduję teraz:

- dalszego strojenia live runtime,
- zmiany `ChangeDetector` w `app_cv`,
- dodawania `scikit-image`,
- implementowania Stage 2 przed raportem benchmarku Stage 1.
