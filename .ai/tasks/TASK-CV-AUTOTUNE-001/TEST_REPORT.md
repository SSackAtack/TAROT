# Raport z Testów — TASK-CV-AUTOTUNE-001

## 1. Testy Automatyczne Backend (Python)
* **Status:** `PASS`
* **Komenda uruchomienia:** `python -m unittest discover tests` w katalogu `app_cv`

### Wynik konsoli:
```text
Ran 187 tests in 0.716s

OK
========================================
[TAROT VISION] Computer Vision Module v2.0 (Audited)
========================================
[LOG] Katalog logow: E:\Antigravity\Projekty\TAROT\logs
[INFO] Wykryto 3 aktywne talie do zaladowania w locie: ['rider-waite-smith', 'zodiak', 'magic']
[INFO] Ladowanie cyfrowych wzorcow dla talii 'Rider-Waite-Smith' z E:\Antigravity\Projekty\TAROT\biblioteka_talii\rider-waite-smith\produkcja\wzorce_cv
[WEBSOCKET] Serwer WebSocket dziala pod adresem ws://localhost:8765
[OK] Zaladowano 79 wzorcow dla talii 'Rider-Waite-Smith'!
[INFO] Ladowanie cyfrowych wzorcow dla talii 'Zodiak' z E:\Antigravity\Projekty\TAROT\biblioteka_talii\zodiak\produkcja\wzorce_cv
[OK] Zaladowano 79 wzorcow dla talii 'Zodiak'!
[INFO] Ladowanie cyfrowych wzorcow dla talii 'Magic' z E:\Antigravity\Projekty\TAROT\biblioteka_talii\magic\produkcja\wzorce_cv
[OK] Zaladowano 79 wzorcow dla talii 'Magic'!
[OK] Zaladowano lacznie 237 wzorcow do pamieci (upright + reversed)!
[ARUCO] Modul kalibracji stolu zainicjalizowany (markery ID 10-13, DICT_4X4_50)
```

---

## 2. Testy Kompilacji Frontend (Node/Vite)
* **Status:** `PASS`
* **Komenda uruchomienia:** `npm run build` w katalogu `app_ar`

### Wynik konsoli:
```text
vite v8.0.14 building client environment for production...
transforming...✓ 25 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:   0.31 kB
dist/assets/index-BO9koHBq.css   18.55 kB │ gzip:   4.43 kB
dist/assets/index-Capq_Fqa.js   617.04 kB │ gzip: 158.60 kB
✓ built in 615ms
```

---

## 3. Wyniki Testów Syntetycznych i Autotunera

Wszystkie scenariusze testowe zaimplementowane w `test_auto_tuner.py` przeszły pomyślnie na zielono:
* **Idealny scoring:** Funkcja `score_candidate_quad` ocenia prawidłowy prostokąt karty tarota umieszczony centralnie w kadrze na wynik powyżej `0.8` (bardzo blisko `1.0`).
* **Wykrywanie parametrów na ciemnym tle:** Autotuner poprawnie odnalazł parametry Canny/mode dla syntetycznego prostokąta, zwracając wiarygodność `HIGH` i wysoki score.
* **Rozwiązanie pułapki zagnieżdżania:** Przetestowano wyszukiwanie na obrazie z A4 i zagnieżdżoną kartą. Autotuner w trybie `list` wykazał większą czułość i poprawną ekstrakcję wewnętrznych krawędzi karty niż w trybie `external`.
* **Puste obrazy:** Blank frame zwraca score `0.0` oraz prawidłową niską wiarygodność (`LOW` confidence).
* **Budżet iteracji:** Przetestowano wymuszenie budżetu 15 iteracji — autotuner zakończył pętlę zgodnie ze specyfikacją bez przekroczenia limitu.
