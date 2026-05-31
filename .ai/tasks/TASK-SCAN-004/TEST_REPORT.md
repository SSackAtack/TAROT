# Raport z testów (TEST_REPORT) — TASK-SCAN-004

## 1. Testy Automatyczne (Regresja backendu)
Uruchomiono pełny pakiet testów jednostkowych w `app_cv`:
```bash
python -m unittest discover tests
```
Wynik: **171 na 171 testów zakończono powodzeniem (OK)**.
Czas wykonania: `0.314s`. Brak jakiejkolwiek regresji.

---

## 2. Testy Praktyczne Skanowania, Klasyfikacji Geometrycznej i Auto-Orientacji

Uruchomiono pełne przetwarzanie plików wejściowych w katalogu `scans_input` przy użyciu nowej logiki segmentacji tła oraz twardego filtrowania dopuszczalnych wariantów na podstawie fizycznej geometrii karty na skanie.

### Arkusz `last_wia_scan.jpg` (2550x3510 px, Skan użytkownika):
* **Fizyczna liczba kart na skanie:** 5 kart.
* **Liczba wykrytych i wyciętych kart:** 5 na 5 kart (100% skuteczności!).
* **Autodetekcja tła (`--background auto`):** Pomyślnie wykryto tło jako **CIEMNE**.
* **Klasyfikacja geometryczna (Portrait vs Landscape):**
  - Karty leżące fizycznie pionowo (np. `Test_04`): Wykryto orientację pionową (`height_real >= width_real`). Scoring jasności został ograniczony wyłącznie do wariantów `rot_0` i `rot_180`. Karty nie uległy błędnemu obróceniu o 90 stopni, zachowując nienaganny układ pionowy w ramce.
  - Karty leżące fizycznie poziomo (np. `Test_05`): Wykryto orientację poziomą (`width_real > height_real`). Wybór wariantów został zablokowany dla wariantów 0°/180° i ograniczony wyłącznie do wariantów obróconych o 90 stopni (`rot_90_cw` oraz `rot_90_ccw`). 
  - Wszystkie karty zostały wycięte z zachowaniem pionowego formatu w pliku wyjściowym, co gwarantuje pełną estetykę i zero spłaszczeń.
* **Wykrycie ciemnej karty „Swords” (zlewającej się z czarnym tłem):** 
  - Karta została bezbłędnie wycięta z poprawnym domknięciem krawędzi (detekcja barwna LAB + Canny).

### Arkusz `failed_scan_1780212179.jpg` (2550x3510 px):
* **Liczba wykrytych kart:** 1 karta (`Test_01.webp`).
* **Klasyfikacja geometryczna:** Wykryto orientację poziomą (`width_real > height_real`). 
* **Auto-orientacja:** Karta została pomyślnie obrócona o 90 stopni do pionu (`rot_90_cw`).

### Arkusz `failed_scan_1780212149.jpg` (850x1170 px, Karta `Test_00`):
* **Liczba wykrytych kart:** 1 karta (`Test_00.webp`).
* **Klasyfikacja geometryczna:** Karta leży pionowo na skanie (`height_real >= width_real`). 
* **Auto-orientacja:** Dzięki twardej blokadzie, program zablokował warianty `rot_90_cw` i `rot_90_ccw` i zapisał wariant `rot_0`. Karta `Test_00` wylądowała w ramce w 100% pionowo! Błąd obrotu bokiem został całkowicie wyeliminowany.

### Arkusz `synthetic_scan_light.jpg` (2000x3000 px):
* **Autodetekcja tła (`--background auto`):** Pomyślnie wykryto tło jako **JASNE** (Otsu dało stabilny próg 62.0 dla odległości LAB).
* **Liczba wyciętych kart:** 2 karty.

---

## 3. Wygenerowane Pliki Wyjściowe

Wszystkie pliki zostały pomyślnie zapisane w folderze `scans_output/`:
* `Test_00.webp` do `Test_12.webp` (wycięte karty).
* Obrazy debugowe podglądu konturów:
  - `debug_failed_scan_1780212149.jpg`
  - `debug_failed_scan_1780212179.jpg`
  - `debug_last_wia_scan.jpg`
  - `debug_synthetic_scan_light.jpg`
  - (i inne).
