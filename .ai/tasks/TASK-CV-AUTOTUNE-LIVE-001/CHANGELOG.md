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

## 2026-06-02 Codex Post-Task 10 recognition diagnostics hook

- Podłączono `SnapshotFirstPipeline` do opcjonalnego callbacku `autotune_sample_recorder`, który po analizie snapshotu przekazuje `candidate_count`, `accepted_count`, `recognition_score`, `recognition_rejections` i czas analizy.
- Dodano w `main.py` `record_autotune_sample_from_snapshot()`, które zapisuje realne próbki do aktywnej `AutotuneSession` i uruchamia rekomendację po zebraniu wymaganej liczby próbek.
- Dla scenariusza `empty` próbki autotuningu karzą false positives na podstawie liczby wykrytych/zaakceptowanych obiektów.
- Rozszerzono `SnapshotAnalyzer` o per-candidate recognition diagnostics: `crop_keypoints`, `top_matches`, `reject_reason`, `score_margin`, `accepted` i agregowany `recognition_score`.
- Rozszerzono `recognize_card_crop_with_debug()` o ranking top-matchy, żeby debug odróżniał zwycięzcę od bliskich alternatyw.
- README uzupełniono o metrykę `recognition_score` i realne pola próbek Live Auto Tune.

## 2026-06-02 Codex glare false-positive hardening

- Dodano `app_cv/tarotvision/card_candidate_validation.py` z walidacją cropa kandydata przed rozpoznawaniem ORB.
- `SnapshotAnalyzer` odrzuca cropy bez cech karty (`smooth_low_texture`, `no_card_border_evidence`) zanim trafią do `recognize_crop`.
- Rozszerzono diagnostykę kandydatów o `candidate_validation` i licznik `candidate_validation_rejections`.
- `SnapshotFirstPipeline` zapisuje `snapshot_candidate_validation_rejections` w metrykach runtime oraz w próbkach autotuningu.
- `CV Explain` pokazuje ostrzeżenie „bez cech karty” i kieruje operatora na odblask/tło, gdy luka kandydatów wynika z walidacji cropa.

## 2026-06-02 Codex Studio sidebar accordion

- Uporządkowano prawy panel Studio jako zestaw rozwijanych sekcji.
- Oddzielono `Auto Tune` od `Aktywnych Talii`, aby wybór talii nie mieszał się z diagnostyką i kalibracją.
- Dodano zapamiętywanie zwiniętych sekcji w `localStorage` pod kluczem `studio:sidebarCollapsedSections`.
- Dodano statyczny test kontraktu UI dla osobnych sekcji i akordeonów.

## 2026-06-02 Codex Auto Tune wizard MVP

- Rozszerzono `AutotuneSession.status()` o `scenario`, `stage_result` i `next_action`.
- Dodano reguly PASS/FAIL dla scenariuszy `empty`, `one_card` i `three_cards`.
- Dodano `app_cv/tarotvision/autotune_session_log.py` zapisujacy trwale logi sesji do `logs/autotune_sessions/`.
- Dodano komende WebSocket `autotune_calibrate`.
- Zmieniono backend tak, aby rekomendacja powstawala po jawnej komendzie `autotune_calibrate`, a nie automatycznie po zebraniu probek.
- Panel Studio pokazuje wynik etapu i ma nowe przyciski `Skalibruj` oraz `Save Profile`.

## 2026-06-02 Codex preview controls visibility

- Sekcja `Widok podgladu` jest teraz domyslnie otwarta w prawym panelu Studio.
- Stary zapis localStorage zwijajacy sekcje `preview` jest ignorowany, aby operator od razu widzial przelaczniki obrazu.
- Przycisk trybu `table` ma czytelniejsza etykiete `Wirtualny stol`.

## 2026-06-02 Codex PiP slider cap fix

- Usunieto twardy limit `560px` z szerokosci okna PiP w Studio.
- Zmieniono ograniczenie rozmiaru PiP na limit wzgledem dostepnej szerokosci overlayu: `calc(100% - 56px)`.
- Dodano statyczny test chroniacy przed ponownym uciekaniem zakresu suwaka 38-45% w martwa strefe.

## 2026-06-02 Codex Auto Tune forced sampling fix

- Zdiagnozowano live przypadek, w ktorym `Pusta mata` zapisywala tylko `stage_started`, ale nie zbierala probek, bo snapshot gate nie dostawal naturalnego ruchu.
- Dodano `SnapshotGate.request_sample(now_ms)` dla operatorskich zadan probkowania.
- `autotune_start` wymusza teraz snapshot po krotkim settle zamiast czekac na ruch.
- `record_autotune_sample_from_snapshot()` zwraca `request_next_sample`, dopoki etap nie ma kompletu probek.
- `SnapshotFirstPipeline` obsluguje zwrot recordera i zada kolejnego snapshotu po zakonczeniu biezacej analizy.
- Dodano testy regresji dla manualnego requestu bramki, wymuszenia probkowania po `autotune_start` i dociagania probek do `3/3`.

## 2026-06-02 Codex event-first background diff plan

- Dodano plan wykonawczy `docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md`.
- Plan definiuje docelowy model `empty_reference`, `previous_stable_snapshot` i ROI hints dla `SnapshotAnalyzer`.
- Plan rozbija implementacje na testowalne taski dla `BackgroundModel`, `ChangeDetector`, `SnapshotAnalyzer`, `SnapshotFirstPipeline`, `main.py`, CV Explain i live smoke.

## 2026-06-02 Event-first plan clarification

- Doprecyzowano w planie rozdzial `Autotune / Calibration Mode` vs `Runtime / Recording Pipeline`.
- Dodano zalozenia kontrolowanego runtime: stale swiatlo, stabilna kamera/mata, motion gate przed analiza oraz docelowo wylaczone auto focus / auto exposure / auto white balance.
- Poprawiono bootstrap `empty_reference`: referencja powstaje z 3-5 stabilnych snapshotow pustej maty przed walidacja, bez polegania na starej globalnej detekcji kart.
- Dodano safety rules: global detection po udanej kalibracji nie jest glowna sciezka, `ignored_global_shift` zachowuje poprzedni stan, brak referencji oznacza jawny fallback mode.
- Zaktualizowano breakdown do Task 0-7 zgodnie z handoffem Supervisor.

## 2026-06-02 Event-first plan amendment 001

- Pobrano z GitHuba osobną erratę `docs/superpowers/plans/2026-06-02-event-first-background-diff-plan-amendment-001.md` jako obowiązkowy materiał review przed implementacją.
- Doprecyzowano semantykę `roi_hints`: `None` oznacza fallback globalny, pusta lista `[]` oznacza aktywny event-first bez ROI i zakaz globalnego skanowania.
- Dodano wymagany test planistyczny chroniący przed fallbackiem globalnym przy `roi_hints=[]`.
- Skorygowano walidację `empty_reference`: ma używać `BackgroundModel.changed_ratio(current_empty_frame)` albo równoważnego porównania reference-vs-current, nie `analysis_frame` vs `analysis_frame`.

## 2026-06-02 Event-first amendment merge

- Scalono treść `event-first-background-diff-plan-amendment-001.md` bezpośrednio do głównego planu `docs/superpowers/plans/2026-06-02-event-first-background-diff-implementation-plan.md`.
- Główny plan zawiera teraz sekcję `ROI Semantics`, wymagany test dla `roi_hints=[]`, zakaz `roi_hints or None` oraz poprawioną walidację `empty_reference` przez `BackgroundModel.changed_ratio()`.
- Usunięto osobny plik amendmentu i osobny raport erraty, aby implementatorzy pracowali z jednym źródłem prawdy.

## 2026-06-02 Event-first Task 1 Stable Empty Reference

- Rozszerzono `BackgroundModel` o `capture_many(frames)`, które buduje referencję pustej maty jako medianę ramek o zgodnym kształcie.
- Dodano `changed_ratio(frame, threshold)`, wspólny helper `_to_gray()` i testy regresji dla median reference oraz udziału foreground.
- Oznaczono Task 1 w głównym planie jako wykonany; kolejnym krokiem implementacyjnym jest Task 2 `ChangeDetector`.

## 2026-06-02 Event-first Task 2 ChangeDetector

- Dodano `app_cv/tarotvision/change_detection.py` z dataclassami `ChangeDetectorConfig`, `ChangeRegion` i `ChangeDetectionResult`.
- `ChangeDetector.detect()` porównuje `previous_frame` z `current_frame`, filtruje małe/duże regiony, wykrywa global shift i klasyfikuje region jako `added_or_moved` albo `removed` względem `empty_reference`.
- Dodano testy syntetyczne dla dodania karty, usunięcia karty, ignorowania drobnej zmiany i globalnej zmiany obrazu.
- Oznaczono Task 2 w głównym planie jako wykonany; kolejnym krokiem implementacyjnym jest Task 3 `SnapshotAnalyzer ROI Hints`.

## 2026-06-02 Event-first Task 3 SnapshotAnalyzer ROI Hints

- Rozszerzono `SnapshotAnalyzer.analyze()` o parametr `roi_hints=None`.
- Dodano diagnostykę `roi_limited` i `roi_count`.
- Przy `roi_hints is None` dotychczasowy global fallback pozostaje dozwolony.
- Przy `roi_hints == []` analyzer nie wykonuje globalnej detekcji i zwraca zero kart, zgodnie z erratą bezpieczeństwa.
- Przy niepustej liście ROI analyzer szuka quadów wyłącznie w cropach ROI i przesuwa punkty z powrotem do współrzędnych pełnego frame.
- Dodano testy regresji dla ograniczenia analizy do ROI oraz zakazu fallbacku globalnego przy pustej liście ROI.
