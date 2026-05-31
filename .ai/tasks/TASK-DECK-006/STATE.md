# STATE — TASK-DECK-006

## Status
APPROVED

## Owner
Gemini

## Supervisor
ChatGPT Supervisor

## Created
2026-05-31

## Current State
Zadanie zostało pomyślnie zakończone i formalnie zatwierdzone przez ChatGPT Supervisor (GREEN LIGHT). Rekomendowany jest merge brancha `task/deck-006-active-session-manifest` do `master`. W celu uodpornienia systemu na przyszłe etapy wdrożenia, ID talii Światło i Cień zostało zrefaktoryzowane z polskimi znakami diakrytycznymi na bezpieczny alias ASCII `swiatlo_i_cien`.

## What Was Done By Gemini
1. Utworzono branch roboczy `task/deck-006-active-session-manifest`.
2. Opracowano centralny manifest talii `app_ar/public/decks_manifest.json` zawierający 7 talii: Rider-Waite-Smith, Zodiak, Magic, Gilded, Marchetti, Boski oraz Światło i Cień.
3. Utworzono plik konfiguracji aktywnego czytania `app_ar/public/active_decks.json` z domyślnie wybranymi 3 taliami (Rider-Waite-Smith, Zodiak, Magic).
4. Napisano odporny skrypt automatycznej walidacji `scripts/validate_decks_manifest.py`, sprawdzający poprawność struktury manifestu, limit aktywnych talii (1–3), unikalność ID, obecność wzorców CV oraz fizyczne istnienie rewersów i przykładowych plików AR na dysku.
5. Pomyślnie przeprowadzono weryfikację dymną i walidację automatyczną (wszystkie warunki OK).
6. Uruchomiono testy jednostkowe backendu (171/171 PASS) oraz build frontendu (Vite build: PASS).
7. Zaktualizowano indeks zadań w `.ai/TASKS_INDEX.md` i przygotowano komplet raportów.
8. [Refaktor Hardening]: Zmieniono ID talii Światło i Cień z `"światło_i_cień"` na ASCII `"swiatlo_i_cien"` zgodnie z zaleceniem ChatGPT Supervisor, zachowując pełne wsparcie dla lokalnych ścieżek z polskimi znakami diakrytycznymi.

## Blockers
Brak.

## Notes
Wszystkie assety graficzne, logika algorytmu CV oraz WebSocket payload pozostały nienaruszone (są w pełni gotowe pod kolejne etapy integracji w TASK-DECK-007+).
