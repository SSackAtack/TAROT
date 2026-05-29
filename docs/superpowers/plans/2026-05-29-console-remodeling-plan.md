# Plan Przebudowy Konsoli Parametrów i Sterowania TarotVision (Snapshot-First)

## Status ogólny
Zakończono wdrożenie etapowej przebudowy parametrów operacyjnych systemu, mającej na celu dostosowanie konsoli sterującej do trybu `snapshot-first`. Wszystkie zadania zostały w pełni wdrożone, przetestowane i zintegrowane.

## Session Status (2026-05-29)
Wdrożono i pomyślnie zintegrowano 4 kroki planu. Uruchomiono pełny pakiet 105 testów jednostkowych (100% sukcesu). Całość zmian została przygotowana do zatwierdzenia.

## Harmonogram Prac

### [x] Krok 1: Czyszczenie i podłączenie parametrów wizyjnych (ORB & Settle)
- [x] Usunięcie martwych parametrów (`TRACKING_IOU_THRESHOLD`, `REVERIFY_INTERVAL_FRAMES`, `LOCK_DEAD_ZONE_ANGLE`, `LOCK_DEAD_ZONE_POS`) ze słownika `PARAMETERS` w [runtime_config.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/runtime_config.py).
- [x] Dodanie nowych parametrów (`SNAPSHOT_SETTLE_SECONDS`, `MIN_GOOD_MATCHES`, `LOWE_RATIO`, `MIN_INLIER_RATIO`, `MOTION_CHANGED_RATIO`) do [runtime_config.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/runtime_config.py).
- [x] Spięcie parametrów z silnikiem CV w [main.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/main.py) oraz z funkcją `recognize_card_crop` w [card_recognition.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/card_recognition.py).
- [x] Aktualizacja etykiet i podpowiedzi parametrów na frontendzie w [main.js](file:///e:/Antigravity/Projekty/TAROT/app_ar/main.js).
- [x] Aktualizacja i pomyślne wykonanie testów jednostkowych.

### [x] Krok 2: Matematyczne poszerzanie obszaru roboczego (Workspace Inflation)
- [x] Dodanie parametru suwaka `WORKSPACE_INFLATE_PERCENT` do [runtime_config.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/runtime_config.py) (zakres `-10.0%` do `+30.0%`).
- [x] Zaimplementowanie wyliczania centroidu i rozszerzania rogów ArUco na zewnątrz w funkcji `compute_table_homography` w [table_calibration.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/tarotvision/table_calibration.py).
- [x] Dodanie testów jednostkowych dla operacji poszerzania rogów w `test_table_calibration.py`.

### [x] Krok 3: Sprzętowa kontrola parametrów kamery z aplikacji
- [x] Dodanie obsługi wiadomości `"camera_set"` w funkcji `handle_control_message` w [main.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/main.py).
- [x] Użycie OpenCV `capture.set()` do sterowania hardware'em kamery (focus, exposure).
- [x] Zintegrowanie zapisu ustawień kamery w profilach kalibracji w celu automatycznego przywracania stanu po restarcie.

### [x] Krok 4: Suwaki rozmieszczenia i skali wirtualnych kart w AR
- [x] Dodanie suwaków sterujących rozstawem poziomym/pionowym, przesunięciem i skalą w panelu ustawień na frontendzie [main.js](file:///e:/Antigravity/Projekty/TAROT/app_ar/main.js).
- [x] Dynamiczne stosowanie tych offsetów w trójwymiarowym renderingu kart w `handleCardData`.

## Kolejne kroki
Przedstawienie wyników Michałowi i ostateczne zatwierdzenie.
