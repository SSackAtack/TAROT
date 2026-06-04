# Stage 6 Real-Camera Fixture Capture

## Cel

Zebrać minimum 28 audytowalnych próbek real-camera Stage 6 bez modyfikowania
mechanizmu live capture i bez integracji runtime.

## Zasada danych

```text
jedna niezmienna sesja capture = jedna próbka agregatu
```

Po dodaniu sesji do agregującego manifestu nie edytuj jej plików. Błędną sesję
zastąp nową sesją o nowym `session_id`, a następnie zaktualizuj manifest.

## Zalecany tryb: wizard operatorski

Najbezpieczniejsza ścieżka to uruchomienie wizarda:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py
```

Wizard:

- prowadzi przez 28 kroków capture,
- pokazuje, którą talię, kartę i orientację przygotować,
- drukuje właściwe zmienne środowiskowe dla istniejącego live capture,
- czeka na ręczne potwierdzenie operatora,
- sprawdza, czy sesja ma wymagane pliki,
- dla `YELLOW` i `visually similar` wymaga wpisania rzeczywistego ID karty
  w formacie `Gilded_XX`,
- dopisuje potwierdzoną próbkę do `manifest.json` i `ground_truth.json`,
- po zebraniu kompletu uruchamia preflight,
- po `PASS` generuje manual review pack.

Wizard nie uruchamia backendu automatycznie i nie zmienia runtime. Jest tylko
warstwą prowadzącą operatora po istniejącym mechanizmie live fixture capture.

Jeśli wizard pokazuje komunikat, że nie widzi kompletu plików sesji, oznacza to,
że backend nie zapisał jeszcze snapshotu w oczekiwanym folderze. Najczęściej
trzeba wtedy:

1. Skopiować env vars pokazane przez wizard do terminala backendu.
2. Uruchomić lub zrestartować backend z tymi env vars.
3. Ustawić kartę stabilnie w Studio.
4. Poczekać, aż backend zapisze snapshot.
5. Wrócić do wizarda i wybrać ponowne sprawdzenie.

Samo naciśnięcie Enter w wizardzie nie robi zdjęcia. Snapshot zapisuje backend.

Podgląd planu bez rozpoczęcia capture:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py --print-plan
```

Jeżeli używasz niestandardowych katalogów:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py `
  --log-dir logs `
  --aggregate-dir logs/live_fixtures/stage6_real_camera_validation `
  --output-dir logs/offline_replay/stage6_real_camera_validation
```

## Uruchomienie istniejącego capture

Przed uruchomieniem backendu ustaw:

```powershell
$env:TAROTVISION_CAPTURE_LIVE_FIXTURES = "1"
$env:TAROTVISION_LIVE_FIXTURE_NAME = "<unique_session_id>"
$env:TAROTVISION_LIVE_FIXTURE_SCENARIO = "one_card"
```

Używaj unikalnych nazw, przykładowo:

```text
stage6_real_gilded_03_upright
stage6_real_gilded_03_reversed
stage6_real_magic_15_wrong_deck
stage6_real_marchetti_21_wrong_deck
stage6_real_gilded_yellow_01
stage6_real_gilded_similar_group_01_card_01
```

## Minimalna macierz

- 6 różnych Gilded upright.
- Te same 6 Gilded reversed.
- 4 Magic wrong-deck.
- 4 Marchetti wrong-deck.
- 4 Gilded z realnym statusem Stage 5 `YELLOW`.
- 2 grupy wizualnie podobnych kart Gilded, po minimum 2 karty.

Łączne minimum: 28 sesji.

W kategoriach `YELLOW` i `visually similar` wizard nie zgaduje tożsamości
karty. Operator musi wpisać realny identyfikator z talii Gilded, np.
`Gilded_34`. Etykiety techniczne typu `Gilded_YELLOW_01` albo
`Gilded_SIM_01_01` są zakazane i preflight je zablokuje.

## Procedura pojedynczej sesji

W trybie wizarda poniższe kroki wykonujesz wtedy, kiedy wizard o to poprosi.

1. Przygotuj wyłącznie jedną kartę i wymaganą orientację.
2. Ustaw nowy unikalny `TAROTVISION_LIVE_FIXTURE_NAME`.
3. Uruchom istniejący capture i poczekaj na zapis scenariusza `one_card`.
4. Sprawdź `analysis_frame_1.png`, `raw_frame_1.png`, `payload.json`,
   `metrics.json` i `roi_diagnostics.json`.
5. Potwierdź, że obraz przedstawia oczekiwaną kartę i kategorię.
6. Dodaj sesję jako jedną pozycję do agregującego `manifest.json`.
7. Dodaj odpowiadającą etykietę do `ground_truth.json`.
8. Ustaw `label_status: manual_confirmed` dopiero po ręcznym potwierdzeniu.
9. Nie edytuj więcej sesji.

## Ground truth

Dla Gilded:

```json
{
  "expected_deck": "gilded",
  "expected_card_id": "Gilded_03",
  "expected_orientation": "upright",
  "expected_behavior": "identify",
  "label_status": "manual_confirmed"
}
```

Dla wrong-deck:

```json
{
  "expected_deck": "magic",
  "expected_card_id": null,
  "expected_orientation": "not_applicable",
  "expected_behavior": "reject",
  "label_status": "manual_confirmed"
}
```

## Preflight

```powershell
python tools/cv_detection_lab/stage6_real_camera_preflight.py `
  --manifest logs/live_fixtures/stage6_real_camera_validation/manifest.json `
  --ground-truth logs/live_fixtures/stage6_real_camera_validation/ground_truth.json `
  --output logs/offline_replay/stage6_real_camera_validation
```

Przed zebraniem wszystkich sesji oczekiwany status to `PROVISIONAL_BLOCKED`.

## Manual review pack

Po uzyskaniu preflight `PASS`:

```powershell
python tools/cv_detection_lab/stage6_real_camera_manual_review_pack.py `
  --manifest logs/live_fixtures/stage6_real_camera_validation/manifest.json `
  --ground-truth logs/live_fixtures/stage6_real_camera_validation/ground_truth.json `
  --preflight logs/offline_replay/stage6_real_camera_validation/preflight_report.json `
  --output logs/offline_replay/stage6_real_camera_validation/manual_review_pack
```

Manual review pack nie zatwierdza runtime thresholdów ani runtime integration.
