# TEST_REPORT

## Data

2026-06-04

## Wynik

`PASS`

## Artefact check

```powershell
Get-ChildItem logs\offline_replay\stage5_crop_quality_validation\manual_review_pack_quality_metric_suite_v1 -Filter *.png
```

Wynik:

```text
6 PNG files present
```

## Source check

All 6 requested source files existed before copy:

```text
empty_to_empty/crop_quality_debug_sheet.png
empty_to_one_card/crop_quality_debug_sheet.png
empty_to_three_cards/crop_quality_debug_sheet.png
one_card_to_three_cards/crop_quality_debug_sheet.png
one_card_to_empty/crop_quality_debug_sheet.png
three_cards_to_empty/crop_quality_debug_sheet.png
```

## Backend tests

`NOT_RUN` — task only copies existing manual review PNG artefacts and updates documentation.

## Frontend tests

`NOT_RUN` — task does not change `app_ar/`.
