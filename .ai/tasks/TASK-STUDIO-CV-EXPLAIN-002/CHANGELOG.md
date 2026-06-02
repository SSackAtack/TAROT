# CHANGELOG: TASK-STUDIO-CV-EXPLAIN-002

## 2026-06-02

- Utworzono zadanie follow-up po live smoke panelu `CV Explain`.
- Zakres ograniczono do komunikacji operatorskiej kandydaci vs zaakceptowane rozpoznania.

## 2026-06-02 Implementation

- Dodano test regresyjny `test_candidate_gap_explains_rejected_cards`.
- Zmieniono `operator_explainability.py`, aby krok `Rozpoznanie` ostrzegał przy luce kandydaci/zaakceptowane.
- Dodano konkretny `next_action` dla operatora.

## 2026-06-02 ArUco Consistency Fix

- Dodano testy regresyjne dla kroku ArUco w `CV Explain`.
- Poprawiono licznik markerów: backend liczy teraz `runtime.table.marker_ids`, a nie nieistniejące `markers_detected`.
- Zmieniono stan ArUco: zapamiętana kalibracja bez widocznych markerów pokazuje `warn`, nie `ok`.
- Dodano komunikat `Uzywam ostatniej kalibracji; pokaz markery ArUco`, aby operator rozumiał różnicę między cache kalibracji a aktualną widocznością markerów.
