# CHANGELOG: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-RECOGNITION-ACCEPTANCE-001

## Wersja 0.2.0 (IN_PROGRESS)

- Utworzono task diagnostyczny dla recognition/acceptance po potwierdzonej stabilizacji geometrii `one_card`.
- Zakres celowo wyklucza dalsze strojenie geometrii oraz zmiany w `active_decks.json`.
- Dodano szczegółową diagnostykę odrzuceń recognition w `app_cv/tarotvision/card_recognition.py`.
- Rozszerzono `SnapshotAnalyzer` o obsługę wyniku `(recognition, debug)` i serializację `recognition_debug`.
- Rozszerzono payload próbek Calibration Wizard o `recognition_debug`.
- Dodano testy jednostkowe dla top rejected match, snapshot diagnostics i zapisu próbki wizardu.
- Dodano hotfix `CameraSession`: na Windows kamera jest otwierana najpierw przez DirectShow (`cv2.CAP_DSHOW`) z fallbackiem do domyślnego backendu, aby ominąć powtarzalny błąd MSMF `grabFrame`.
- Dodano fallback runtime resize: gdy sterownik kamery raportuje inną rozdzielczość niż żądane 1280x720, `CameraSession.read()` skaluje realną klatkę do rozmiaru oczekiwanego przez pipeline.
- Uodporniono wybór backendu kamery: DirectShow jest odrzucany, jeśli próbne klatki są całkowicie czarne, i wtedy `CameraSession` wraca do domyślnego backendu OpenCV/MSMF.
- Uciszono traceback MJPEG preview przy normalnym przerwaniu połączenia klienta (`ConnectionAbortedError`/`OSError`).
- Rozszerzono `start_tarotvision_studio.bat` o kontrolę i opcjonalne zamykanie procesów na portach `5173`, `8765` i `8766`, żeby uniknąć `WinError 10048` oraz startu Studio na starej sesji.
