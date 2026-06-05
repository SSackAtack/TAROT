# STATE: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## Status

TODO

## Branch

`task/cv-stage-6-calibration-wizard-one-card-recognition-acceptance-001`

## Stan aktualny

Task utworzony jako follow-up po stabilizacji geometrii jednej karty. Fizyczna talia użyta w smoke teście została potwierdzona jako Gilded, a runtime/Studio również używały aktywnej talii `gilded`. Niespójność talii nie wyjaśnia więc `accepted_total=1/3`.

## Session Status (2026-06-05)

- Utworzono zakres diagnostyczny nowego taska.
- Ustalono, że nie wolno kontynuować zmian w geometrii bez nowych dowodów.
- Ustalono, że pierwszym krokiem jest zebranie szczegółowej diagnostyki recognition dla odrzuconych cropów.

## Kolejne kroki

1. Przejść na branch `task/cv-stage-6-calibration-wizard-one-card-recognition-acceptance-001`.
2. Zebrać dane recognition dla 3 próbek `one_card` Gilded.
3. Dopiero po root cause zdecydować, czy potrzebny jest mały fix, czy raport `DIAGNOSTIC_COMPLETE_FIX_REQUIRED`.
