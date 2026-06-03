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

## Session Status (2026-06-03 Event-first Task 7 Empty Layout Hold Fix)

Stan aktualny: **Task 7 nadal IN_PROGRESS, ale główny błąd UI z pustej maty został naprawiony**. Live smoke przy ustawionej kamerze i widocznych markerach ArUco (`table.calibrated=True`, `marker_ids=[10,11,12,13]`) pokazał, że etap `Pusta mata` zbiera `3/3` i tworzy `background_reference_active=True`, ale w każdej próbce nadal występują false positives na pustej macie. Przed poprawką te fałszywe karty były publikowane do layoutu i pojawiały się w scenie Studio mimo pustego obszaru ArUco.

Co zostało zrobione: `autotune_start empty` czyści teraz `last_snapshot_cards` i licznik pustych snapshotów. `SnapshotFirstPipeline` podczas `empty_reference_capture_active` nadal zapisuje false positives do próbek Auto Tune, ale nie publikuje ich do layoutu (`cards=[]`, `detected=false`, metryka `empty_reference_false_positive_hold=1`). Realny retest po restarcie backendu potwierdził: `background_reference_active=True`, `background_reference_validation_ratio=0.01`, `background_reference_validation_warning=0`, `cards_len=0`, a log sesji nadal uczciwie pokazuje `stage_result=FAIL` przez false positives.

Kolejne kroki: nie kontynuować do scenariuszy jedna/trzy karty jako pełny green smoke, dopóki `empty` ma false positives. Następny mały task powinien zmniejszyć false positives na pustej macie po warpie ArUco; aktualne próbki empty miały `candidate_count` 3, 2, 2 oraz `accepted_count` 2, 1, 1.

## Session Status (2026-06-03 Event-first Empty Reference Status Fix)

Stan aktualny: **Task 7 nadal IN_PROGRESS, ale etap `Pusta mata` nie jest już blokowany przez stary detektor**. Po decyzji Michala rozdzielono status utworzenia `empty_reference` od testu false positives starego detektora. Komplet próbek `empty` i poprawna walidacja tła oznaczają `empty_reference_status=PASS`; false positives są widoczne jako warning diagnostyczny, ale nie blokują referencji i nie trafiają do layoutu.

Co zostało zrobione: `AutotuneSession` publikuje `empty_reference_status`, traktuje false positives w scenariuszu `empty` jako diagnostykę (`diagnostics.legacy_detector_false_positive`, `diagnostics.false_positive_count`) i nie ustawia przez nie `stage_result=FAIL`. Backend dopisuje ostrzeżenie operatorskie, że referencja pustej maty jest OK, a stary detektor widzi false positives tylko diagnostycznie. Realny retest z kamerą i ArUco potwierdził `background_reference_active=True`, `background_reference_validation_warning=0`, `detected=false`, `cards_len=0` oraz diagnostykę `false_positive_count=7`.

Kolejne kroki: kontynuować pełny Task 7 Live Smoke na event-first: jedna karta, trzy karty, no-change, usunięcie karty i global shift. Redukcja false positives starego detektora na pustej macie jest osobnym późniejszym taskiem (`TASK-CV-LEGACY-DETECTOR-EMPTY-FP-001`) i nie powinna blokować `empty_reference`.

## Session Status (2026-06-03 Event-first Previous Stable Seed Fix)

Stan aktualny: **Task 7 nadal IN_PROGRESS, a stabilna pusta mata po `empty_reference` nie wraca już do globalnego skanu**. Podczas przygotowania scenariusza jednej karty live payload pokazał `cards_len=2` po zakończonym `Pusta mata PASS`. Analiza logów wykazała, że `empty_reference` była aktywna, ale `previous_stable_snapshot` nie został ustawiony przy finalizacji pustej referencji, więc kolejny snapshot mógł przejść przez `roi_hints=None` i globalny `SnapshotAnalyzer`.

Co zostało zrobione: po `BackgroundModel.capture_many()` i walidacji `changed_ratio()` pipeline ustawia `update_previous_stable_snapshot=True`, dzięki czemu bieżąca pusta klatka staje się pierwszą referencją zdarzeń. Dodano test regresyjny, który najpierw failował na `previous_stable_snapshot is None`, a po poprawce przechodzi. Live retest po restarcie backendu potwierdził `empty_reference_status=PASS`, `background_reference_active=True`, `background_reference_validation_warning=0`, a przez 53 kolejne payloady `post_max_cards_len=0` i `post_any_detected=false`.

Kolejne kroki: teraz można kontynuować właściwy Task 7 od realnego dodania jednej karty na obszar ArUco.

## Session Status (2026-06-03 Event-first Task 7 One Card Smoke)

Stan aktualny: **Task 7 nadal IN_PROGRESS; scenariusz jednej karty przeszedł funkcjonalnie, ale diagnostyka change detection wymaga obserwacji w kolejnych krokach**. Po realnym położeniu jednej karty na obszarze ArUco backend utrzymał `background_reference_active=True`, stół pozostał skalibrowany (`marker_ids=[10,11,12,13]`), a layout opublikował dokładnie jedną kartę.

Co zostało zaobserwowane: payload live pokazał `detected=true`, `cards_len=1`, karta `Gilded_03`, `confidence=0.4`, `orientation=reversed`, `snapshot_analysis_warped=1.0` w metrykach. Pełny layout nie został zanieczyszczony dodatkowymi false positives. Metryki rolling wskazują jednak mieszany sygnał change detection: `change_added_count=0.333`, `change_region_count=0.333`, `change_global_shift=0.667`, `change_mask_ratio=0.467`. To oznacza, że funkcjonalnie karta została wykryta, ale część próbek była klasyfikowana jako global shift.

Kolejne kroki: kontynuować smoke do trzech kart, a potem szczególnie sprawdzić no-change i removal. Jeśli global shift będzie stale pojawiał się przy normalnym dodawaniu kart, zapisać osobny mały task diagnostyczny dla progu/global-shift klasyfikacji w `ChangeDetector`, bez strojenia starego detektora pustej maty.

## Session Status (2026-06-03 Event-first Task 7 Three Cards Smoke)

Stan aktualny: **RED dla scenariusza trzech kart**. Po dołożeniu kart do trzech fizycznych kart na macie backend przez dwa odczyty live nie opublikował układu trzech kart. Maksymalny zaobserwowany layout miał `cards_len=1`.

Co zostało zaobserwowane: `table.calibrated=True`, `marker_ids=[10,11,12,13]`, `background_reference_active=True`, `detected=True`, ale layout zawierał tylko `Gilded_50` (`confidence=0.5`, `orientation=upright`). Metryki z `cv_metrics.jsonl` pokazują, że event-first widział wiele regionów zmian (`change_region_count=3.5`, `change_added_count=3.5`, `change_mask_ratio=0.311`), więc problem nie wygląda na brak detekcji zmiany. Wąskim gardłem jest downstream analiza/rozpoznanie ROI: `snapshot_quads_found=10.111`, `snapshot_recognition_attempts=6.222`, `snapshot_recognition_rejections=4.778`, `snapshot_candidate_validation_rejections=3.889`, a finalnie `snapshot_detection_quads_final=0.444` i `cards_len=1`.

Kolejne kroki: zatrzymać Task 7 przed oznaczeniem jako green. Następny mały task powinien zbadać, dlaczego przy wielu regionach event-first rozpoznaje tylko jedną z trzech kart: ROI sizing/merge, walidacja kandydatów albo rozpoznawanie wielu ROI. Nie wracać do strojenia starego detektora pustej maty.

Decyzja Michala po restarcie procesu: **opcja 1**. Nie odtwarzać teraz smoke od zera. Wcześniejsze wyniki `Pusta mata` i `1 karta` pozostają reprezentatywne, a `3 karty` zostaje zapisane jako RED na podstawie danych sprzed restartu.

## Session Status (2026-06-03 Event-first Multi-ROI Diagnostics)

Stan aktualny: **Task diagnostyczny wykonany; Task 7 nadal RED dla trzech kart do ponownego smoke po diagnostyce**. Zgodnie z review Supervisor nie zmieniano progów `ChangeDetector`, ArUco, pustej referencji, ORB ani Studio UI.

Co zostało zrobione: `SnapshotAnalyzer` publikuje teraz diagnostykę per ROI dla `roi_hints`: bbox, powierzchnię ROI, liczbę quadów, liczbę kandydatów po walidacji, odrzucenia walidacji, próby rozpoznania, odrzucenia rozpoznania, zaakceptowane karty i powody odrzuceń. Dodano agregaty `roi_with_quads_count`, `roi_with_accepted_card_count`, `accepted_cards_before_dedup`, `accepted_cards_after_dedup`. To pozwoli w kolejnym smoke rozróżnić, czy trzy karty odpadają na ROI, walidacji cropa, ORB recognition czy późniejszym składaniu layoutu.

Kolejne kroki: po ponownej kalibracji pustej maty uruchomić smoke trzech kart i odczytać nowe pola `roi_diagnostics`. Dopiero na podstawie tej diagnostyki wybrać następny fix.

## Session Status (2026-06-03 ROI Diagnostics Pipeline Passthrough)

Stan aktualny: **mały fix diagnostyczny dodany; Task 7 nadal RED do ponownego smoke trzech kart**. Podczas próby odczytu live po commicie `09db040` okazało się, że `SnapshotAnalyzer` generuje `roi_diagnostics`, ale `SnapshotFirstPipeline` publikuje tylko stare skalarne metryki, więc pola ROI nie były widoczne w WebSocket payload.

Co zostało zrobione: `SnapshotFirstPipeline` kopiuje teraz wymagane pola diagnostyki ROI z `SnapshotAnalyzer.diagnostics` do `metrics_snapshot` publikowanego przez `status_store.update_cv_state`. Nie zmieniano logiki detekcji, progów, ORB, ArUco, pustej referencji ani Studio UI.

Weryfikacja: test kontraktowy najpierw RED z `KeyError: 'roi_count'`, potem PASS po passthrough. Targeted suite `test_snapshot_analyzer + test_pipelines_contract + test_operator_explainability + test_main_static_audit` PASS (`55`).

Kolejne kroki: po commicie i pushu powtórzyć krótki cykl live: `Pusta mata 3/3`, następnie `3 karty`, i odczytać `roi_diagnostics` z payloadu WebSocket.

## Kolejne kroki

1. Kontynuować pełny `Task 7: Live Smoke` przy widocznych 4 markerach ArUco: jedna karta, trzy karty, no-change, removal i global shift.
2. Traktować false positives starego detektora podczas `Pusta mata` jako warning diagnostyczny, nie jako bloker referencji tła.
3. Osobny późniejszy task: `TASK-CV-LEGACY-DETECTOR-EMPTY-FP-001`, jeżeli po smoke nadal warto ograniczać false positives starego detektora.

## 2026-06-03 Event-first 3-card ROI diagnostic smoke

### Input state
- backend commit: branch HEAD `e19b866`; ostatni commit kodu backendu `991ba87`
- table.calibrated: `true`
- marker_ids: `[10, 11, 12, 13]`
- empty_reference_status: `PASS`
- background_reference_active: `true`
- background_reference_validation_warning: `0.0`

### 3-card result
- cards_len: `2` maksymalnie w 154 payloadach
- detected: `true`
- change_region_count: `3.706`
- change_added_count: `3.529`
- change_removed_count: `0.176`
- change_mask_ratio: `0.088`
- snapshot_quads_found: `15.923`
- snapshot_recognition_attempts: `9.154`
- snapshot_recognition_rejections: `8.308`
- snapshot_candidate_validation_rejections: `6.769`
- snapshot_detection_quads_final: `0.154`
- roi_count: `5`
- roi_with_quads_count: `5`
- roi_with_accepted_card_count: `1`
- accepted_cards_before_dedup: `2`
- accepted_cards_after_dedup: `2`

### ROI diagnostics
- ROI 0: bbox `[180, 92, 228, 358]`, area `81624`, quads `7`, candidates after validation `5`, validation rejections `2`, recognition attempts `5`, recognition rejections `3`, accepted cards `2`, reject reasons: `not_enough_good_matches=1`, `smooth_low_texture=2`, `not_enough_crop_descriptors=2`.
- ROI 1: bbox `[151, 8, 117, 144]`, area `16848`, quads `10`, candidates after validation `1`, validation rejections `9`, recognition attempts `1`, recognition rejections `1`, accepted cards `0`, reject reasons: `smooth_low_texture=9`, `not_enough_crop_descriptors=1`.
- ROI 2: bbox `[257, 23, 91, 82]`, area `7462`, quads `9`, candidates after validation `5`, validation rejections `4`, recognition attempts `5`, recognition rejections `5`, accepted cards `0`, reject reasons: `not_enough_good_matches=1`, `not_enough_crop_descriptors=4`, `smooth_low_texture=4`.
- ROI 3: bbox `[606, 476, 90, 70]`, area `6300`, quads `10`, candidates after validation `8`, validation rejections `2`, recognition attempts `8`, recognition rejections `8`, accepted cards `0`, reject reasons: `not_enough_crop_descriptors=7`, `not_enough_good_matches=1`, `smooth_low_texture=2`.
- ROI 4: bbox `[554, 570, 82, 69]`, area `5658`, quads `4`, candidates after validation `1`, validation rejections `3`, recognition attempts `1`, recognition rejections `1`, accepted cards `0`, reject reasons: `not_enough_crop_descriptors=1`, `smooth_low_texture=3`.

### Interpretation
Wybór: **recognition issue**.

ROI passthrough działa i nie jest to brak regionów: `roi_count=5`, `roi_with_quads_count=5`. Walidacja cropów odrzuca część kandydatów, ale przez rozpoznanie nadal przechodzi dużo prób (`snapshot_recognition_attempts=9.154`, suma prób ROI w wybranym payloadzie `20`), z bardzo wysokim odsetkiem odrzuceń (`snapshot_recognition_rejections=8.308`, suma ROI `18`). Dominujące powody to `not_enough_crop_descriptors`, `smooth_low_texture` i `not_enough_good_matches`, więc najbliższy problem jest w jakości cropów/rozpoznawaniu ORB w ROI, a nie w deduplikacji ani publikacji layoutu.

### Required next action
Utworzyć mały task naprawczy `TASK-CV-ROI-RECOGNITION-CROP-QUALITY-001`: zapisać diagnostyczne cropy/kontekst rozpoznawania dla ROI z `not_enough_crop_descriptors` i `not_enough_good_matches`, a następnie poprawić jakość cropu/normalizacji przekazywanej do ORB bez zmiany progów `ChangeDetector`, ArUco, pustej referencji ani starego detektora pustej maty.

## TASK-CV-ROI-RECOGNITION-CROP-QUALITY-001

### Summary
Dodano crop-level diagnostics w `SnapshotAnalyzer`, aby następny live smoke trzech kart mógł powiązać każde odrzucenie rozpoznania lub walidacji z konkretnym ROI i konkretnym kandydatem. Diagnostyka nie zmienia decyzji detekcji, walidacji, ORB ani publikacji layoutu.

Nowe pola:
- globalnie: `diagnostics.crop_diagnostics`
- per ROI: `roi_diagnostics[].roi_candidate_diagnostics`
- per kandydat: `roi_index`, `candidate_index`, `crop_width`, `crop_height`, `crop_keypoints`, `descriptor_count`, `reject_reason`, `candidate_validation`, `recognition_attempt_result`, `top_matches`, `score_margin`, `recognition_score`

### Evidence
Opisane są teraz trzy krytyczne ścieżki odrzuceń z RED smoke:
- `not_enough_crop_descriptors`: diagnostyka zawiera rozmiar cropu, ROI, indeks kandydata, `crop_keypoints`/`descriptor_count` i wynik próby rozpoznania.
- `smooth_low_texture`: diagnostyka zawiera kontekst walidacji cropa, w tym `candidate_validation.accepted=false` i `candidate_validation.reject_reason`.
- `not_enough_good_matches`: diagnostyka wiąże odrzucenie z konkretnym ROI oraz zachowuje `top_matches`/`match_count`, jeżeli `RecognitionDebug` je dostarcza.

### Tests
- `python -m unittest app_cv.tests.test_snapshot_analyzer.SnapshotAnalyzerTest.test_roi_crop_diagnostics_include_descriptor_rejection_context app_cv.tests.test_snapshot_analyzer.SnapshotAnalyzerTest.test_roi_crop_diagnostics_include_smooth_validation_context app_cv.tests.test_snapshot_analyzer.SnapshotAnalyzerTest.test_roi_crop_diagnostics_map_rejections_to_specific_roi -v` => RED przed implementacją (`KeyError: 'crop_diagnostics'`), PASS po implementacji.
- `python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_card_candidate_validation -v` => PASS, 19 testów.
- `python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability app_cv.tests.test_main_static_audit -v` => PASS, 58 testów.
- `python -B -m py_compile app_cv\tarotvision\snapshot_analyzer.py` => PASS.

### Decision
To był task diagnostyczny. Nie dodano fixu jakości cropu, ponieważ bez nowego live smoke z `crop_diagnostics` nie ma jeszcze dowodu, czy naprawa powinna dotyczyć normalizacji kontrastu, paddingu ROI, deskew/resize, minimalnego rozmiaru cropu czy walidacji `smooth_low_texture`.

### Required next action
Powtórzyć krótki live smoke `Pusta mata 3/3 -> 3 karty` i odczytać nowe `crop_diagnostics` dla odrzuceń. Dopiero po tych danych wybrać jeden mały fix: crop normalization, ROI padding, deskew/resize albo candidate validation.

## TASK-CV-LIVE-FIXTURE-CAPTURE-001

### Summary
Dodano lokalny zapis fixture live smoke do `logs/live_fixtures/`. Mechanizm jest domyślnie wyłączony i aktywuje się dopiero po ustawieniu `TAROTVISION_CAPTURE_LIVE_FIXTURES=1`. Fixture zapisuje reprezentatywną próbkę scenariusza: `raw_frame.png`, `analysis_frame.png`, opcjonalnie `empty_reference.png`, `metrics.json`, `payload.json`, `roi_diagnostics.json` oraz wspólny `manifest.json`.

### Scope
Zmienione pliki:
- `app_cv/tarotvision/live_fixture_capture.py`
- `app_cv/tests/test_live_fixture_capture.py`
- `app_cv/tarotvision/pipelines/snapshot_first.py`
- `app_cv/tests/test_pipelines_contract.py`
- `app_cv/main.py`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`

Nie zmieniano `.gitignore`, bo repo ignoruje już cały katalog `logs/`.

### Tests
- `python -m unittest app_cv.tests.test_live_fixture_capture -v` => PASS, 4 testy.
- `python -m unittest app_cv.tests.test_snapshot_analyzer app_cv.tests.test_pipelines_contract app_cv.tests.test_operator_explainability app_cv.tests.test_main_static_audit -v` => PASS, 60 testów.
- `python -B -m py_compile app_cv\tarotvision\live_fixture_capture.py app_cv\tarotvision\pipelines\snapshot_first.py app_cv\main.py` => PASS.
- `cd app_cv; python -m unittest discover tests -v` => PASS, 314 testów.

### Manual verification
NOT_RUN. Nie uruchamiano backendu live ani fizycznego smoke w tej sesji; poprawność zapisu plików została zweryfikowana testem jednostkowym na tymczasowym katalogu.

### Next action
Uruchomić backend z `TAROTVISION_CAPTURE_LIVE_FIXTURES=1` i `TAROTVISION_LIVE_FIXTURE_NAME=event_first_current_debug`, zebrać fixture `empty`, `one_card`, `three_cards`, a potem użyć ich w replay/debug tasku dla `TASK-CV-ROI-RECOGNITION-CROP-QUALITY-001`.

## 2026-06-03 Live fixture filename disambiguation

### Summary
Podczas ręcznego zbierania fixture wykryto, że identyczne nazwy `raw_frame.png` i `analysis_frame.png` w każdym folderze scenariusza są zbyt łatwe do pomylenia przy ręcznej kontroli i kopiowaniu snapshotów. Zmieniono nazwy obrazów na scenariuszowe:
- `empty`: `raw_frame_0.png`, `analysis_frame_0.png`, `empty_reference_0.png`
- `one_card`: `raw_frame_1.png`, `analysis_frame_1.png`, `empty_reference_1.png`
- `three_cards`: `raw_frame_3.png`, `analysis_frame_3.png`, `empty_reference_3.png`

### Tests
- `cd app_cv; python -m unittest tests.test_live_fixture_capture -v` => PASS, 5 testów.
- `cd app_cv; python -m unittest tests.test_live_fixture_capture tests.test_pipelines_contract -v` => PASS, 24 testy.
- `cd app_cv; python -B -m py_compile tarotvision\live_fixture_capture.py tarotvision\pipelines\snapshot_first.py main.py` => PASS.

### Snapshot cleanup
Usunięto wszystkie lokalne wcześniejsze snapshoty z `logs/live_fixtures/`. Następna procedura live capture ma zacząć od pustego katalogu i nowych nazw obrazów.

### Next action
Zebrać od zera `empty`, `one_card`, `three_cards`; po każdym scenariuszu zweryfikować fizycznie zapisany obraz i dopiero po potwierdzeniu przejść dalej.

## 2026-06-03 Live fixture overwrite guard and verified capture

### Summary
Podczas ponownego ręcznego capture wykryto realny błąd operacyjny: backend działał dalej pod ostatnim scenariuszem i po fizycznej zmianie układu kart potrafił nadpisać wcześniej poprawne pliki scenariusza. Dodano ochronę w `LiveFixtureCapture`: jeżeli scenariusz ma już `raw_frame_<suffix>.png` albo `analysis_frame_<suffix>.png`, kolejne wywołanie `save_snapshot()` zwraca `ok=false`, `reason="already_exists"` i nie nadpisuje plików.

### Verified fixture
Wyczyszczono `logs/live_fixtures/` i zebrano od zera trzy scenariusze. Po każdym scenariuszu obrazy zostały pokazane Michałowi i ręcznie potwierdzone:
- `empty`: poprawna pusta mata, 4 markery ArUco, brak kart.
- `one_card`: poprawny obraz z dokładnie jedną kartą.
- `three_cards`: poprawny obraz z dokładnie trzema kartami.

Zatwierdzony komplet znajduje się lokalnie w:

```text
logs/live_fixtures/event_first_current_debug_verified/
  empty/raw_frame_0.png
  empty/analysis_frame_0.png
  one_card/raw_frame_1.png
  one_card/analysis_frame_1.png
  three_cards/raw_frame_3.png
  three_cards/analysis_frame_3.png
```

Payload dla `three_cards` wykrył `cards_len=4`, ale to nie blokuje celu tego etapu: fixture ma być fizyczną bazą obrazów do offline replay/debug i nauki poprawnej identyfikacji kart bez ciągłego układania kart oraz bez obciążenia frontendem/backendem.

### Decision
Ten etap dostarczył dataset bazowy, nie fix rozpoznawania. Następna praca powinna używać zapisanych obrazów offline, najpierw do najlepszego odtworzenia detekcji zmian i identyfikacji kart poza pełnym runtime, a dopiero po wypracowaniu metody przenieść mały, dowiedziony fix do głównego kodu.

### Required next action
Utworzyć mały offline replay/debug task używający `event_first_current_debug_verified/{empty,one_card,three_cards}` jako wejścia. Celem taska ma być analiza i poprawa identyfikacji kart na zapisanych obrazach, bez strojenia progów na ślepo i bez wymagania kolejnych live snapshotów.
