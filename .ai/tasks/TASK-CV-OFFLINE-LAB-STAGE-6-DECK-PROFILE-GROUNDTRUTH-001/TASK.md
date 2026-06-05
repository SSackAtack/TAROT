# TASK-CV-OFFLINE-LAB-STAGE-6-DECK-PROFILE-GROUNDTRUTH-001

## Cel

Uzupełnić brakujące dane wejściowe wymagane przez Stage 6 Card Identification Preflight:

- `biblioteka_talii/gilded/deck_profile.json`
- `logs/live_fixtures/event_first_current_debug_verified/ground_truth.json`

## Zakres

Dozwolone zmiany:

- dane wejściowe Stage 6 dla talii Gilded,
- dokumentacja taska,
- `.ai/TASKS_INDEX.md`,
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`.

## Poza Zakresem

- Brak identyfikacji kart.
- Brak benchmarku Stage 6.
- Brak ORB / FLANN / AKAZE / BRISK / template matching / OCR / ML.
- Brak zmian runtime, Studio, WebSocket, ArUco i pipeline CV.
- Brak nowych zależności.

## Decyzja Danych

`deck_profile.json` powstał na podstawie `biblioteka_talii/gilded/info.json`.

Ponieważ repo nie zawiera potwierdzonych ręcznych etykiet kart dla fixture, `ground_truth.json` używa `UNKNOWN_DECK` dla wszystkich niepustych cropów. To przechodzi strukturalny preflight, ale nie jest finalnym ground truth do pomiaru top1/top3 accuracy.
