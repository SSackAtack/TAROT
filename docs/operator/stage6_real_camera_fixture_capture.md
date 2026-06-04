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

## Zalecany tryb: wizard jako aparat

Najbezpieczniejsza ścieżka to uruchomienie launchera z głównego katalogu
repozytorium:

```powershell
.\stage6_capture_wizard.bat
```

Wizard:

- prowadzi przez 28 kroków capture,
- pokazuje, którą talię, kartę i orientację przygotować,
- używa kamery jak aparatu fotograficznego,
- po naciśnięciu Enter robi jedno zdjęcie,
- zapisuje komplet wymaganych plików sesji,
- czeka na ręczne potwierdzenie operatora,
- pozwala zaakceptować zdjęcie, powtórzyć je, pominąć krok albo przerwać,
- dla `YELLOW` i `visually similar` wymaga wpisania rzeczywistego ID karty
  w formacie `Gilded_XX`,
- dopisuje potwierdzoną próbkę do `manifest.json` i `ground_truth.json`,
- po zebraniu kompletu uruchamia preflight,
- po `PASS` generuje manual review pack.

W domyślnym trybie backend i Studio mogą być wyłączone. Wizard nie zmienia
runtime i nie uruchamia aplikacji. Kamera musi być dostępna dla OpenCV jako
indeks `0`, chyba że uruchomisz skrypt z innym `--camera-index`.

Wizard otwiera kamerę przez tę samą klasę `CameraSession`, której używa backend:
wymusza rozdzielczość `1280x720` i odtwarza zapisane ustawienia z
`logs/camera_settings.json`, między innymi focus, exposure, brightness i
contrast.

Jeżeli zdjęcie jest błędne, wybierz `r` i zrób je ponownie. Wizard nadpisuje
niezaakceptowane pliki tej samej sesji i dopisuje próbkę do agregatu dopiero po
ręcznym zaakceptowaniu zdjęcia.

Podgląd planu bez rozpoczęcia capture:

```powershell
.\stage6_capture_wizard.bat plan
```

Bez launchera można uruchomić bezpośrednio:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py
```

Jeżeli system ma więcej kamer:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py --camera-index 1
```

Jeżeli używasz niestandardowych katalogów:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py `
  --log-dir logs `
  --aggregate-dir logs/live_fixtures/stage6_real_camera_validation `
  --output-dir logs/offline_replay/stage6_real_camera_validation
```

## Tryb legacy: istniejący backend capture

Ten tryb jest opcją awaryjną. Użyj go tylko wtedy, gdy świadomie chcesz, żeby
snapshot zapisywał backend zamiast wizarda:

```powershell
python tools/cv_detection_lab/stage6_real_camera_capture_wizard.py --capture-mode backend
```

W tym trybie samo naciśnięcie Enter w wizardzie nie robi zdjęcia. Snapshot
zapisuje backend.

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
2. Sprawdź nazwę sesji pokazaną przez wizard.
3. W domyślnym trybie naciśnij Enter w wizardzie, żeby zrobić zdjęcie.
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
