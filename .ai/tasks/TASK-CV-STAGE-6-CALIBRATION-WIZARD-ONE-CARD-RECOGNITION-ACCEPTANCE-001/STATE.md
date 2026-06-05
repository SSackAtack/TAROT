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

## Kolejne kroki

1. Przy kolejnym uruchomieniu użyć `.bat`; jeśli wykryje zajęte porty `5173/8765/8766`, wybrać opcję automatycznego zatrzymania starej sesji.
2. Fizycznie poruszyć kartą/ręką nad stołem i odłożyć kartę Gilded stabilnie na 2-3 sekundy podczas aktywnego scenariusza `one_card`.
3. Sprawdzić nowy plik `logs/autotune_sessions/*one_card*sample_collected.json` albo `*recommendation_ready.json`.
4. Na podstawie `recognition_debug` określić root cause: `not_enough_crop_descriptors`, `insufficient_good_matches`, `insufficient_inlier_ratio` albo inny powód.
5. Dopiero po root cause zdecydować, czy potrzebny jest mały fix, czy raport `DIAGNOSTIC_COMPLETE_FIX_REQUIRED`.
