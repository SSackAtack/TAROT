# TarotVision MVP Recording Runbook

## Cel

Ten runbook prowadzi operatora od startu aplikacji do decyzji, czy można nagrać krótką sesję MVP. Nie służy do zbierania fixture offline i nie uruchamia `stage6_capture_wizard.bat`.

Priorytet MVP: jedna talia Gilded, stabilny podgląd, preflight `empty` / `one_card` / `three_cards`, a potem recording demo.

## Setup

- physical deck: Gilded
- active deck runtime: `gilded`
- camera target resolution: `1280x720`
- WebSocket port: `8765`
- Studio URL: `http://localhost:5173/?studio=1`
- frontend dev port: `5173`
- primary launcher: `start_tarotvision_studio.bat`

## Before Start

1. Zamknij stare okna backendu, Studio, Node/Vite i OBS, jeśli używa kamery.
2. Upewnij się, że kamera nie jest używana przez inną aplikację.
3. Nie cofaj lokalnego `app_ar/public/active_decks.json`, jeśli wskazuje `gilded`; to konfiguracja operatora dla MVP.
4. Nie uruchamiaj `stage6_capture_wizard.bat` w tym workflow. Ten wizard jest do fixture offline, nie do recording-ready MVP.

## Start

1. Z głównego katalogu repo uruchom:

```powershell
.\start_tarotvision_studio.bat
```

2. Otwórz Studio:

```text
http://localhost:5173/?studio=1
```

3. Sprawdź w logu backendu:

```text
[OK] Zaladowano talie aktywne: ['gilded']
```

4. Sprawdź w Studio:

- preview kamery jest widoczne,
- panel Calibration Wizard jest dostępny,
- aktywna talia to Gilded,
- nie ma czarnego preview.

## Preflight

### EMPTY

W Studio uruchom scenariusz `PUSTA MATA`.

Expected:

- samples: `3/3`
- false positives: NIE
- HUD false warnings: NIE
- detected cards: `0`

Decision:

- PASS: przejdź do `ONE_CARD`.
- STOP: jeśli pojawia się jakakolwiek fałszywa karta.

### ONE_CARD

Połóż jedną fizyczną kartę Gilded i uruchom scenariusz `1 KARTA`.

Expected:

- samples: `3/3`
- accepted_total: `3`
- detected_count: `1` dla każdej próbki albo czytelny powód odrzucenia
- final stage result: PASS

Decision:

- PASS: przejdź do `THREE_CARDS`.
- WARN: jeśli są warningi kamery, ale próbki przechodzą i preview działa.
- STOP: jeśli aktywna talia nie zgadza się z fizyczną albo accepted_total spada bez czytelnej przyczyny.

### THREE_CARDS

Połóż trzy fizyczne karty Gilded i uruchom scenariusz `3 KARTY`.

Expected:

- stage result: PASS
- wynik jest stabilny i zrozumiały dla operatora

Jeśli FAIL, sklasyfikuj przyczynę:

- `geometry` — zły detected_count, karta się dzieli lub znika,
- `recognition` — crop istnieje, ale karta nie jest akceptowana,
- `operator setup` — talia, światło, ułożenie lub mata są niespójne,
- `camera` — preview znika, kamera nie daje klatek.

## Decision

### GO

Przejdź do recording demo, jeśli:

- preview działa,
- active deck zgadza się z physical deck,
- `EMPTY` PASS,
- `ONE_CARD` PASS,
- `THREE_CARDS` PASS albo istnieje jawny manual fallback,
- warningi kamery nie blokują próbek.

### WARN

Można kontynuować ostrożnie, jeśli:

- kamera loguje warningi, ale preview i sample działają,
- confidence jest niskie, ale wynik jest stabilny,
- rekomendacja wizard jest LOW, ale stage przechodzi.

### STOP

Zatrzymaj workflow, jeśli:

- preview jest czarne,
- port `8765` jest zajęty i backend nie startuje,
- active deck nie zgadza się z physical deck,
- `EMPTY` wykrywa fałszywe karty,
- nie można zebrać próbek,
- `THREE_CARDS` failuje bez klasyfikacji przyczyny.

## Recovery

### Konflikt portu 8765

Objaw:

```text
OSError: [Errno 10048] error while attempting to bind on address ('::1', 8765...)
```

Działanie:

1. Zamknij stare terminale backendu.
2. Jeśli launcher pokazuje PID procesu na porcie, zatrzymaj ten proces.
3. Uruchom `start_tarotvision_studio.bat` ponownie.

### Czarne preview

Działanie:

1. Zamknij backend, Studio i inne aplikacje kamery.
2. Uruchom ponownie launcher.
3. Jeśli preview nadal jest czarne, klasyfikuj jako `STOP_CAMERA`.

### Warningi kamery

Objaw:

```text
CvCapture_MSMF::grabFrame videoio(MSMF): can't grab frame
```

Działanie:

- `WARN`, jeśli preview i próbki działają.
- `STOP`, jeśli preview znika albo sample nie dochodzą do `3/3`.

### Niezgodna talia

Jeśli fizyczna talia to Gilded, runtime musi pokazywać:

```text
['gilded']
```

Jeśli runtime pokazuje inną talię, zatrzymaj smoke. Nie interpretuj błędów recognition jako błędów algorytmu, dopóki deck config nie jest zgodny.

## Output

Po preflight uzupełnij:

- `docs/operator/mvp_physical_smoke_checklist.md` w kopii raportowej albo
- `.ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001/TEST_REPORT.md`, jeśli wykonywany jest formalny Task 2 harmonogramu.
