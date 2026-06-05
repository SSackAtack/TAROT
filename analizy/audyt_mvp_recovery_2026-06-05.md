# Audyt projektu TarotVision i plan odzyskania MVP

Data: 2026-06-05
Autor: Codex
Branch: `codex/project-mvp-recovery-audit-2026-06-05`
Zakres: audyt procesu, architektury runtime, ślepych uliczek i planu dojścia do MVP bez dalszego kodowania w tej sesji.

## Decyzja wykonawcza

Projekt nie wygląda na technicznie bezsensowny ani skazany na porażkę. Ostatnie wyniki live smoke pokazują, że po ustawieniu fizycznej i aktywnej talii na Gilded scenariusz `one_card` przeszedł jako całość: `3/3`, `accepted_total=3`, `stage_result=PASS`. To jest mocny sygnał, że główny kierunek snapshot-first/OpenCV nadal ma sens dla MVP.

Problemem nie jest teraz brak jakiejkolwiek drogi technicznej. Problemem jest utrata ostrości procesu: autotuning i kalibracja zaczęły pełnić rolę celu samego w sobie. To generuje kolejne progi, profile, scoringi, smoke testy i sesje diagnostyczne, ale nie przybliża proporcjonalnie do pierwszego używalnego nagrania.

Rekomendacja: wejść w tryb **MVP Recovery Mode**. Na czas dojścia do pierwszego używalnego MVP zamrozić rozwój autotuningu jako funkcji, utrzymać go wyłącznie jako preflight/readiness check, a główny cel przesunąć na operator-assisted recording workflow: stabilny podgląd, wybrana talia, kontrolowany smoke, rozpoznanie układu i gotowość do nagrania krótkiego materiału testowego.

## Fakty zweryfikowane

### Stan tasków

W momencie rozpoczęcia audytu indeks `.ai/TASKS_INDEX.md` zawierał 78 pozycji. Stan przed dodaniem tego taska recovery:

- `APPROVED`: 47
- `DONE`: 28
- `GEOMETRY_VERIFIED_RECOGNITION_FOLLOWUP_REQUIRED`: 1
- `IN_PROGRESS`: 1
- `TODO`: 1

To potwierdza, że projekt ma dużo wykonanej pracy, ale obecnie duża część energii idzie w zadania walidacyjno-tuningowe, nie w domknięcie demonstracyjnego workflow.

### Ostatni wynik krytycznego smoke testu

Zadanie `TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001` pokazuje najważniejszy przełom:

- fizyczna talia: Gilded
- aktywna talia runtime: `gilded`
- scenariusz: `one_card`
- próbki: `3/3`
- `stage_result`: `PASS`
- `accepted_total`: `3`
- `false_positive_total`: `0`
- komunikat: `1 karta poprawna: wykryto i zaakceptowano jedna karte.`

Wniosek: pierwotny blocker geometrii oraz późniejszy blocker recognition acceptance dla jednej karty nie są już obecnie dowodem na ślepą uliczkę. Były w dużej mierze efektem kombinacji progów, konfiguracji talii i problemów runtime/kamery.

### Bieżąca architektura i obciążenie modułów

Projektowy runtime CV jest funkcjonalny, ale coraz cięższy organizacyjnie:

- `app_cv/main.py` ma około 930 linii i łączy uruchamianie kamery, WebSocket, komendy Studio, stan kalibracji, profile, autotune i część logiki operacyjnej.
- `app_cv/tarotvision/pipelines/snapshot_first.py` ma około 266 linii i obsługuje gate, sampling, jakość klatek, analizę, diagnostykę, HUD i przekazanie próbek autotune.
- `app_cv/tarotvision/calibration_wizard_scoring.py` ma około 287 linii i pełni rolę scoringu preflight.
- `app_ar/src/studio/studioConsole.js` ma ponad 1700 linii i zawiera wiele odpowiedzialności UI.

To nie oznacza, że trzeba teraz robić wielki refaktor. Oznacza, że każde kolejne dokładanie funkcji do autotuningu lub Studio zwiększa koszt poznawczy i oddala MVP.

### Konfiguracja talii

`app_ar/public/active_decks.json` ma lokalną zmianę `rider-waite-smith -> gilded`. To było kluczowe dla ostatniego smoke testu i jest sensowną konfiguracją operatorską, ale plik jest poza zakresem commita. Nie wolno traktować go jako zwykłej zmiany kodowej, bo może odzwierciedlać aktualny fizyczny setup operatora.

## Czy wpadliśmy w ślepe uliczki?

### 1. Autotuning jako centrum projektu

Tak, to jest obecna ślepa uliczka procesowa.

Autotuning miał pomagać operatorowi ustawić stanowisko i zebrać diagnostykę. W praktyce zaczął produkować kolejne zadania, kolejne progi i kolejne definicje sukcesu. To kradnie uwagę z pytania: czy można już nagrać pierwszy materiał z działającym rozpoznaniem i AR?

Decyzja: autotuning nie jest MVP. Autotuning ma być ograniczony do preflight:

- pusta mata nie daje fałszywych kart,
- jedna karta jest wykryta i zaakceptowana,
- trzy karty są wykryte albo jasno klasyfikowane jako wymagające ręcznej interwencji,
- HUD mówi operatorowi co poprawić.

Nie rozwijamy teraz kolejnych automatycznych rekomendacji profili, jeśli nie blokują bezpośrednio pierwszego nagrania.

### 2. Ciągłe luzowanie progów geometrii

Częściowo tak.

Fallback `min_area_rect` pomógł, bo `one_card` przestał rozpadać się geometrycznie. Ale każde kolejne luzowanie progów zwiększa ryzyko false positive na pustej macie, cieniach i odbiciach. W tej chwili geometria powinna być traktowana jako wystarczająco dobra do MVP, dopóki `empty` pozostaje czyste.

Decyzja: zamrozić tuning geometrii. Wracać do niego tylko, gdy:

- `empty` failuje przez false positives,
- `one_card` przestaje mieć `detected_count=1`,
- `three_cards` failuje z jednoznacznie geometrycznego powodu, nie przez recognition/acceptance.

### 3. Offline benchmarki jako substytut używalności

Tak, jeśli zaczynają zastępować fizyczny workflow.

Offline benchmarki są wartościowe do regresji i izolowania zmian, ale MVP TarotVision wymaga realnego obrazu z kamery, stabilnego preview i gotowości do nagrania. Testy offline nie odpowiedzą, czy operator może zrobić sesję bez wielogodzinnej diagnostyki.

Decyzja: od teraz każda większa zmiana CV musi mieć krótką odpowiedź: co poprawia w nagraniu/operator workflow? Jeśli odpowiedź brzmi wyłącznie "lepszy scoring autotune", zadanie nie jest priorytetem MVP.

### 4. Pełna odporność wielotalijna przed pierwszym MVP

Tak.

Projekt obsługuje wiele talii i to jest wartościowe, ale dla MVP trzeba wybrać jedną kontrolowaną talię. Po ostatnich testach naturalnym kandydatem jest Gilded, bo fizyczny test `one_card` przeszedł po spójnej konfiguracji.

Decyzja: MVP powinno być na jednej aktywnej talii. Multi-deck hardening wraca dopiero po pierwszym nagraniu.

### 5. Perfekcyjna kamera i perfekcyjny backend capture

Częściowo.

MSMF/DirectShow i konflikty portów realnie przeszkadzały. Dodane obejścia i recovery są potrzebne. Ale ostrzeżenia kamery nie mogą automatycznie resetować priorytetów, jeśli system nadal pobiera próbki, preview działa i nagranie da się wykonać.

Decyzja: kamera jest blockerem tylko wtedy, gdy nie ma obrazu, nie da się zebrać próbek albo preview jest niestabilny podczas nagrania. Same ostrzeżenia są `WARN`, nie `STOP`.

## Co zachować

- Snapshot-first jako główną ścieżkę CV dla MVP.
- OpenCV-first bez wprowadzania teraz modelu ML/YOLO.
- Aktywną talię jako świadomy wybór operatora.
- Calibration Wizard jako checklistę gotowości, nie jako autonomiczny optimizer.
- Diagnostykę `recognition_debug`, jeśli pomaga wyjaśnić odrzucenia.
- Recovery kamery, jeśli utrzymuje preview i sample capture.
- Zasadę "diagnostyka przed progiem": nie zmieniać progów bez dowodu z konkretnego smoke testu.

## Co zamrozić do czasu MVP

- Nowe profile autotune i nowe heurystyki scoringu autotune.
- Dalsze luzowanie geometrii bez regresji smoke.
- Rozszerzanie talii.
- Przebudowę na ML/YOLO.
- Duże refaktory `main.py` i Studio UI, jeśli nie odblokowują bezpośrednio nagrania.
- Rozwijanie porównywania kolejnych snapshotów jako osobnego systemu event detection. Dla MVP wystarczy, że snapshoty stabilnie identyfikują aktualny stan stołu.

## Definicja MVP

MVP TarotVision nie powinno być definiowane jako "system sam się perfekcyjnie dostraja". MVP powinno być definiowane jako:

> Operator może uruchomić aplikację, wybrać jedną fizyczną talię, potwierdzić gotowość stanowiska, rozłożyć karty, zobaczyć stabilny wynik w Studio/AR i nagrać krótki materiał testowy bez ręcznego debugowania kodu.

### MVP obejmuje

- Jedną aktywną talię: rekomendacja na teraz to Gilded.
- Jeden kontrolowany setup: znana kamera, znana mata, znane światło.
- Stabilny preview kamery.
- Preflight:
  - `empty`: PASS,
  - `one_card`: PASS,
  - `three_cards`: PASS albo jawny manual fallback.
- AR/Studio pokazujące wynik w sposób używalny do nagrania.
- Krótki test recording, nawet jeśli operator musi zatwierdzić/wybrać poprawkę ręcznie.

### MVP nie obejmuje

- Perfekcyjnego autotuningu.
- Automatycznej optymalizacji progów dla każdego światła.
- Pełnej odporności na każdą talię i każdą kamerę.
- Bezobsługowego rozpoznawania każdego układu.
- Dużego refaktoru architektury.
- Rozwijania każdej ścieżki diagnostycznej do osobnej funkcji produktu.

## Proponowany tryb pracy: MVP Recovery Mode

### Reguły na najbliższe zadania

1. Każde zadanie musi mieć sekcję "wpływ na MVP".
2. Każde zadanie musi mieć stop condition: kiedy przestajemy drążyć.
3. Nie tworzyć zadań autotune, chyba że usuwają złożoność albo naprawiają twardy blocker nagrania.
4. Nie zmieniać geometrii bez nowego `empty` smoke.
5. Nie commitować `active_decks.json`.
6. Jedno zadanie powinno zmieniać maksymalnie mały, czytelny zakres.
7. Testy jednostkowe są ważne, ale decyzje MVP muszą opierać się też na fizycznym smoke.

### Nowe kryteria decyzji

`GO`:

- preview działa,
- `empty` PASS,
- `one_card` PASS,
- `three_cards` PASS albo operator ma prosty fallback,
- wynik można pokazać/nagrać.

`WARN`:

- kamera loguje warningi, ale sample i preview działają,
- confidence jest niskie, ale accepted output jest stabilny,
- rekomendacja wizard jest LOW, ale stage przechodzi.

`STOP`:

- `empty` wykrywa fałszywe karty,
- preview jest czarne albo zrywa się w trakcie sesji,
- aktywna talia nie zgadza się z fizyczną,
- system wymaga kolejnego tuningu zanim operator może zrobić prosty test.

## Plan naprawczy do MVP

### Faza 0: Zamknięcie audytu i zamrożenie rozproszenia

Status: wykonywane w tym tasku.

Wynik:

- zapisany audyt,
- zapisany plan recovery,
- brak zmian w kodzie runtime,
- `active_decks.json` pominięty.

### Faza 1: Runbook operatora

Cel: operator ma jedną instrukcję uruchomienia i smoke testu, bez szukania po czacie.

Zakres:

- aktywna talia,
- kamera i porty,
- kolejność uruchamiania `.bat`,
- co zrobić przy konflikcie portu 8765,
- co zrobić przy czarnym preview,
- jak klasyfikować warningi kamery,
- kiedy przerwać, a kiedy kontynuować.

Stop condition:

- runbook pozwala wykonać `empty`, `one_card`, `three_cards` bez decyzji projektowych w trakcie testu.

### Faza 2: MVP smoke zamiast kolejnego autotuningu

Cel: jeden spójny test produktu.

Minimalny protokół:

1. Gilded jako fizyczna i aktywna talia.
2. `empty`: 3/3, false positives NIE.
3. `one_card`: 3/3, accepted_total 3.
4. `three_cards`: PASS albo FAIL z klasyfikacją: geometry / recognition / operator setup.
5. Preview Studio widoczne.
6. Brak port conflict.
7. Krótki zapis wyniku.

Stop condition:

- jeśli `three_cards` przejdzie, nie tuningujemy dalej; przechodzimy do nagrania.
- jeśli `three_cards` nie przejdzie, oceniamy najpierw manual fallback, nie progi.

### Faza 3: Manual fallback / operator override

Cel: MVP ma dać się użyć nawet przy pojedynczym błędzie recognition.

Wymaganie produktowe:

- operator może potwierdzić kartę lub skorygować wynik bez kończenia sesji.

Decyzja:

- jeśli taki mechanizm już istnieje, opisać go w runbooku;
- jeśli nie istnieje, zrobić minimalną wersję, ale dopiero po smoke `three_cards`.

Stop condition:

- jeśli ręczna korekta pozwala nagrać materiał, nie rozwijamy dalej autotuningu przed MVP.

### Faza 4: Pierwszy recording-ready demo

Cel: krótki materiał demonstracyjny, który pokazuje sens produktu.

Zakres:

- jedna talia,
- jeden rozkład,
- operator-assisted flow,
- widoczny wynik w Studio/AR,
- zapis problemów jako backlog, nie jako natychmiastowy tuning.

Stop condition:

- jeśli demo jest używalne, MVP Recovery Mode kończy się sukcesem i wracamy do porządkowania długu.

## Priorytety backlogu po MVP

1. Aktualizacja README i `.ai/PROJECT_STATE.md`, bo część opisów nie odzwierciedla obecnego stanu.
2. Wydzielenie orchestracji z `main.py` dopiero po nagraniu MVP.
3. Uporządkowanie Studio UI po stronie modułów, nie przed MVP.
4. Utrzymanie autotune jako narzędzia diagnostycznego.
5. Dopiero potem multi-deck robustness, lighting robustness i większe refaktory.

## Najbliższy bezpieczny krok

Nie pisać kolejnego tuningu. Wykonać:

1. Aktualny task recognition acceptance oznaczyć w dokumentacji jako: `ONE_CARD_ACCEPTANCE_VERIFIED_MVP_FOLLOWUP_REQUIRED`.
2. Przygotować runbook operatora MVP.
3. Uruchomić fizyczny `three_cards` smoke na Gilded.
4. Jeśli `three_cards` przejdzie, przejść do recording-ready demo.
5. Jeśli `three_cards` nie przejdzie, najpierw sprawdzić manual fallback/operator override, a dopiero potem decydować o kodzie CV.

## Ocena końcowa

Projekt nadal ma sens, ale wymaga zmiany definicji sukcesu. Sukcesem najbliższego etapu nie jest "autotuning działa idealnie". Sukcesem jest "operator może wykonać i nagrać kontrolowaną sesję".

Autotuning powinien pomagać w gotowości stanowiska. Nie może być głównym produktem.
