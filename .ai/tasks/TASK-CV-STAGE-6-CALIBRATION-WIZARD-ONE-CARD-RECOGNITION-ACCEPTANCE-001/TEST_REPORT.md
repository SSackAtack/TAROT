# TEST REPORT: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## Testy automatyczne

NOT_RUN — task utworzony, implementacja diagnostyki jeszcze nierozpoczęta.

## Smoke / diagnostyka fizyczna

Punkt wejścia z poprzedniego taska:

- Physical deck: Gilded.
- Active runtime deck: `gilded`.
- `empty`: PASS.
- `one_card` geometry: PASS, `detected_count=1` dla 3/3 próbek.
- `one_card` acceptance: FAIL, `accepted_total=1/3`.
- `three_cards`: NOT_RUN.

## Zakres

- `app_ar/public/active_decks.json`: poza zakresem, nie commitować.
- Frontend build: NOT_RUN — frontend not changed.
