# STATE: TASK-CV-AUTOTUNE-LIVE-001

## Status

IN_PROGRESS

## Branch

`task/cv-event-first-plan-001-clarify-autotune-runtime`

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

## Session Status (2026-06-02 Codex Auto Tune forced sampling fix)

Po live obserwacji Michala: klikniecie `Pusta mata` tworzylo log `stage_started`, ale przez kilka minut nie zbieralo probek (`0/3`). Analiza logow pokazala, ze kamera i ArUco dzialaly, ale `stable_for_ms` pozostawal `0.0`, bo `SnapshotGate` w stanie `holding_last_good` nie uruchamia probkowania bez naturalnego ruchu. Codex dodal jawne `SnapshotGate.request_sample()` wywolywane przy `autotune_start` oraz petle dociagania kolejnych snapshotow az do kompletu `3/3`. Live smoke po restarcie backendu potwierdzil `stage_started` + trzy `sample_collected` + `stage_completed` dla `empty` w okolo 5 sekund. Wynik etapu byl poprawnie `FAIL`, bo na pustej macie system nadal widzial false positives (`candidate_count` 1-2, `accepted_count` 1), co jest teraz zapisane w logach i widoczne w UI.

## Session Status (2026-06-02 Codex event-first background diff plan)

Po dyskusji z Michalem o uzyciu pustej maty jako stalej referencji oraz kolejnych stabilnych snapshotow jako referencji zdarzen Codex przygotowal szczegolowy plan implementacyjny: `docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md`. Plan opisuje przejscie z globalnego szukania kart na model `empty_reference` + `previous_stable_snapshot` + ROI z regionow zmian. Kod nie zostal zmieniony w tej sesji planistycznej.

## Session Status (2026-06-02 Event-first plan clarification)

Doprecyzowano architekturę: autotuning jest procedurą kalibracyjną przed sesją, a event-first background diff jest właściwym runtime pipeline podczas nagrywania. Empty reference powstaje w kalibracji i jest używany w runtime. Global card detection po udanej kalibracji nie jest główną ścieżką roboczą.

## Session Status (2026-06-02 Event-first plan amendment 001)

ChatGPT Supervisor dopisał obowiązkową erratę planu: `docs/superpowers/plans/2026-06-02-event-first-background-diff-plan-amendment-001.md`. Errata blokuje implementację do czasu uwzględnienia dwóch zasad: `roi_hints=[]` nie może uruchamiać globalnej detekcji, a walidacja `empty_reference` musi porównywać bieżący pusty frame z referencją przez `BackgroundModel.changed_ratio()` lub równoważny mechanizm, nie `analysis_frame` z samym sobą.

## Session Status (2026-06-02 Event-first amendment merge)

Codex pobrał nowszy stan branchu z GitHuba i scalił erratę bezpośrednio do głównego planu `docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md`. Plan zawiera teraz obowiązkową semantykę `roi_hints is None` vs `roi_hints == []`, test chroniący przed globalnym fallbackiem na pustej liście ROI oraz poprawioną walidację `empty_reference` przez porównanie bieżącej pustej klatki z referencją. Osobny amendment został usunięty, żeby główny plan był jedynym źródłem prawdy.

## Session Status (2026-06-02 Event-first Task 1 Stable Empty Reference)

Codex wykonał Task 1 z planu event-first background diff. `BackgroundModel` potrafi teraz budować stabilną referencję pustej maty przez medianę wielu ramek (`capture_many`) oraz raportować udział zmienionych pikseli względem referencji (`changed_ratio`). Dodano testy jednostkowe zabezpieczające oba kontrakty. Kod nie podłącza jeszcze event-first runtime; to pozostaje zakresem kolejnych tasków.

## Session Status (2026-06-02 Event-first Task 2 ChangeDetector)

Codex wykonał Task 2 z planu event-first background diff. Dodano niezależny moduł `ChangeDetector`, który klasyfikuje regiony zmian między stabilnymi snapshotami jako `added_or_moved` lub `removed`, raportuje `mask_nonzero_ratio`, `global_shift`, `ignored_small_count` i `ignored_large_count`. Moduł nie jest jeszcze podłączony do `SnapshotFirstPipeline`; integracja runtime pozostaje zakresem Task 4.

## Session Status (2026-06-02 Event-first Task 3 SnapshotAnalyzer ROI Hints)

Codex wykonał Task 3 z planu event-first background diff. `SnapshotAnalyzer.analyze()` przyjmuje teraz `roi_hints`; `None` zachowuje dotychczasowy global fallback, pusta lista `[]` oznacza aktywny event-first bez regionów i nie uruchamia globalnej detekcji, a niepusta lista ogranicza detekcję do ROI. Runtime nadal nie przekazuje ROI, bo integracja `ChangeDetector` z `SnapshotFirstPipeline` jest zakresem Task 4.

## Session Status (2026-06-02 Event-first Task 4 Runtime Pipeline Integration)

Codex wykonał Task 4 z planu event-first background diff. `SnapshotFirstPipeline` przyjmuje teraz opcjonalne `change_detector` i `background_model`, pamięta `previous_stable_snapshot`, wylicza regiony zmian po stabilnym snapshocie i przekazuje `roi_hints` do `SnapshotAnalyzer`. `main.py` tworzy `ChangeDetector` i przekazuje go razem z `background_model` do pipeline. Kluczowa semantyka erraty została zabezpieczona testem: brak regionów `added_or_moved` jest przekazywany jako `roi_hints=[]`, nie jako `None`.

## Session Status (2026-06-02 Event-first Task 4 Supervisor fix)

Po review ChatGPT Supervisor z decyzją `CHANGES_REQUESTED` Codex poprawił runtime logikę event-first. `global_shift` nie wraca już do globalnej detekcji i nie nadpisuje `previous_stable_snapshot`. Brak regionów zmian przy istniejących kartach nie jest już interpretowany jako pusty stół; pipeline zachowuje poprzedni layout i nie inkrementuje `empty_snapshot_streak`. Usunięcie kart pozostaje osobnym stanem (`removed_only`) obsługiwanym przez `roi_hints=[]` i dotychczasową ścieżkę potwierdzania pustych snapshotów.

## Session Status (2026-06-02 Event-first Task 5 Autotune Creates Session Reference)

Codex wykonał Task 5 z planu event-first background diff. Etap Auto Tune `Pusta mata` czyści poprzedni `BackgroundModel`, zbiera stabilne snapshoty pustej maty, buduje median `empty_reference` przez `BackgroundModel.capture_many()` i waliduje ostatnią pustą klatkę przez `BackgroundModel.changed_ratio(frame, threshold=20)`. Walidacja nie porównuje już klatki z samą sobą ani nie zależy od globalnego wyniku detekcji kart. Następny bezpieczny task: Task 6 `CV Explain and Diagnostics`.

## Session Status (2026-06-02 Event-first Task 5 Supervisor fix)

Po review ChatGPT Supervisor z decyzją `CHANGES_REQUESTED` Codex zabezpieczył interakcję Task 5 z `hold_previous_state` z Task 4. `Pusta mata` ustawia teraz `empty_reference_capture_active`, dzięki czemu recorder zbiera próbki empty również wtedy, gdy aktywny `ChangeDetector` i istniejący `previous_stable_snapshot` dają `no_change_hold_previous`. Pipeline nadal nie uruchamia `SnapshotAnalyzer` w hold-state, więc nie wraca do globalnej detekcji; zapisuje pustą próbkę `0/0`, a po komplecie ramek wykonuje `capture_many()` i `changed_ratio()`.

## Session Status (2026-06-02 Event-first Task 6 CV Explain and Diagnostics)

Codex wykonał Task 6 z planu event-first background diff. CV Explain pokazuje teraz stan pustej referencji (`inactive`, aktywna, zbieranie `N/3`, warning walidacji) oraz stan change detection: brak regionów zmian, global shift albo liczby regionów `added`/`removed` z `mask ratio`. Pipeline publikuje wyłącznie minimalne pola diagnostyczne potrzebne UI: `background_reference_active`, `empty_reference_capture_active`, `empty_reference_frame_count`; logika detekcji nie została zmieniona.

## Session Status (2026-06-03 Event-first Task 7 Live Smoke)

Stan aktualny: **RED live smoke**. Automatyczna weryfikacja Task 7 przeszła (`47` testów targeted, `300` testów full backend, frontend build PASS), a backend uruchomiony z bieżącego kodu publikuje nowe pola Task 6 (`background_reference_active`, `empty_reference_capture_active`, `empty_reference_frame_count`) oraz kroki CV Explain `empty_reference` i `change_detection`.

Co zostało zrobione: zrestartowano stary backend CV, uruchomiono świeży `SnapshotFirstPipeline` z `TAROTVISION_SNAPSHOT_FIRST=1`, potwierdzono początkowo skalibrowany stół ArUco i wysłano komendę `autotune_start` dla scenariusza `empty`. Po starcie `empty_reference_capture_active=True`, ale etap `Pusta mata` pozostał na `0/3`; `empty_reference_frame_count=0`, `background_reference_active=False`, a w `logs/autotune_sessions/` powstał tylko plik `empty_stage_started`. Metryki `logs/cv_metrics.jsonl` pokazują powtarzalne `snapshot_samples_taken=1.0`, `snapshot_rejected_count=1.0`, `stable_for_ms` spadające do `0.0` oraz później brak widocznych markerów ArUco (`marker_ids: []`).

Kolejne kroki: nie przechodzić do merge ani kolejnego taska runtime. Następny bezpieczny krok to mała diagnoza/fix przed ponowieniem Task 7: ustalić, dlaczego live `Pusta mata` nie zbiera zaakceptowanych snapshotów w obecnych warunkach kamery, mimo aktywnego `empty_reference_capture_active`, i dopiero potem powtórzyć pełny smoke (`empty`, jedna karta, trzy karty, no-change, removal, global shift).

## Session Status (2026-06-03 Event-first Task 7 Snapshot Quality Diagnostics)

Stan aktualny: **Task 7 nadal IN_PROGRESS**. Codex dodał brakującą diagnostykę dla ścieżki `all_samples_rejected`, żeby następny smoke nie kończył się samym `0/3` bez przyczyny. `SnapshotFirstPipeline` publikuje teraz w layout i metrykach powód odrzucenia jakości (`too_dark`, `too_bright`, `low_contrast`, `blurry`) oraz wartości `blur_score`, `brightness`, `contrast`; CV Explain pokazuje ten powód w kroku `Snapshot` i w `next_action`.

Co zostało zrobione: uruchomiono wąski test RED dla brakującego `snapshot_quality_reject_reason`, wdrożono minimalną diagnostykę bez zmiany semantyki akceptacji snapshotów, a następnie powtórzono próbę `autotune_start empty`. W tej lokalnej powtórce `empty` zebrał `3/3` i utworzył `background_reference_active=True`, ale tylko w trybie bez kalibracji ArUco (`table.calibrated=False`, `marker_ids=[]`, `snapshot_analysis_warped=0.0`). To nie zamyka Task 7, bo docelowy smoke wymaga skalibrowanej maty i widocznych markerów.

Kolejne kroki: uruchomić pełny live smoke przy widocznych 4 markerach ArUco. Jeżeli `Pusta mata` znowu zostanie na `0/3`, sprawdzić nowe pola `snapshot_quality_reject_code`, `snapshot_quality_blur_score`, `snapshot_quality_brightness`, `snapshot_quality_contrast` oraz komunikat CV Explain `Snapshot`.

## Kolejne kroki

1. Powtórzyć pełny `Task 7: Live Smoke` przy widocznych 4 markerach ArUco.
2. Jeżeli `Pusta mata` znowu zostanie na `0/3`, użyć nowych metryk jakości snapshotu do decyzji: światło/kontrast/ostrość/ArUco.
3. Manualny live smoke z kamerą pozostaje wymagany dla obecnego `TASK-CV-AUTOTUNE-LIVE-001` przed oznaczeniem go jako `DONE`.
