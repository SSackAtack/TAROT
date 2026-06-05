# TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001

## Cel

Zastąpić strukturalne etykiety `UNKNOWN_DECK` w Stage 6 ground truth realnymi `expected_card_id`, tylko tam gdzie tożsamość karty jest możliwa do jednoznacznego potwierdzenia.

## Zakres

Dozwolone zmiany:

- `logs/live_fixtures/event_first_current_debug_verified/ground_truth.json`
- dokumentacja taska w `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001/`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-6-plan.md`

## Poza Zakresem

- Brak benchmarku Stage 6.
- Brak implementacji identyfikacji kart.
- Brak ORB / FLANN / AKAZE / BRISK / template matching / OCR / ML.
- Brak zmian runtime.

## Źródła Potwierdzenia

- `logs/offline_replay/stage5_crop_quality_validation/quality_metric_suite_v1/*/crop_quality_debug_sheet.png`
- `biblioteka_talii/gilded/produkcja/wzorce_cv/Gilded_*.jpg`
- roboczy kontaktowy sheet referencji: `logs/offline_replay/stage6_manual_label_confirmation/gilded_reference_contact_sheet.jpg`

## Potwierdzone Karty

- `Gilded_34`
- `Gilded_54`
- `Gilded_73`
