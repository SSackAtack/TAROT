# STAGE6 RUNTIME INTEGRATION SCOPE AUDIT — 2026-06-05

## Executive Summary
Niniejszy raport zawiera audyt kodu pozostałego do integracji w ramach etapu PR-F (Runtime WebSocket / Autotune Integration). Analizie poddano różnice między gałęzią `master` a monolityczną gałęzią źródłową `origin/task/cv-stage-6-rws-expansion-benchmark-001`. Celem audytu jest określenie minimalnej, bezpiecznej ścieżki integracji, która eliminuje ryzyko regresji w działaniu pętli przetwarzania obrazu na żywo.

## Current Master Baseline
* Gałąź `master` zawiera wszystkie zintegrowane zmiany z etapów PR-A, PR-B, PR-C, PR-D oraz PR-E.
* Ostatni commit na `master` to merge commit dla PR #21 (Studio UI) o hash: `d536fbc9838c8bf4cba6cfb532aba70e46147891`.
* Stan repozytorium jest czysty. Jedyne nieśledzone pliki to katalog `Komercja/`, który zgodnie z instrukcją jest ignorowany.

## Remaining Runtime Diff Summary
Do wdrożenia pozostały zmiany w silniku uruchomieniowym (runtime) oraz obsługa protokołu komunikacyjnego WebSocket. 
* Główne modyfikacje dotyczą:
  * Pliku `app_cv/main.py` (235 linii dodanych) — obsługa nowych komend WebSocket oraz integracja sesji autotuningu.
  * Pliku `app_cv/tarotvision/pipelines/snapshot_first.py` (273 linie dodane) — rejestrowanie próbek autotuningu, zmiana detekcji ruchu na detekcję zmian.
  * Pliku `app_cv/tarotvision/snapshot_analyzer.py` (284 linie dodane) — obsługa ROI, walidacja kandydatów na karty oraz tryb debugowania rozpoznawania.
  * Nowych plików wspomagających (`change_detection.py`, `card_candidate_validation.py`, `live_fixture_capture.py`).

## File Classification Matrix

| File | Classification | Runtime Risk | Suggested PR | Notes |
|---|---|---:|---|---|
| [tuning_protocol.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/tuning_protocol.py) | `PR-F1_RUNTIME_PROTOCOL_ONLY` | Low | PR-F1 | Dodaje tylko definicje struktur wiadomości WebSocket. |
| [main.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/main.py) | `PR-F2_MAIN_WS_COMMANDS` | Medium-High | PR-F2 | Integracja pętli głównej i obsługa stanu autotuningu. |
| [snapshot_first.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/pipelines/snapshot_first.py) | `PR-F3_AUTOTUNE_RUNTIME_SESSION` | High | PR-F3 / PR-G | Łączy zapis próbek autotuningu (PR-F3) oraz detekcję zmian (PR-G). |
| [snapshot_analyzer.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/snapshot_analyzer.py) | `PR-F3_AUTOTUNE_RUNTIME_SESSION` | Medium | PR-F3 / PR-G | Dodaje walidację kandydatów (PR-F3) oraz obsługę ROI z detekcji zmian (PR-G). |
| [card_recognition.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/card_recognition.py) | `PR-F3_AUTOTUNE_RUNTIME_SESSION` | Low-Medium | PR-F3 | Dodaje funkcję debugowania z wyliczaniem metryk dopasowań. |
| [card_candidate_validation.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/card_candidate_validation.py) | `PR-F3_AUTOTUNE_RUNTIME_SESSION` | Low | PR-F3 | Nowy plik. Waliduje kontury pod kątem jasności, kontrastu i krawędzi. |
| [change_detection.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/change_detection.py) | `PR-G_EVENT_FIRST_CHANGE_DETECTION` | Low | PR-G | Nowy plik. Analizuje różnice klatek pod kątem ROI. |
| [background_model.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/background_model.py) | `PR-G_EVENT_FIRST_CHANGE_DETECTION` | Low | PR-G | Dodaje wyliczanie mediany i wskaźnika zmian. |
| [operator_explainability.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/operator_explainability.py) | `DEFER_OPERATOR_EXPLAINABILITY` | Low | Defer | Wizualizacja stanu na konsoli operatora. |
| [live_fixture_capture.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/live_fixture_capture.py) | `DEFER_UNKNOWN` | Low | Defer | Narzędzie do automatycznego zapisu klatek testowych. |

## app_cv/main.py Analysis
* **Liczba dodanych linii:** 235 linii.
* **Liczba zmienionych regionów (hunks):** 8 hunks.
* **Nowe odpowiedzialności:**
  * Rejestracja i obsługa 5 komend WebSocket: `autotune_start`, `autotune_calibrate`, `autotune_cancel`, `autotune_apply`, `autotune_save`.
  * Zarządzanie instancją `AutotuneSession` oraz listą generowanych profili kandydatów.
  * Logowanie zdarzeń autotuningu przy użyciu `AutotuneSessionLog`.
  * Integracja z potokiem `SnapshotFirstPipeline` poprzez przekazanie parametrów: `autotune_sample_recorder`, `change_detector`, `background_model`, `live_fixture_capture`.
  * Podział funkcji rozpoznawania na `recognize_snapshot_crop` oraz `recognize_snapshot_crop_with_debug`.
* **Zalecenie podziału:** Tak. Plik `main.py` nie powinien być wdrażany w całości w jednym kroku. Zmiany należy podzielić na rejestrację protokołu z pustymi handlerami (PR-F2) oraz pełną integrację z potokiem przetwarzania (PR-F3).

## WebSocket Command Inventory
Wprowadzono 5 nowych komend sterujących przesyłanych przez WebSocket:

1. **`autotune_start`**
   * **Payload żądania:** `{"type": "autotune_start", "scenario": "empty" | "one_card" | "three_cards"}`
   * **Payload odpowiedzi (stan):** `{"state": "collecting", "last_score": null, "autotune": {...}}`
   * **Walidacja:** Pole `scenario` musi należeć do zbioru `{"empty", "one_card", "three_cards"}`. W przeciwnym razie zgłaszany jest `ControlMessageError`.
   * **Obsługa błędów:** Wyjątek parsowania jest przechwytywany i wysyłany jako ostrzeżenie operatorskie.
   * **Status frontend:** Studio UI (wdrożone w PR-E) wysyła już tę komendę po kliknięciu przycisku startu kalibracji.
   * **Bezpieczeństwo localhost:** Tak. Zmiany dotyczą wyłącznie pamięci lokalnej procesu.

2. **`autotune_calibrate`**
   * **Payload żądania:** `{"type": "autotune_calibrate"}`
   * **Payload odpowiedzi (stan):** `{"state": "recommendation_ready", "last_score": <float>, "autotune": {...}}`
   * **Walidacja:** Brak parametrów wejściowych.
   * **Obsługa błędów:** Jeśli sesja nie jest zainicjalizowana lub nie zebrała wymaganych próbek, operacja jest przerywana z ostrzeżeniem `"Brak kompletnych probek autotuningu do kalibracji"`.
   * **Status frontend:** Studio UI wysyła tę komendę przy wywołaniu obliczania rekomendacji.
   * **Bezpieczeństwo localhost:** Tak. Obliczenia są całkowicie CPU-bound na maszynie lokalnej.

3. **`autotune_cancel`**
   * **Payload żądania:** `{"type": "autotune_cancel"}`
   * **Payload odpowiedzi (stan):** `{"state": "idle", "last_score": null}`
   * **Walidacja:** Brak.
   * **Obsługa błędów:** Bezpieczna w każdym stanie; czyści instancję sesji autotuningu.
   * **Status frontend:** Studio UI wysyła po kliknięciu "Anuluj".
   * **Bezpieczeństwo localhost:** Tak.

4. **`autotune_apply`**
   * **Payload żądania:** `{"type": "autotune_apply"}`
   * **Payload odpowiedzi (stan):** `{"state": "applied", "last_score": <float>, "autotune": {...}}`
   * **Walidacja:** Brak.
   * **Obsługa błędów:** Zgłasza błąd operatorski, jeśli sesja nie wypracowała rekomendacji profilu.
   * **Status frontend:** Studio UI wysyła po zatwierdzeniu zmian przez operatora.
   * **Bezpieczeństwo localhost:** Tak. Aktualizuje i zapisuje parametry w aktywnym `RuntimeConfigSession`.

5. **`autotune_save`**
   * **Payload żądania:** `{"type": "autotune_save", "name": "<nazwa_profilu>"}`
   * **Payload odpowiedzi (stan):** Bezpośrednio nie zmienia stanu kalibracji, ale zapisuje dane profilu na dysku.
   * **Walidacja:** Wymaga obecności parametru `name`.
   * **Obsługa błędów:** Zgłasza błąd, jeśli brak `name` lub brak wygenerowanej rekomendacji.
   * **Status frontend:** Studio UI wysyła podczas zapisu profilu kalibracji.
   * **Bezpieczeństwo localhost:** Tak. Zapisuje plik JSON w folderze profili.

## Runtime Payload Expectations
Studio UI wdrożone w PR-E oczekuje następujących pól w pakiecie stanu wysyłanym z runtime:
* **`calibration.autotune`** zawierającego słownik statusu sesji:
  * `scenario` — nazwa aktywnego scenariusza,
  * `state` — aktualny krok sesji (`collecting`, `ready_to_score`, `recommendation_ready`),
  * `collected_count` — liczba zebranych klatek z próbkami,
  * `required_count` — wymagana liczba próbek (zawsze 3),
  * `ready_to_score` — wartość boolowska,
  * `recommendation` — wyliczone parametry i ich oceny (obecne po komendzie `autotune_calibrate`).
* **`explainability`** z krokami diagnostycznymi (krok `empty_reference` oraz `change_detection`).

## Dependencies on PR-D Autotune Backend
Integracja runtime w pełni zależy od modułów dostarczonych w PR-D:
* Używa `AutotuneSession` z `autotune_session.py` do zarządzania stanem.
* Używa `AutotuneSessionLog` z `autotune_session_log.py` do zapisu przebiegu strojenia.
* Używa `generate_candidate_profiles` z `autotune_profiles.py` do tworzenia siatki parametrów.
* Używa `choose_best_profile_result` z `autotune_scoring.py` do oceny i wyboru optymalnych nastaw.
* Używa `ProfileStore` z `profile_store.py` do trwałego zapisu wyników.
Wszystkie te zależności znajdują się już w gałęzi `master`.

## Dependencies on PR-E Studio UI
Studio UI (PR-E) nie blokuje kompilacji backendu, ale jest odbiorcą danych diagnostycznych i nadawcą komunikatów kontrolnych. Zmiany w runtime muszą idealnie mapować się na strukturę danych oczekiwaną przez frontend.

## Operator Explainability Assessment
* **Klasyfikacja:** `OPTIONAL_DEFER`
* **Uzasadnienie:** Modyfikacje w `app_cv/tarotvision/operator_explainability.py` nie wpływają na sam algorytm autotuningu ani na pętlę detekcji. Zmiana sygnatury funkcji nie występuje (interfejs `build_cv_explainability` pozostaje zgodny z `master`). Z tego względu wdrożenie szczegółowych opisów wyjaśniających działanie detekcji zmian i tła może zostać odłożone do kolejnego małego PR, co zmniejsza ryzyko regresji.

## Event-First / Change Detection Separation
* **Klasyfikacja:** `PR-G_EVENT_FIRST_CHANGE_DETECTION`
* **Uzasadnienie:** Plik `change_detection.py` oraz integracja `ChangeDetector` z `snapshot_first.py` powinny być całkowicie odseparowane od PR-F i przeniesione do PR-G. Autotuning (strojenie progów i kontrastu) nie zależy funkcjonalnie od obecności optymalizacji obszarów zmian (ROI). Wydzielenie tej części zmniejsza złożoność PR-F o ponad 40%.

## Candidate Tests
Testy jednostkowe z gałęzi monolitycznej przyporządkowano następująco:
* `test_tuning_protocol.py` -> `INCLUDE_PR_F_TEST` (testy walidacji komend)
* `test_card_candidate_validation.py` -> `INCLUDE_PR_F_TEST` (testy nowego filtra jakości konturów)
* `test_snapshot_analyzer.py` -> `INCLUDE_PR_F_TEST` (testy debugowania rozpoznawania i metryk)
* `test_pipelines_contract.py` -> `INCLUDE_PR_F_TEST` (testy kontraktu potoku z użyciem mocków, brak zależności od kamery)
* `test_background_model.py` -> `INCLUDE_PR_F_TEST` (testy wyliczania mediany)
* `test_change_detection.py` -> `DEFER_PR_G_TEST` (zależność od detektora zmian)
* `test_operator_explainability.py` -> `DEFER_PR_G_TEST` (zależność od explainability)
* `test_live_fixture_capture.py` -> `DEFER_UNKNOWN` (zapis klatek diagnostycznych)

## Live Smoke Test Requirements
Integracja runtime wymaga przeprowadzenia testu dymnego przed scaleniem zmian. Zakres testu obejmuje:
1. Uruchomienie backendu (`python app_cv/main.py`) oraz aplikacji Studio UI.
2. Połączenie przeglądarki ze stacją operatorską (`localhost`).
3. Weryfikację stabilności: upewnienie się, że podstawowy mechanizm detekcji działa i nie generuje błędów w pętli klatek.
4. Sprawdzenie odporności UI: upewnienie się, że Studio UI nie ulega awarii, gdy stan autotuningu jest pusty (`null`).
5. Wywołanie nieaktywnych komend (np. `autotune_calibrate` bez próbek) i sprawdzenie, czy system reaguje łagodnym błędem operatorskim.
6. Uruchomienie sesji na żywo z kamerą AnkerWork C310 przez minimum 10 minut w celu weryfikacji wycieków pamięci i stabilności wątku WebSocket.

## Recommended PR-F Split
Sugeruje się podział etapu integracji na trzy mniejsze, bezpieczne kroki wdrażane na osobnych gałęziach:

### PR-F1: WebSocket Protocol Foundations
* **Zakres:** Modyfikacje w `tuning_protocol.py` (definicje komend) oraz testy `test_tuning_protocol.py`.
* **Cel:** Zapewnienie, że serwer potrafi bezbłędnie zinterpretować nowe komunikaty bez ich wykonywania.

### PR-F2: WebSocket Commands & Lifecycle
* **Zakres:** Integracja szkieletu komend w `main.py` z pustymi stubami operacji autotuningu, zarządzanie stanem `AutotuneSession` oraz testy integracyjne WebSocket.
* **Cel:** Umożliwienie komunikacji dwukierunkowej ze Studio UI bez modyfikacji potoku przetwarzania obrazu.

### PR-F3: Autotune Pipeline Integration & Candidate Quality
* **Zakres:** Pełna implementacja zbierania próbek w `snapshot_first.py`, rozszerzenie `snapshot_analyzer.py` o walidację kandydatów (`card_candidate_validation.py`), debugowanie dopasowań w `card_recognition.py` oraz powiązane testy jednostkowe.
* **Cel:** Uruchomienie pełnego, automatycznego strojenia parametrów detekcji.

## Blockers
Brak krytycznych blokerów. Należy jednak pamiętać o:
* Całkowitym wykluczeniu katalogu `Komercja/` z poleceń `git add` podczas przyszłych prac.
* Zabezpieczeniu przed jednoczesnym modyfikowaniem potoku na potrzeby detekcji zmian (ROI) — detekcja zmian musi poczekać na etap PR-G.

## Final Recommendation
`SPLIT_PR_F_INTO_SMALLER_PARTS`
