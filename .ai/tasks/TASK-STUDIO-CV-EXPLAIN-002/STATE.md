# STATE: TASK-STUDIO-CV-EXPLAIN-002

## Status

DONE

## Branch

`codex/live-autotuning-foundation`

## Stan aktualny

Zadanie zaimplementowane jako pierwszy etap live autotuningu. Panel `CV Explain` pokazuje teraz ostrzeżenie, gdy liczba kandydatów kart jest większa niż liczba zaakceptowanych rozpoznań.

## Session Status (2026-06-02)

Codex zapisał follow-up po obserwacji Michała: panel `CV Explain` poprawnie pokazał status `OK`, ale nie wyjaśniał różnicy między 3 widocznymi kartami na stole i 2 zaakceptowanymi rozpoznaniami.

## Session Status (2026-06-02 Implementation)

Codex dodał test regresyjny dla przypadku 3 kandydatów / 2 zaakceptowane karty i zmienił `operator_explainability.py`: krok `Rozpoznanie` pokazuje teraz wartość `2/3`, stan `warn` oraz komunikat o liczbie odrzuconych kandydatów. `next_action` kieruje operatora do poprawy światła, kontrastu albo separacji karty.

## Session Status (2026-06-02 ArUco Consistency Fix)

Michał wykrył sprzeczność w `CV Explain`: krok ArUco pokazywał zielony status `Stol skalibrowany`, ale wartość `0/4`. Root cause: `operator_explainability.py` czytał nieistniejące pole `markers_detected`, podczas gdy `TableCalibration.status()` publikuje `marker_ids`. Codex dodał testy regresyjne i poprawił logikę tak, aby:

- `marker_ids` były liczone jako bieżący licznik markerów,
- `4/4` + aktywna kalibracja dawało zielony status,
- `0/4` przy zapamiętanej kalibracji dawało żółty status i komunikat o użyciu ostatniej kalibracji.

## Kolejne kroki

1. Wykonać live smoke przy scenariuszu pustej maty i potwierdzić, że ArUco nie pokazuje już zielonego statusu przy `0/4`.
2. Wykonać live smoke przy scenariuszu 3 kart i potwierdzić czy ostrzeżenie pojawia się dla karty odrzuconej przez rozpoznanie.
