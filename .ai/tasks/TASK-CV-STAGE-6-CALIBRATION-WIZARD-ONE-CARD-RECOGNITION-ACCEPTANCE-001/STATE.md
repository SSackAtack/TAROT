# STATE: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## Status

IN_PROGRESS

## Branch

`task/cv-stage-6-calibration-wizard-one-card-recognition-acceptance-001`

## Stan aktualny

Task utworzony jako follow-up po stabilizacji geometrii jednej karty. Fizyczna talia użyta w smoke teście została potwierdzona jako Gilded, a runtime/Studio również używały aktywnej talii `gilded`. Niespójność talii nie wyjaśnia więc `accepted_total=1/3`.

Wdrożono minimalną diagnostykę recognition acceptance: odrzucone cropy mogą teraz raportować `crop_keypoints`, `reject_reason` oraz top match candidates z `match_count`, `inlier_ratio` i `score`. Diagnostyka jest przekazywana przez `SnapshotAnalyzer`, `SnapshotFirstPipeline` i zapisywana w próbkach Calibration Wizard.

Po restarcie backendu runtime potwierdził aktywną talię `gilded`, a Studio widziało jedną zaakceptowaną kartę (`Cards=1`, `Rozpoznanie=1`). Uruchomienie `one_card` nie zebrało jednak nowych próbek bez świeżego ruchu/snapshotu; dalsza weryfikacja wymaga fizycznego poruszenia kartą/ręką i odłożenia karty stabilnie.

Podczas przygotowania kolejnego smoke testu operator zgłosił powtarzalny błąd OpenCV MSMF `can't grab frame`. Po zamknięciu okien i restarcie `.bat` problem wracał. Dodano mały hotfix kamery: na Windows `CameraSession` próbuje najpierw backend DirectShow (`cv2.CAP_DSHOW`), a gdy nie zadziała, wraca do domyślnego backendu OpenCV. Lokalny restart backendu potwierdził otwarcie kamery przez DirectShow bez nowych ostrzeżeń MSMF.

Po hotfixie DirectShow kamera sprzętowo zgłaszała surowe 1920x1080 mimo żądania 1280x720. Dodano runtime resize w `CameraSession.read()`: jeśli sterownik ignoruje rozdzielczość, klatki są skalowane do żądanego 1280x720 przed przekazaniem do pipeline. Log po restarcie potwierdził: raw 1920x1080, runtime 1280x720.

Zgłoszony `WinError 10048` na porcie `8765` wynikał z dwóch równoległych procesów `python main.py`; stara instancja trzymała WebSocket. Procesy zostały zamknięte i backend po czystym restarcie poprawnie nasłuchuje na `8765`.

Następna diagnoza braku obrazu wykazała, że endpoint MJPEG działał i zwracał poprawne JPEG-i, ale DirectShow dawał klatki całkowicie czarne (`mean_gray=0.0`). Ten sam indeks kamery przez domyślny backend OpenCV/MSMF dawał normalny obraz (`mean_gray~54-58`). `CameraSession` został więc uodporniony: DirectShow jest akceptowany tylko wtedy, gdy próbne klatki nie są czarne; w przeciwnym razie następuje fallback do domyślnego backendu. Po restarcie backendu preview zwróciło `mean_gray=53.8`, a Studio pokazało realny obraz.

Launcher Studio został rozszerzony o kontrolę portów `5173`, `8765` i `8766`, ponieważ konflikt dotyczył nie tylko Vite, ale też WebSocket i MJPEG preview backendu. MJPEG preview obsługuje teraz także normalne przerwanie połączenia klienta bez czerwonego tracebacka.

Po fizycznym smoke teście Gilded `one_card` zebrał 3/3 próbki i po komendzie `autotune_calibrate` przeszedł jako `PASS`. Każda próbka miała `detected_count=1`, `accepted_count=1`, `recognition_rejections=0`; finalnie `accepted_total=3`, `false_positive_total=0`. Recognition acceptance dla tej konfiguracji nie jest już blockerem w scenariuszu `one_card`.

Mimo udanego smoke testu runtime nadal potrafił spamować ostrzeżeniami MSMF `grabFrame` przy nieudanych odczytach. Dodano mechanizm samonaprawy `CameraSession`: po serii kolejnych nieudanych odczytów kamera jest przeotwierana na tym samym indeksie, a pojedyncze krótkie niepowodzenia są lekko throttlowane, żeby ograniczyć pętlę błędów.

## Session Status (2026-06-05)

- Utworzono zakres diagnostyczny nowego taska.
- Ustalono, że nie wolno kontynuować zmian w geometrii bez nowych dowodów.
- Dodano TDD dla raportowania najlepszego odrzuconego matcha w recognition debug.
- Dodano TDD dla przeniesienia recognition debug przez `SnapshotAnalyzer` do diagnostyki snapshotu.
- Dodano TDD dla zapisu `recognition_debug` w próbkach Calibration Wizard.
- Zrestartowano backend i potwierdzono runtime `gilded`.
- Próba zebrania nowego `one_card` nie dała próbek bez fizycznego ruchu.
- Dodano DirectShow-first fallback dla kamery na Windows po powtarzalnym błędzie MSMF `grabFrame`.
- Dodano skalowanie klatek w runtime do 1280x720, gdy sterownik DirectShow ignoruje żądaną rozdzielczość.
- Zdiagnozowano i usunięto lokalny konflikt portu `8765` spowodowany dwoma procesami `python main.py`.
- Zdiagnozowano czarny obraz: DirectShow zwracał czarne klatki, a domyślny backend/MSMF zwracał obraz.
- Dodano fallback z DirectShow do domyślnego backendu, gdy próbne klatki są czarne.
- Rozszerzono launcher Studio o kontrolę portów `5173`, `8765`, `8766`.
- Uciszono traceback MJPEG przy normalnym zerwaniu połączenia klienta.
- Potwierdzono fizyczny `one_card` smoke dla Gilded: `PASS`, `accepted_total=3/3`.
- Dodano samonaprawę kamery po kolejnych nieudanych odczytach `grabFrame`.

## Kolejne kroki

1. Przy kolejnym uruchomieniu użyć `.bat`; jeśli wykryje zajęte porty `5173/8765/8766`, wybrać opcję automatycznego zatrzymania starej sesji.
2. Wykonać opcjonalny scenariusz `three_cards` albo świadomie oznaczyć go jako `NOT_RUN`.
3. Jeżeli `three_cards` nie jest wymagany do tej decyzji, przygotować status review dla supervisora z wynikiem `one_card PASS 3/3`.
4. Monitorować, czy samonaprawa kamery ograniczy spam MSMF w dłuższym runtime; jeśli nie, wydzielić osobny task kamery/backendu.
