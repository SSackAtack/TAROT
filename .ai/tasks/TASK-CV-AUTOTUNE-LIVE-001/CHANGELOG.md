# CHANGELOG: TASK-CV-AUTOTUNE-LIVE-001

## 2026-06-02 Codex

- Zatwierdzono istniejące fundamenty offline autotuningu w `.ai/TASKS_INDEX.md`.
- Dodano ostrzeżenie `CV Explain` dla sytuacji, gdy kandydatów kart jest więcej niż zaakceptowanych rozpoznań.
- Dodano `app_cv/tarotvision/autotune_scoring.py`.
- Dodano `app_cv/tarotvision/autotune_profiles.py`.
- Dodano `app_cv/tarotvision/autotune_session.py`.
- Dodano testy jednostkowe dla scoringu, profili i sesji autotuningu.

## 2026-06-02 Codex Task 5

- Rozszerzono `tuning_protocol.py` o `autotune_start`, `autotune_apply`, `autotune_save` i `autotune_cancel`.
- Dodano walidację scenariusza autotuningu: `empty`, `one_card`, `three_cards`.
- Dodano testy parsera dla nowych komend i błędnych payloadów.

## 2026-06-02 Codex Task 6

- Podłączono w `main.py` globalny stan `AutotuneSession` i listę profili kandydackich.
- Dodano `update_autotune_recommendation_from_samples()` jako helper dla przyszłej integracji próbek z pipeline.
- Dodano obsługę `autotune_start`, `autotune_cancel`, `autotune_apply` i `autotune_save` w backendowym handlerze komend.
- Dodano statyczny test, że `main.py` obsługuje autotuning bez ukrytego auto-apply.

## 2026-06-02 Codex Task 7

- Dodano panel `Auto Tune` w Studio z przyciskami scenariuszy `empty`, `one_card`, `three_cards`.
- Podłączono komendy operatorskie `autotune_start`, `autotune_apply` i `autotune_cancel` przez WebSocket.
- Dodano renderowanie stanu i rekomendacji z `operator.calibration.autotune`.
- Dodano style panelu zgodne z istniejącą diagnostyką Studio/CV Explain.
- Rozszerzono statyczny test UI o kontrakt panelu Auto Tune.

## 2026-06-02 Codex Task 8

- Rozszerzono `ProfileStore` o `save_autotune_recommendation()` zapisujące profil z polami `name`, `parameters`, `source`, `score` i `confidence`.
- Dodano `load_parameters()`, aby `profile_apply` obsługiwał zarówno stare surowe profile, jak i nowe profile z metadanymi.
- Podłączono `autotune_save` w `main.py` do zapisu rekomendacji z metadanymi zamiast surowej mapy parametrów.
- Dodano testy zapisu rekomendacji autotuningu, walidacji parametrów i statycznego kontraktu `main.py`.

## 2026-06-02 Codex Task 9

- Dodano do README sekcję `Live Auto Tune` z opisem roli narzędzia operatorskiego, bezpieczną sekwencją pracy i formatem profilu z metadanymi.
- Zaktualizowano `.ai/TASKS_INDEX.md`, aby wpis `TASK-CV-AUTOTUNE-LIVE-001` odzwierciedlał wykonanie Tasków 0-9 i oczekiwanie na pełną weryfikację/live smoke.
- Zaktualizowano stan zadania i kolejny krok dla modelu przejmującego pracę.

## 2026-06-02 Codex Task 10 automatic verification

- Uruchomiono pełny backend test suite.
- Uruchomiono build frontendu `app_ar`.
- Manualny live smoke z fizyczną kamerą pozostawiono jako jawny kolejny krok, bo nie został wykonany w tej sesji.
