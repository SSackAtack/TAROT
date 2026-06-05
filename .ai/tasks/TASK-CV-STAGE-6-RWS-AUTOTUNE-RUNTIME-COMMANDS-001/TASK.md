# TASK-CV-STAGE-6-RWS-AUTOTUNE-RUNTIME-COMMANDS-001

## Cel
Wdrożyć bezpieczny szkielet obsługi komend WebSocket Autotune w runtime backendu, tak aby Studio UI mogło wysyłać komendy:
- `autotune_start`
- `autotune_calibrate`
- `autotune_cancel`
- `autotune_apply`
- `autotune_save`

Backend ma je przyjmować, walidować, utrzymywać minimalny stan sesji autotuningu i zwracać czytelny status operatorski. To ma być etap runtime lifecycle only — jeszcze bez zbierania próbek z pipeline CV.

## Zakres
- Dodanie w `app_cv/main.py` obsługi komend: `autotune_start`, `autotune_calibrate`, `autotune_cancel`, `autotune_apply`, `autotune_save`.
- Integracja minimalnego runtime state dla autotuningu opartego o `AutotuneSession`, `AutotuneSessionLog` oraz `ProfileStore`.
- Dodanie testów jednostkowych / integracyjnych dla lifecycle komend.

## Poza zakresem
- Zmiany w `app_cv/tarotvision/pipelines/snapshot_first.py`.
- Zmiany w `app_cv/tarotvision/snapshot_analyzer.py`.
- Dodawanie `change_detection.py`, ROI, zbieranie próbek z obrazu.
- Zmiany w algorytmach detekcji i dopasowywania kart.
- Zmiany we frontendzie Studio UI.
- Modyfikacja WebSocket payloadu kart.
- Zmiany w OBS overlay.

## Kryteria akceptacji
- Backend nie crashuje po otrzymaniu żadnej z komend autotuningu.
- `autotune_start` tworzy stan sesji i publikuje status `collecting`.
- `autotune_cancel` działa bezpiecznie i czyści stan.
- `autotune_calibrate` bez próbek zwraca kontrolowane ostrzeżenie.
- `autotune_apply` i `autotune_save` bez rekomendacji zwracają kontrolowane ostrzeżenie.
- Studio UI może czytać `calibration.autotune` w stanie `idle`.
- Brak regresji w pętli CV.
