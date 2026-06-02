# STATE: TASK-STUDIO-CV-EXPLAIN-001

## Status

APPROVED

## Branch

`master`

## Stan aktualny

Dodano backendowy builder `operator.explainability` oraz panel `CV Explain` w Studio. Panel pokazuje status etapów pipeline i jeden następny krok operatora.

## Session Status (2026-06-01)

Codex wdrożył zaakceptowany wariant B po visual companion: prowadzona diagnostyka z przyczynami i następnym krokiem.

## Session Status (2026-06-02)

Codex przygotował zadanie do merge: odświeżono lokalne zależności Python w `C:\tmp\tarot_pydeps`, powtórzono pełną weryfikację backendu i build frontendu. Wynik: backend 234/234 PASS, Vite build PASS. Zadanie zatwierdzone do scalenia z `master`.

## Session Status (2026-06-02 Live Smoke)

Michał wykonał live smoke test po merge na `master`: kamera działa, ArUco kalibruje stół, snapshot przechodzi w `holding_last_good`, kandydaci kart są wykrywani, a panel `CV Explain` pokazuje status `OK` i następny krok „Można prowadzić sesję.” Zaobserwowano nieblokującą lukę diagnostyczną: na stole były 3 karty, panel raportował 2 zaakceptowane rozpoznania. Follow-up zapisano jako `TASK-STUDIO-CV-EXPLAIN-002`.

## Kolejne kroki

1. Wykonać `TASK-STUDIO-CV-EXPLAIN-002`, aby panel jasno tłumaczył różnicę między liczbą kandydatów i zaakceptowanych kart.
2. Kontynuować kolejne małe zadania stabilizacyjne zgodnie z `.ai/TASKS_INDEX.md`.
