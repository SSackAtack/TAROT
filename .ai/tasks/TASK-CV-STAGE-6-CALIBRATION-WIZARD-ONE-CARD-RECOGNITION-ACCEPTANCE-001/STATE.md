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

## Session Status (2026-06-05)

- Utworzono zakres diagnostyczny nowego taska.
- Ustalono, że nie wolno kontynuować zmian w geometrii bez nowych dowodów.
- Dodano TDD dla raportowania najlepszego odrzuconego matcha w recognition debug.
- Dodano TDD dla przeniesienia recognition debug przez `SnapshotAnalyzer` do diagnostyki snapshotu.
- Dodano TDD dla zapisu `recognition_debug` w próbkach Calibration Wizard.
- Zrestartowano backend i potwierdzono runtime `gilded`.
- Próba zebrania nowego `one_card` nie dała próbek bez fizycznego ruchu.
- Dodano DirectShow-first fallback dla kamery na Windows po powtarzalnym błędzie MSMF `grabFrame`.

## Kolejne kroki

1. Uruchomić backend/launcher po hotfixie i potwierdzić brak nowych ostrzeżeń MSMF `grabFrame`.
2. Fizycznie poruszyć kartą/ręką nad stołem i odłożyć kartę Gilded stabilnie na 2-3 sekundy podczas aktywnego scenariusza `one_card`.
3. Sprawdzić nowy plik `logs/autotune_sessions/*one_card*sample_collected.json` albo `*recommendation_ready.json`.
4. Na podstawie `recognition_debug` określić root cause: `not_enough_crop_descriptors`, `insufficient_good_matches`, `insufficient_inlier_ratio` albo inny powód.
5. Dopiero po root cause zdecydować, czy potrzebny jest mały fix, czy raport `DIAGNOSTIC_COMPLETE_FIX_REQUIRED`.
