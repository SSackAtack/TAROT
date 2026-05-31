# TASK-DECK-006: Manifest talii i aktywne talie sesji

## Goal
Wprowadzić pierwszy bezpieczny etap architektury obsługi wielu talii na raz: manifest dostępnych talii oraz standard konfiguracji aktywnej sesji czytania, w której operator wybiera 1–3 talie używane w danym czytaniu.

Celem nie jest jeszcze pełna przebudowa CV ani WebSocket payload. Ten task ma przygotować fundament, żeby system nie musiał ładować wszystkich 7 talii, tylko talie wskazane dla bieżącej sesji.

## Context
Aktualnie biblioteka zawiera 7 talii. Dalsze rozszerzanie biblioteki będzie kontynuowane później. Na tym etapie najważniejsze jest ograniczenie obciążenia CPU/GPU/RAM przez ładowanie tylko talii aktywnych w sesji.

Docelowa zasada architektoniczna:

```text
Biblioteka talii = wszystkie dostępne talie
Sesja czytania = wybrane 1–3 talie
Frontend = ładuje tekstury tylko aktywnych talii
Backend CV = docelowo ładuje wzorce tylko aktywnych talii
Payload = docelowo zawiera deck_id + card_id
```

## Scope
W tym tasku wykonaj tylko pierwszy, mały etap.

Do wykonania:

1. Utwórz manifest dostępnych talii jako jedno źródło prawdy:
   - preferowana ścieżka: `app_ar/public/decks_manifest.json`
   - alternatywnie: `biblioteka_talii/decks_manifest.json` + kopia/generowanie do `app_ar/public/`.
2. Manifest ma zawierać wszystkie obecne talie, ich ID techniczne, nazwę wyświetlaną, prefiks plików i liczbę kart.
3. Dodaj prosty plik konfiguracji aktywnej sesji:
   - preferowana ścieżka: `app_ar/public/active_decks.json`
   - domyślnie maksymalnie 3 talie, np. jedna lub trzy wskazane przez Michała.
4. Dodaj walidację pomocniczą w małym skrypcie Python, jeżeli to konieczne:
   - sprawdzenie, czy `active_decks` istnieją w manifeście,
   - sprawdzenie limitu 1–3 talii,
   - sprawdzenie, czy każda talia ma `card_count=78` i `has_back=true`.
5. Zaktualizuj dokumentację taska i raporty.

## Out of Scope
Nie rób jeszcze pełnego refaktoru runtime.

Nie zmieniaj w tym tasku:

- algorytmu CV,
- WebSocket payload,
- `app_cv/main.py`, chyba że wyłącznie do odczytu konfiguracji bez zmiany zachowania produkcyjnego,
- dużej logiki `textureCache.js`, jeśli wymagałaby przebudowy ładowania,
- UI konsoli Studio,
- assetów talii,
- `scripts/process_scans.py`,
- `scripts/prepare_deck.py`, chyba że dodajesz bardzo małą walidację manifestu.

Nie usuwaj żadnej talii ani żadnego assetu.

## Files Allowed to Change
Preferowany limit: 1–3 pliki produkcyjne + dokumentacja `.ai`.

Dozwolone:

- `app_ar/public/decks_manifest.json`
- `app_ar/public/active_decks.json`
- opcjonalnie `scripts/validate_decks_manifest.py`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-DECK-006/*`

Jeżeli Gemini uzna, że musi zmienić więcej plików produkcyjnych albo dotknąć backendu i frontendu jednocześnie, ma zatrzymać pracę i poprosić o Human Override.

## Manifest Requirements
Manifest powinien mieć stabilny, prosty format, np.:

```json
{
  "version": 1,
  "default_max_active_decks": 3,
  "decks": [
    {
      "id": "zodiak",
      "display_name": "Zodiak",
      "prefix": "Zodiak",
      "card_count": 78,
      "has_back": true,
      "ar_path_template": "/karty/Zodiak_{index}.webp",
      "back_texture": "/karty/Zodiak_back.webp",
      "cv_path": "biblioteka_talii/zodiak/produkcja/wzorce_cv"
    }
  ]
}
```

`active_decks.json` powinien mieć format:

```json
{
  "version": 1,
  "active_decks": ["zodiak"]
}
```

Dopuszczalny limit aktywnych talii: minimum 1, maksimum 3.

## Acceptance Criteria
1. Manifest zawiera wszystkie 7 obecnych talii.
2. Każda talia ma unikalne `id`.
3. Każda talia ma `prefix`, `card_count`, `has_back`, `ar_path_template`, `back_texture`, `cv_path`.
4. `active_decks.json` zawiera od 1 do 3 talii.
5. Wszystkie aktywne talie istnieją w manifeście.
6. Nie preloadujemy jeszcze wszystkiego inaczej — ten task tylko przygotowuje dane wejściowe pod kolejny etap.
7. Brak zmian w assetach.
8. Brak zmian w WebSocket payload.
9. Brak regresji testów backendu.

## Tests Required
Minimum:

```bash
python -m unittest discover app_cv/tests
```

Jeżeli dodasz skrypt walidacyjny:

```bash
python scripts/validate_decks_manifest.py
```

Jeżeli zmienisz cokolwiek w `app_ar/src`:

```bash
cd app_ar && npm run build
```

Jeżeli zmienisz tylko JSON w `app_ar/public`, build frontendu nie jest obowiązkowy, ale zalecany.

## Reports Required
Utwórz lub zaktualizuj:

- `.ai/tasks/TASK-DECK-006/STATE.md`
- `.ai/tasks/TASK-DECK-006/CHANGELOG.md`
- `.ai/tasks/TASK-DECK-006/TEST_REPORT.md`
- `.ai/tasks/TASK-DECK-006/GEMINI_REPORT.md`

Raport Gemini musi zawierać:

- listę 7 talii z manifestu,
- listę aktywnych talii,
- wynik walidacji 1–3 aktywne talie,
- wynik testów,
- potwierdzenie, że nie zmieniono assetów ani WebSocket payload.

## Branch
`task/deck-006-active-session-manifest`

## Commit Message
`feat: add deck manifest and active session deck config`

## Next Tasks Roadmap
Nie realizować w tym tasku, tylko wpisać jako przyszłą roadmapę:

- TASK-DECK-007 — frontend lazy loading tylko aktywnych talii,
- TASK-DECK-008 — backend CV registry tylko dla aktywnych talii,
- TASK-DECK-009 — WebSocket payload z `deck_id + card_id`,
- TASK-DECK-010 — UI wyboru 1–3 talii w Studio / launcherze.
