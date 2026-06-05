# STATE — TASK-PROJECT-MVP-RECOVERY-AUDIT-001

## Status

DONE — audit complete, recovery plan prepared.

## Branch

`codex/project-mvp-recovery-audit-2026-06-05`

## Stan aktualny

Projekt nie jest technicznie w ślepej uliczce. Ostatni smoke `one_card` na Gilded przeszedł jako całość (`3/3`, `accepted_total=3`). Ślepą uliczką stał się proces: autotuning i kalibracja zaczęły dominować nad celem MVP.

## Co zostało zrobione

- Przeanalizowano aktualny stan tasków, dokumentację i ostatnie raporty smoke.
- Sprawdzono ryzyka wokół snapshot-first, Calibration Wizard, autotune i konfiguracji aktywnej talii.
- Zapisano audyt w `analizy/audyt_mvp_recovery_2026-06-05.md`.
- Zapisano plan wykonawczy w `docs/superpowers/plans/2026-06-05-mvp-recovery-plan.md`.
- Potwierdzono, że `app_ar/public/active_decks.json` jest poza zakresem commita.

## Kolejne kroki

1. Wykonać Task 1 z planu recovery: MVP Recovery Lock.
2. Przygotować operator runbook.
3. Uruchomić product-level smoke na Gilded, w tym `three_cards`.
4. Jeśli `three_cards` przejdzie, przejść do recording-ready demo.
5. Jeśli `three_cards` nie przejdzie, sprawdzić manual fallback przed zmianami progów CV.
