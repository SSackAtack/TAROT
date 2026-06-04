# Stage 6 Real-Camera Fixture — Design

## Cel

Zaprojektować audytowalny real-camera validation fixture dla Stage 6 bez zmian
runtime i bez integracji metody identyfikacji z produkcyjnym pipeline.

Model:

```text
multiple immutable capture sessions
+
single offline aggregate validation manifest
```

## Architektura

Każde ujęcie walidacyjne jest zapisywane jako osobna, niezmienna sesja przez
istniejący mechanizm live fixture capture. Narzędzia offline agregują wskazane
sesje przez jeden manifest, walidują ich kompletność oraz generują ground truth
i manual review pack.

Capture odpowiada wyłącznie za dane źródłowe. Manifest i ground truth
odpowiadają za logikę walidacji. Żadne narzędzie offline nie modyfikuje plików
sesji capture.

## Zakres

### In scope

- specyfikacja nazw i struktury niezmiennych sesji capture,
- agregujący `manifest.json`,
- `ground_truth.json`,
- stabilne `sample_id`,
- preflight agregatu,
- manual review pack generowany z agregatu,
- scenariusze Gilded upright i reversed,
- wrong-deck Magic i Marchetti,
- trudne realne cropy klasyfikowane jako Stage 5 `YELLOW`,
- wizualnie podobne karty Gilded.

### Out of scope

- zmiany `app_cv/main.py`,
- zmiany `app_cv/tarotvision/*`,
- zmiany `app_ar/*`,
- modyfikacja istniejącego mechanizmu live fixture capture,
- runtime thresholdy,
- integracja ORB/AKAZE z produkcyjnym snapshot-first pipeline,
- automatyczne zatwierdzenie metody do runtime.

## Struktura danych

### Sesje capture

Każda sesja ma osobny katalog:

```text
logs/live_fixtures/<session_id>/
```

Przykładowe identyfikatory:

```text
stage6_real_gilded_03_upright
stage6_real_gilded_03_reversed
stage6_real_magic_15_wrong_deck
stage6_real_marchetti_21_wrong_deck
stage6_real_gilded_similar_pair_01
stage6_real_gilded_yellow_crop_01
```

Po dodaniu sesji do manifestu agregującego jej zawartość jest traktowana jako
read-only. Korekta wymaga utworzenia nowej sesji i aktualizacji manifestu.

### Agregat

Katalog agregatu:

```text
logs/live_fixtures/stage6_real_camera_validation/
```

Pliki:

```text
manifest.json
ground_truth.json
README_FOR_SUPERVISOR.md
```

Wygenerowane raporty preflight i manual review pack trafiają do:

```text
logs/offline_replay/stage6_real_camera_validation/
```

## Kontrakt manifestu

`manifest.json` zawiera:

```json
{
  "fixture_id": "stage6_real_camera_validation",
  "manifest_version": 1,
  "created_at": "ISO-8601",
  "capture_policy": "immutable_sessions",
  "samples": []
}
```

Każda pozycja `samples` zawiera:

```json
{
  "sample_id": "stable-id",
  "session_id": "stage6_real_gilded_03_upright",
  "session_path": "../stage6_real_gilded_03_upright",
  "scenario": "one_card",
  "category": "gilded_upright",
  "expected_deck": "gilded",
  "expected_card_id": "Gilded_03",
  "expected_orientation": "upright",
  "expected_behavior": "identify",
  "quality_expectation": "PASS_OR_YELLOW",
  "similarity_group": null,
  "notes": ""
}
```

`sample_id` jest stabilnym identyfikatorem pochodzącym z wartości
`session_id + scenario + category`, bez losowego UUID.

Manifest wskazuje ścieżki do sesji, ale ich nie modyfikuje ani nie kopiuje.

## Kategorie wymagane

Minimalny agregat musi obejmować:

- `gilded_upright`,
- `gilded_reversed`,
- `wrong_deck_magic`,
- `wrong_deck_marchetti`,
- `gilded_yellow`,
- `gilded_visually_similar`.

`gilded_reversed` jest osobną kategorią oraz ma
`expected_orientation: reversed`.

Wrong-deck ma:

```json
{
  "expected_behavior": "reject",
  "expected_card_id": null,
  "expected_orientation": "not_applicable"
}
```

## Minimalna macierz capture

Pierwsza wersja agregatu powinna zawierać co najmniej:

- 6 różnych kart Gilded upright,
- te same 6 kart Gilded reversed,
- 4 karty Magic jako wrong-deck,
- 4 karty Marchetti jako wrong-deck,
- 4 realne próbki Gilded z jakością Stage 5 `YELLOW`,
- 2 grupy wizualnie podobnych kart Gilded, minimum 2 karty na grupę.

Łączne minimum: 28 próbek. Jedna sesja może dostarczać tylko jedną pozycję
agregatu, aby zachować prostą audytowalność.

## Ground truth

`ground_truth.json` jest generowany lub utrzymywany obok manifestu i zawiera
jedną etykietę dla każdego `sample_id`.

Wymagane pola:

```text
sample_id
expected_deck
expected_card_id
expected_orientation
expected_behavior
label_status
notes
```

`label_status` musi mieć wartość `manual_confirmed` przed użyciem próbki
w benchmarku identyfikacji.

## Preflight

Offline preflight sprawdza:

- unikalność `sample_id`,
- dozwolone kategorie i expected behaviors,
- obecność każdej wskazanej sesji,
- obecność wymaganego scenariusza i plików capture,
- zgodność manifestu z ground truth,
- kompletność wszystkich wymaganych kategorii,
- minimalne liczby próbek,
- poprawne pola reversed,
- poprawne pola wrong-deck,
- `label_status: manual_confirmed`,
- brak modyfikowania sesji podczas działania.

Preflight zapisuje `preflight_report.json` i `preflight_report.md`.

Status:

- `PASS`: agregat kompletny i gotowy do manual review,
- `WARNING`: komplet danych istnieje, ale są nieblokujące ograniczenia,
- `PROVISIONAL_BLOCKED`: brakuje danych lub metadane są sprzeczne.

## Manual review pack

Manual review pack jest generowany wyłącznie z agregującego manifestu.

Zawiera:

- `README_FOR_SUPERVISOR.md`,
- kopię manifestu i ground truth,
- raport preflight,
- indeks próbek,
- jeden debug sheet na próbkę,
- grupowanie po kategorii,
- osobne zestawienie visually similar groups,
- oczekiwane deck/card/orientation/behavior i widoczny wynik jakości Stage 5.

Pack nie modyfikuje sesji i nie stanowi zgody na runtime integration.

## Workflow operatorski

1. Operator tworzy nową unikalną nazwę sesji.
2. Operator ustawia scenę i wykonuje capture istniejącym mechanizmem.
3. Sesja jest wizualnie sprawdzana.
4. Sesja zostaje dodana do agregującego manifestu.
5. Ground truth zostaje ręcznie potwierdzony.
6. Preflight waliduje kompletność agregatu.
7. Generator tworzy manual review pack.
8. Supervisor wydaje decyzję o jakości fixture.

Niepoprawna sesja nie jest edytowana. Jest zastępowana nową sesją.

## Kryteria akceptacji taska

- istnieje specyfikacja agregatu i ground truth,
- istnieje offline preflight agregatu,
- istnieje generator manual review pack,
- agregat ma minimum 28 ręcznie potwierdzonych próbek,
- wszystkie wymagane kategorie są obecne,
- żadna sesja capture nie została zmodyfikowana przez narzędzia offline,
- nie zmieniono runtime,
- Supervisor może przeprowadzić manual review wyłącznie z wygenerowanej paczki.

## Decyzja bezpieczeństwa

Real-camera fixture jest warunkiem rozmowy o przyszłym runtime thresholdzie,
ale ukończenie tego taska samo w sobie nie zatwierdza thresholdów ani runtime
integration.
