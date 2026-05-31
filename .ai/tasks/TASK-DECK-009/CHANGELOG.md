# CHANGELOG — TASK-DECK-009

Wszystkie zmiany wprowadzone w ramach zadania **TASK-DECK-009: WebSocket payload z deck_id + card_id**.

## [1.0.0] - 2026-05-31

### Dodano (Added)
- Wczytywanie manifestu `decks_manifest.json` do cache (`self._decks_cache`) podczas inicjalizacji `StatusStore` w `app_cv/tarotvision/status/status_store.py`.
- Wewnętrzną metodę pomocniczą `_get_deck_id(self, card_name)` w `StatusStore` mapującą prefiks karty na bezpieczny, techniczny identyfikator talii (`deck_id`) z pełnym zestawem odpornych fallbacków ASCII (np. dla RWS, Zodiak, Magic, Gilded, Marchetti, Boski, Światło i Cień) w celu zapewnienia stabilności przy braku dostępu do pliku manifestu w chmurze testowej lub CI.
- Wzbogacanie struktury payloadu dla każdej karty w tablicy `cards` o dodatkowe klucze `"deck_id"` oraz `"card_id"` w metodzie `update_cv_state`.

### Poprawiono (Fixed)
- Uodporniono metodę `update_cv_state` na typy kart inne niż słowniki (`isinstance(card, dict)`). Pozwala to na pełną kompatybilność wsteczną ze starymi testami jednostkowymi (np. w `test_status_store.py`), które przekazywały karty jako listę prostych stringów. Zapobiega to występowaniu błędu `AttributeError: 'str' object has no attribute 'get'`.
- Zaktualizowano frontendowy moduł pozycjonowania Three.js (`app_ar/src/renderer/cardFactory.js`) w metodzie `handleCardData` do pobierania bezpiecznego identyfikatora za pomocą `card_id || name`, dzięki czemu system dynamicznego renderowania 3D jest gotowy na przejście na nowy payload bez zakłócenia dotychczasowego działania.

### Bezpieczeństwo i Kompatybilność Wsteczna (Backward Compatibility & Safety)
- Zachowano pełną zgodność wsteczną protokołu WebSocket v1 — pole `"name"` nadal jest wysyłane bez jakichkolwiek zmian, co gwarantuje stabilność starych widoków przed ukończeniem zadania TASK-DECK-010.
