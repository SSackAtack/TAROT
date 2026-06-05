# CHANGELOG: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## Wersja 0.2.0 (IN_PROGRESS)

- Utworzono task diagnostyczny dla recognition/acceptance po potwierdzonej stabilizacji geometrii `one_card`.
- Zakres celowo wyklucza dalsze strojenie geometrii oraz zmiany w `active_decks.json`.
- Dodano szczegółową diagnostykę odrzuceń recognition w `app_cv/tarotvision/card_recognition.py`.
- Rozszerzono `SnapshotAnalyzer` o obsługę wyniku `(recognition, debug)` i serializację `recognition_debug`.
- Rozszerzono payload próbek Calibration Wizard o `recognition_debug`.
- Dodano testy jednostkowe dla top rejected match, snapshot diagnostics i zapisu próbki wizardu.
- Dodano hotfix `CameraSession`: na Windows kamera jest otwierana najpierw przez DirectShow (`cv2.CAP_DSHOW`) z fallbackiem do domyślnego backendu, aby ominąć powtarzalny błąd MSMF `grabFrame`.
