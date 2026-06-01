# SUPERVISOR HANDOFF — TASK-CV-SNAPSHOT-LIVE-001

## Decision

REVIEW_REQUESTED

## Goal

Wesprzeć Michała podczas fizycznych testów kamery dla gałęzi `codex/snapshot-first-recognition-hardening` i zebrać użyteczne dane do decyzji, czy snapshot-first po taskach `001-008` jest gotowy do dalszego strojenia, czy wymaga poprawki detekcji/warpu/rozpoznania.

## Context

Aktualna gałąź zawiera:

- snapshot-first jako jedyny runtime CV,
- Unicode-safe loader wzorców,
- analizę snapshotu po warp ArUco,
- metryki porażek detekcji i rozpoznania,
- wieloprofilową detekcję kart,
- opcjonalny model pustej maty,
- offline recognition-aware autotuning,
- kontrakt lokalnego benchmarku snapshot recognition.

Ostatni commit na gałęzi przed testami:

```text
858bd68 test:dodaj-kontrakt-benchmarku-snapshot-recognition
```

## Scope

Gemini ma:

- prowadzić Michała przez testy operatorskie z kamerą i Studio,
- prosić o konkretne obserwacje oraz fragmenty logów/metryk,
- pomagać klasyfikować porażki na etapach: kamera, ArUco warp, motion gate, snapshot quality, quad detection, crop/deskew, ORB recognition, WebSocket/Studio,
- zapisać wyniki w plikach taska po zakończeniu testów,
- rekomendować kolejny krok jako `GREEN`, `YELLOW` albo `RED` dla dalszych prac.

## Out of Scope

Gemini nie powinien bez osobnej zgody Michała:

- zmieniać kodu produkcyjnego,
- robić merge do `master`,
- usuwać plików lub logów,
- commitować fizycznych zdjęć z kamery,
- dodawać Ultralytics/YOLO albo innej zależności ML do runtime,
- przebudowywać architektury snapshot-first.

## Files Allowed to Change

Gemini może aktualizować tylko dokumentację testów:

- `.ai/tasks/TASK-CV-SNAPSHOT-LIVE-001/STATE.md`
- `.ai/tasks/TASK-CV-SNAPSHOT-LIVE-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-SNAPSHOT-LIVE-001/GEMINI_REPORT.md`
- opcjonalnie `docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md` z krótkim `Session Status`

Zmiany w kodzie wymagają osobnej decyzji Michała i nowego taska.

## Test Procedure

1. Upewnij się, że Michał jest na gałęzi:

```powershell
git -C E:\Antigravity\Projekty\TAROT status --short --branch
```

Oczekiwane: `codex/snapshot-first-recognition-hardening`, clean worktree.

2. Uruchom Studio launcher:

```powershell
E:\Antigravity\Projekty\TAROT\start_tarotvision_studio.bat
```

3. W Studio Console sprawdź:

- czy backend CV publikuje WebSocket status,
- czy aktywne talie są widoczne,
- czy warning HUD nie pokazuje krytycznego błędu,
- czy metryki `snapshot_*` pojawiają się po ustaniu ruchu.

4. Testuj minimalną macierz scen:

| Scena | Cel |
|---|---|
| Pusta mata | brak false positives |
| 1 jasna karta na macie | baseline detekcji i rozpoznania |
| 1 ciemna karta na ciemnej macie | główny test multi-profile/background_diff |
| 3 karty stabilnie ułożone | layout i liczba kart |
| Ruch ręką/kartą | motion gate trzyma ostatni dobry layout |
| Po kalibracji ArUco | sprawdzić `snapshot_analysis_warped=1` |

5. Jeśli testujesz model pustej maty:

- najpierw pusta mata,
- wyślij/uruchom `background_capture`,
- połóż kartę,
- obserwuj, czy profil `background_diff` poprawia `snapshot_quads_found`.

## Metrics To Capture

Gemini powinien poprosić Michała o wartości albo fragmenty z payload/logów:

- `snapshot_analysis_warped`
- `snapshot_quads_found`
- `snapshot_recognition_attempts`
- `snapshot_recognition_rejections`
- `snapshot_quality_score`
- `snapshot_analysis_ms`
- `snapshot_rejected_count`
- `layout_publish_count`
- `motion_changed_ratio`
- `stable_for_ms`
- aktywne talie (`operator.active_decks`)
- ostrzeżenia operatora (`warnings`)

## Classification Guide

Interpretuj porażkę tak:

- `snapshot_quads_found = 0`: problem detekcji prostokątów / kontrastu / warpu / tła.
- `snapshot_quads_found > 0` i `recognition_attempts > 0`, ale `recognition_rejections` wysokie: problem cropa, ORB, progu matchingu albo jakości wzorców.
- `snapshot_analysis_warped = 0` mimo widocznych markerów: problem kalibracji ArUco.
- Wysoki `motion_changed_ratio` przy statycznej scenie: kamera/flicker/ekspozycja/motion gate.
- Layout publikuje złą liczbę kart: deduplikacja, próg detekcji albo fałszywe kontury.
- Studio nie aktualizuje statusu: WebSocket/frontend, nie CV.

## Acceptance Criteria

Po testach Gemini ma zostawić raport:

- które sceny przeszły,
- które sceny zawiodły,
- najważniejsze metryki,
- 1-3 przykłady konkretnych objawów,
- rekomendację `GREEN/YELLOW/RED`,
- następny bezpieczny task.

## Tests Required

Testy automatyczne nie są wymagane w tej sesji, jeśli Gemini tylko dokumentuje test operatorski.

Jeśli Gemini zmieni kod, musi uruchomić co najmniej:

```powershell
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

## Reports Required

Gemini ma uzupełnić:

- `.ai/tasks/TASK-CV-SNAPSHOT-LIVE-001/STATE.md`
- `.ai/tasks/TASK-CV-SNAPSHOT-LIVE-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-SNAPSHOT-LIVE-001/GEMINI_REPORT.md`

## Branch

`codex/snapshot-first-recognition-hardening`

## Commit Message

Jeżeli Gemini tylko dokumentuje wyniki:

```text
docs:zapisz-wyniki-live-testu-snapshot-first
```

Jeżeli pojawi się potrzeba kodu, najpierw uzgodnić z Michałem nowy task i zakres.
