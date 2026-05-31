# TASK-DECK-007: Frontend lazy loading tylko aktywnych talii

## Goal
Zastąpić sztywne ładowanie wszystkich 7 talii na starcie frontendu dynamicznym ładowaniem metadanych z manifestów, tak aby system wczytywał tekstury wyłącznie dla talii wskazanych jako aktywne w danej sesji czytania (zmniejszenie obciążenia RAM/GPU).

## Context
Obecnie system ma 7 talii. Ładowanie wszystkich tekstur (7 * 78 = 546 obrazów WebP) na starcie aplikacji znacznie obciąża przeglądarkę. Poprzez odczyt `active_decks.json` oraz `decks_manifest.json` możemy wczytywać tylko 1-3 wybrane talie, zmniejszając narzut o ponad 50-80%.

## Scope
1. Zmodyfikować `app_ar/src/renderer/textureCache.js`:
   - Zastąpić statyczną stałą `cardNames` pustą tablicą modyfikowalną w locie (`export const cardNames = []`).
   - Wewnątrz funkcji `loadTextures` pobrać asynchronicznie pliki `/active_decks.json` oraz `/decks_manifest.json`.
   - Zinterpretować aktywne talie i wygenerować tablicę `cardNames` (metodą modyfikacji "w miejscu", czyli `cardNames.push(...)` po uprzednim wyczyszczeniu), aby zachować referencje w innych modułach.
   - Wczytać wyłącznie tekstury należące do wygenerowanej listy kart.
2. Zaktualizować dokumentację i raporty w katalogu taska.

## Out of Scope
- Nie modyfikować algorytmu CV backendu.
- Nie zmieniać formatu ani logiki WebSocket payload.
- Nie zmieniać panelu operatora ani konsoli Studio.
- Nie usuwać ani nie modyfikować fizycznych plików assetów graficznych w `app_ar/public/karty/`.

## Files Allowed to Change
- `app_ar/src/renderer/textureCache.js`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-DECK-007/*`

## Acceptance Criteria
1. Tablica `cardNames` jest dynamicznie generowana na starcie aplikacji na podstawie `active_decks.json` i `decks_manifest.json`.
2. Aplikacja wczytuje i buforuje wyłącznie tekstury aktywnych talii (np. 234 tekstury dla 3 aktywnych talii, zamiast 546).
3. System Three.js ładuje się poprawnie bez błędów w konsoli deweloperskiej.
4. Testy jednostkowe backendu przechodzą w 100% (171/171 PASS).
5. Frontend buduje się bez błędów za pomocą `npm run build`.

## Tests Required
- `python scripts/validate_decks_manifest.py`
- `cd app_cv && python -m unittest discover tests`
- `cd app_ar && npm run build`

## Reports Required
- `.ai/tasks/TASK-DECK-007/STATE.md`
- `.ai/tasks/TASK-DECK-007/CHANGELOG.md`
- `.ai/tasks/TASK-DECK-007/TEST_REPORT.md`
- `.ai/tasks/TASK-DECK-007/GEMINI_REPORT.md`

## Branch
`task/deck-007-frontend-lazy-loading`

## Commit Message
`feat: implement frontend lazy loading for active decks only`
