# Stage 6 Synthetic Validation Benchmark — Design

## Cel

Zbudować szerszy, deterministyczny benchmark walidacyjny dla
`orb_bfmatcher_ratio_test` przed jakąkolwiek integracją runtime oraz porównać
go z `akaze_bfmatcher` jako kandydatem fallback.

Benchmark pozostaje całkowicie izolowany w offline labie.

## Zakres

### In scope

- deterministyczne generowanie wariantów syntetycznych na bazie istniejących
  wzorców kart,
- 24 równomiernie wybrane unikalne karty Gilded,
- przypadki upright i reversed,
- trudne warianty imitujące cropy Stage 5 `YELLOW`,
- unknown / wrong deck z dwóch innych talii,
- porównanie ORB i AKAZE,
- pomiar dokładności, odrzucania wrong deck, confidence gap i runtime,
- manifest reprodukowalności, raporty i przykładowe debug sheety.

### Out of scope

- zmiany `app_cv/tarotvision/*`, `app_cv/main.py` i `app_ar/*`,
- integracja runtime,
- strojenie runtime thresholdów,
- twierdzenie, że lokalny runtime jest pomiarem wykonanym na HP EliteBook 830 G6,
- commitowanie pełnego wygenerowanego datasetu obrazów.

## Zestaw walidacyjny

### Gilded

Benchmark wybierze deterministycznie 24 karty z `deck_profile.json`, rozłożone
równomiernie po pełnej liście 78 kart.

Dla każdej karty powstaną warianty:

1. `upright_clean`
2. `reversed_clean`
3. `perspective`
4. `blur`
5. `exposure`
6. `extra_margin`
7. `yellow_combined`

Wariant `yellow_combined` połączy umiarkowaną perspektywę, blur, zmianę
ekspozycji i dodatkowy margines. Parametry muszą być stałe i zapisane
w manifeście.

### Unknown / wrong deck

Benchmark wybierze deterministycznie po 12 kart z dwóch innych kompletnych
talii dostępnych w repozytorium. Te próbki nie mogą znajdować się w reference
deck Gilded i będą oceniane jako przypadki wymagające odrzucenia.

## Reprodukowalność

- Generator użyje stałego seed.
- Każda próbka otrzyma stabilny `sample_id`.
- Manifest zapisze źródłową kartę, kategorię, orientację i parametry
  transformacji.
- Pełne obrazy syntetyczne będą generowane w pamięci.
- Do outputu trafią wyłącznie przykładowe debug sheety potrzebne do audytu.

## Metody

Benchmark uruchomi:

- `orb_bfmatcher_ratio_test` — metoda zatwierdzona dla bieżącego fixture,
- `akaze_bfmatcher` — fallback candidate.

Obie metody użyją istniejącej implementacji z
`tools/cv_detection_lab/stage6_identification_methods.py`.

## Odrzucanie unknown / wrong deck

Benchmark nie zatwierdza runtime thresholdu. Zamiast tego:

- zapisze score top-1 i confidence gap dla known oraz wrong-deck samples,
- policzy false-accept rate dla jawnie zadanego, offline-only progu
  walidacyjnego,
- pokaże rozkłady score/gap potrzebne do późniejszej decyzji thresholdowej.

Próg offline-only będzie częścią konfiguracji benchmarku i raportu, nie
konfiguracji runtime.

## Metryki

Dla każdej metody raport obejmie:

- overall top-1 accuracy,
- overall top-3 accuracy,
- upright accuracy,
- reversed accuracy,
- `yellow_combined` accuracy,
- wrong-deck false-accept rate,
- mean confidence gap,
- runtime p50,
- runtime p95,
- średni runtime.

Raport musi osobno pokazać wyniki dla każdej kategorii wariantu.

## Pomiar runtime

Runtime zostanie zmierzony lokalnie na obecnej maszynie, po krótkim warm-up,
dla pojedynczego cropu porównywanego z pełnym reference deck Gilded.

Raport musi jawnie oznaczyć wynik jako lokalny proxy. Nie wolno opisywać go
jako bezpośredni pomiar HP EliteBook 830 G6, jeśli benchmark nie został
uruchomiony na tym urządzeniu.

## Artefakty

Benchmark zapisze pod `logs/offline_replay/stage6_validation_benchmark/`:

- `manifest.json`,
- `matrix.csv`,
- `report.json`,
- `report.md`,
- przykładowe debug sheety dla upright, reversed, `yellow_combined`
  i wrong-deck.

Artefakty pozostają ignorowane przez Git. Kod, testy i dokumentacja zadania
zostaną zapisane w repozytorium.

## Kryteria sukcesu

Benchmark jest ukończony, gdy:

- dataset jest deterministyczny i reprodukowalny,
- obejmuje wszystkie wymagane kategorie,
- ORB i AKAZE są porównane tym samym zestawem próbek,
- raport pokazuje accuracy, wrong-deck false accepts i runtime p50/p95,
- output zawiera debug sheety do manual review,
- pełne testy offline lab nie wykazują regresji,
- nie zmieniono runtime.

Wynik benchmarku nie stanowi automatycznej zgody na integrację runtime.
