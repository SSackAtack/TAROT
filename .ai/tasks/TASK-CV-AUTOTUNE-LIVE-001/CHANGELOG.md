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
