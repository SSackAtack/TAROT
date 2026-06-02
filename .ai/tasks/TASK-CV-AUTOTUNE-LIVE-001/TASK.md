# TASK-CV-AUTOTUNE-LIVE-001 — Live Autotuning Recommendation Flow

## Cel

Wdrożyć live autotuning jako bezpieczną rekomendację profilu, która optymalizuje wynik całego pipeline snapshot-first: kandydaci kart, zaakceptowane rozpoznania, recognition score, stabilność, brak false positives i koszt czasowy.

## Plan źródłowy

`docs/superpowers/plans/2026-06-02-final-live-autotuning-implementation-plan.md`

## Zakres

- Diagnostyka różnicy kandydaci kart vs zaakceptowane rozpoznania.
- Scoring live autotuningu.
- Bezpieczne profile kandydackie MVP.
- Stan sesji live autotuningu.
- Docelowo: protokół WebSocket, integracja z backendem, panel Studio, apply/rollback/save.

## Poza zakresem MVP

- Automatyczne nadpisywanie ustawień bez decyzji operatora.
- Zmiana progów ORB/FLANN/RANSAC w pierwszej iteracji.
- Strojenie sprzętowych ustawień kamery bez potwierdzonego readbacku.

## Kryteria akceptacji

- Backend test suite przechodzi w całości.
- Frontend build przechodzi.
- Autotuning nie stosuje rekomendacji bez `autotune_apply`.
- Rekomendacja zawiera score, confidence i konkretne parametry.
- Pusta mata karze false positives.
- Scenariusz 3 kart uwzględnia różnicę kandydaci vs zaakceptowane.
- Operator ma rollback.
- Profil po save jest zapisany w `logs/calibration_profiles/`.
