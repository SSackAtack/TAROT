# STATE: TASK-CV-AUTOTUNE-LIVE-001

## Status

IN_PROGRESS

## Branch

`codex/live-autotuning-foundation`

## Stan aktualny

Codex rozpoczął wdrożenie od fundamentów bezpiecznych dla Gemini do kontynuacji. Zaimplementowano Task 0-9 z finalnego planu oraz wykonano automatyczną część Task 10: pełny backend test suite i build frontendu. Po dodatkowym przeglądzie logiki rozpoznawania kart domknięto brakującą pętlę danych live: snapshot-first przekazuje realne próbki autotuningu, a `SnapshotAnalyzer` publikuje per-candidate recognition diagnostics. Manualny live smoke z fizyczną kamerą i stołem pozostaje do wykonania przez operatora/Gemini w środowisku live.

## Session Status (2026-06-02 Codex)

Commity na branchu:

- `51a0b1f docs: zatwierdz fundament offline autotuningu`
- `4492741 feat: wyjasnij roznice kandydatow i rozpoznan`
- `83ddba6 feat: dodaj scoring live autotuningu`
- `7acd1dd feat: dodaj bezpieczne profile kandydackie autotuningu`
- `325e45c feat: dodaj stan sesji live autotuningu`
- `aec8e7b docs: zapisz status live autotuningu`
- `ddf137c docs: zapisz pelna weryfikacje live autotuningu`
- `057e6aa feat: dodaj protokol komend live autotuningu`
- `096db9e feat: podlacz backend live autotuningu`
- Task 7: panel Auto Tune w Studio wdrożony w bieżącej sesji.
- Task 8: zapis rekomendacji autotuningu jako profil z metadanymi wdrożony w bieżącej sesji.
- Task 9: dokumentacja i runbook operatora wdrożone w bieżącej sesji.
- Task 10 automatyczny: backend tests PASS, frontend build PASS; live smoke NOT RUN w tej sesji.
- Post-Task 10 hardening: podłączono live sample collection z `SnapshotFirstPipeline` do `AutotuneSession`.
- Post-Task 10 hardening: dodano per-candidate recognition diagnostics: top match ranking, `crop_keypoints`, `reject_reason`, `score_margin` i agregowany `recognition_score`.

## Session Status (2026-06-02 Codex glare false-positive hardening)

Po live obserwacji operatora: przy jednej karcie na macie silny odblask byl przepuszczany jako kandydat, a rozpoznawanie dobieralo dla niego najlepszy wzorzec. Codex dodal walidacje cropa kandydata przed ORB, ktora odrzuca gladkie/jasne cropy bez tekstury, krawedzi i sladow granicy karty. `SnapshotAnalyzer` publikuje teraz `candidate_validation_rejections`, `SnapshotFirstPipeline` przekazuje te dane do metryk i probek autotuningu, a `CV Explain` komunikuje przypadek jako odrzucony kandydat wygladajacy jak odblask albo tlo.

## Session Status (2026-06-02 Codex continuation verification)

Codex wznowil prace na czystym branchu `codex/live-autotuning-foundation` i potwierdzil, ze pozostaly zakres taska nie wymaga kolejnej zmiany produkcyjnej przed live smoke. Swieza weryfikacja automatyczna przeszla: pelny backend test suite `267 tests` PASS oraz frontend `npm --prefix app_ar run build` PASS z istniejacymi ostrzezeniami Vite o duzym chunku i nieskutecznym dynamicznym imporcie `textureCache.js`. Status pozostaje `IN_PROGRESS`, bo manualny live smoke z fizyczna kamera nie zostal wykonany w tej sesji.

## Session Status (2026-06-02 Codex Studio sidebar accordion)

Po uwagach Michala o pomieszaniu aktywnych talii z diagnostyka Codex uporzadkowal prawy panel Studio. Sekcje `Transport`, `Kamera`, `Widok`, `Rezyser`, `Audio`, `Aktywne Talie`, `Auto Tune` i `CV Health` sa teraz osobnymi rozwijanymi szufladami z zapamietaniem stanu w `localStorage`. `Auto Tune` zostal oddzielony od wyboru talii, a domyslnie otwarte zostaja sekcje operacyjne: `Transport`, `Auto Tune` i `CV Health`. Manualny live smoke z fizyczna kamera nadal pozostaje wymagany przed zamknieciem taska.

## Session Status (2026-06-02 Codex Auto Tune wizard MVP)

Codex wdrozyl minimalny wizard operatorski dla Auto Tune: scenariusze `empty`, `one_card` i `three_cards` dostaja teraz czytelny `stage_result` (`COLLECTING`/`PASS`/`FAIL`) oraz `next_action` w payloadzie Studio. Dodano jawna komende `autotune_calibrate`, ktora generuje rekomendacje dopiero po komplecie probek, zamiast robic to nieczytelnie automatycznie po samym kliknieciu scenariusza. Dodano trwaly logger sesji `logs/autotune_sessions/autotune_*.json`, zapisujacy start, probki, zakonczenie etapu, rekomendacje, apply, save i cancel. Panel Studio ma teraz przyciski `Skalibruj` oraz `Save Profile`; zapis profilu uzywa automatycznej nazwy `studio_live_YYYYMMDD_HHMMSS`. Manualny live smoke z fizyczna kamera nadal pozostaje wymagany przed oznaczeniem taska jako `DONE`.

## Session Status (2026-06-02 Codex PiP slider cap fix)

Codex usunal twardy limit `560px` z okna PiP w Studio, ktory powodowal, ze suwak rozmiaru wizualnie przestawal powiekszac podglad od okolo 38%, mimo zakresu do 45%. PiP jest teraz limitowany dostepna szerokoscia overlayu (`calc(100% - 56px)`), wiec zakres 20-45% pozostaje uzyteczny bez ryzyka wyjscia poza obszar podgladu. Weryfikacja przegladarkowa potwierdzila wzrost szerokosci z okolo 494px przy 38% do okolo 585px przy 45%.

## Kolejne kroki

1. Wykonać manualny live smoke z kamerą: Auto Tune `empty`, `one_card`, `three_cards`, potem `Apply` i zapis profilu.
2. W live smoke sprawdzić, czy `recognition_score`, `candidate_validation_rejections` oraz `CV Explain` odpowiadają realnej liczbie kart w kadrze, zwlaszcza przy odblasku na pustej czesci maty.
3. Jeśli smoke będzie GREEN, oznaczyć task jako `DONE` i przygotować review/merge branchu `codex/live-autotuning-foundation`.
