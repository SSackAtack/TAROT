# TASK-STUDIO-CV-EXPLAIN-002 — Candidate vs Accepted Explainability

## Cel

Doprecyzować panel `CV Explain`, aby operator rozumiał różnicę między kandydatami kart wykrytymi geometrycznie a kartami zaakceptowanymi przez rozpoznanie.

## Kontekst

Po merge `TASK-STUDIO-CV-EXPLAIN-001` live smoke test pokazał poprawny status ogólny `OK`, ale na stole były 3 karty, a panel raportował 2 zaakceptowane rozpoznania. Obecny komunikat jest technicznie poprawny, ale nie tłumaczy operatorowi, dlaczego jedna karta nie weszła do finalnego layoutu.

## Zakres

- Dodać komunikat w `operator.explainability` dla sytuacji: liczba kandydatów kart > liczba zaakceptowanych rozpoznań.
- Pokazać w Studio czytelną różnicę: kandydaci / zaakceptowane / odrzucone.
- Jeśli dostępna jest diagnostyka recognition threshold lub top match, wykorzystać ją w krótkim komunikacie.
- Zachować fallback dla payloadów bez nowych pól.

## Poza zakresem

- Zmiana algorytmu rozpoznawania.
- Zmiana progów recognition bez osobnej decyzji.
- Nowe biblioteki frontendowe.

## Kryteria akceptacji

- Operator widzi, że np. „Wykryto 3 kandydatów, zaakceptowano 2, 1 wymaga poprawy rozpoznania”.
- Backend i frontend mają testy zabezpieczające nowy przypadek.
- Pełne testy backendu i build frontendu przechodzą.
