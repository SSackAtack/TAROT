# STATE — TASK-DECK-006

## Status
TODO / Awaiting Gemini

## Owner
Gemini

## Supervisor
ChatGPT Supervisor

## Created
2026-05-31

## Current State
Zadanie zostało przygotowane jako mały, bezpieczny etap architektury multi-deck. Celem jest dodanie manifestu talii oraz konfiguracji aktywnych talii sesji, bez przebudowy runtime, CV, WebSocket i UI.

## What Was Done By ChatGPT Supervisor
- Dodano wpis `TASK-DECK-006` do `.ai/TASKS_INDEX.md`.
- Utworzono `.ai/tasks/TASK-DECK-006/TASK.md` z pełnym handoffem dla Gemini.
- Utworzono ten plik statusu.

## What Gemini Should Do Next
1. Wykonać `git pull` na lokalnym repo.
2. Przeczytać `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`.
3. Przeczytać `.ai/tasks/TASK-DECK-006/TASK.md`.
4. Utworzyć branch `task/deck-006-active-session-manifest`.
5. Wykonać wyłącznie mały zakres taska: manifest talii + aktywne talie sesji.
6. Zostawić raporty w katalogu taska.

## Blockers
Brak na starcie.

## Notes
Nie robić jeszcze pełnego lazy loadingu, backend CV registry ani WebSocket payload z `deck_id`. To są kolejne taski po zatwierdzeniu manifestu.
