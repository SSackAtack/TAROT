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

## Kolejne kroki

1. Wykonać live smoke przy scenariuszu 3 kart i potwierdzić czy ostrzeżenie pojawia się dla karty odrzuconej przez rozpoznanie.
2. Kontynuować finalny plan live autotuningu od `Task 2: Autotune scoring model`.
