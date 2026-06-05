# TASK-CV-OFFLINE-LAB-STAGE-5-MANUAL-REVIEW-PACK-001

## Cel

Przygotowac paczke manual review Stage 5 dla metody:

```text
quality_metric_suite_v1
```

Paczka ma zawierac 6 plikow `crop_quality_debug_sheet.png` wygenerowanych przez benchmark Stage 5.

## Zakres

Dozwolone:

- skopiowanie istniejacych artefaktow debug sheet z `logs/offline_replay/stage5_crop_quality_validation/quality_metric_suite_v1/`
- przygotowanie lokalnej paczki review w `logs/offline_replay/stage5_crop_quality_validation/manual_review_pack_quality_metric_suite_v1/`
- aktualizacja dokumentacji taska w `.ai/tasks/`
- aktualizacja `.ai/TASKS_INDEX.md`

Poza zakresem:

- zmiany runtime CV
- zmiany benchmarku Stage 5
- zmiany metryk `quality_metric_suite_v1`
- zapis `APPROVED_STAGE_5_METHOD`
- start Stage 6
- commitowanie plikow PNG lub innych artefaktow z `logs/`

## Kryteria akceptacji

- istnieje 6 plikow PNG paczki manual review
- kazdy plik odpowiada jednemu scenariuszowi benchmarku Stage 5
- dokumentacja wskazuje dokladne sciezki do paczki
- repozytorium nie zawiera zacommitowanych artefaktow `logs/`
