# TASK-STUDIO-CV-EXPLAIN-001 — Operator CV Explainability

## Cel

Dodać w Studio panel `CV Explain`, który pokazuje operatorowi uporządkowaną przyczynę problemu CV i konkretny następny krok.

## Zakres

- Backend publikuje `operator.explainability` w payloadzie statusu.
- Studio renderuje panel `CV Explain` pod `Diagnostyka CV Health`.
- Panel ma fallback dla starszego payloadu bez `operator.explainability`.
- Testy zabezpieczają builder backendowy, payload i obecność panelu.

## Pliki do zmiany

- `app_cv/tarotvision/operator_explainability.py`
- `app_cv/tarotvision/pipelines/snapshot_first.py`
- `app_cv/main.py`
- `app_cv/tests/test_operator_explainability.py`
- `app_cv/tests/test_status_store.py`
- `app_cv/tests/test_main_static_audit.py`
- `app_cv/tests/test_camera_controls_static.py`
- `app_ar/src/studio/studioConsole.js`
- `app_ar/studio.css`

## Poza zakresem

- Zmiana algorytmu rozpoznawania kart.
- Nowe biblioteki frontendowe.
- Zmiana publicznego protokołu komend WebSocket.

## Kryteria akceptacji

- Backend generuje `severity`, `steps` i `next_action`.
- Studio pokazuje listę etapów oraz boks `Następny krok`.
- Pełne testy backendu i build frontendu przechodzą.
