# TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001

## Cel

Przygotować izolowany preflight walidujący wejścia wymagane do przyszłego benchmarku Stage 6 Card Identification:

- `reference_deck_dir`,
- `deck_profile.json`,
- `ground_truth.json`,
- dostępność outputów Stage 5.

## Zakres

Dozwolone zmiany:

- `tools/cv_detection_lab/stage6_preflight.py`,
- `app_cv/tests/test_cv_detection_lab_stage6_preflight.py`,
- dokumentacja taska w `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001/`,
- `.ai/TASKS_INDEX.md`,
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`.

## Poza zakresem

- Brak implementacji identyfikacji kart.
- Brak ORB / FLANN / AKAZE / BRISK / template matching / OCR / ML.
- Brak benchmarku Stage 6.
- Brak zmian runtime, WebSocket, Studio UI, ArUco i `SnapshotFirstPipeline`.
- Brak zmian w benchmarkach Stage 1-5.
- Brak nowych zależności.

## Kryteria akceptacji

- Preflight zwraca `PASS`, `WARNING` albo `PROVISIONAL_BLOCKED`.
- `PASS` jest możliwy tylko przy kompletnym fixture, profilu talii, obrazach referencyjnych, ground truth, zgodności profilu i poprawnych parach.
- Brak outputów Stage 5 daje `WARNING`, ponieważ przyszły benchmark może sam regenerować Stage 1-5.
- Błędy wejść blokujących dają `PROVISIONAL_BLOCKED`.
- Raporty są zapisywane jako `preflight_report.json` i `preflight_report.md`.

## Komendy

```powershell
python tools\cv_detection_lab\stage6_preflight.py `
  --fixture logs\live_fixtures\event_first_current_debug_verified `
  --reference-deck-dir biblioteka_talii\<deck>\produkcja\wzorce_cv `
  --deck-profile biblioteka_talii\<deck>\deck_profile.json `
  --ground-truth logs\live_fixtures\event_first_current_debug_verified\ground_truth.json `
  --output logs\offline_replay\stage6_card_identification_preflight
```
