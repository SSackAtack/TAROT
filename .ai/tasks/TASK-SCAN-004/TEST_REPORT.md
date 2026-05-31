# Raport z testów (TEST_REPORT) — TASK-SCAN-004

## 1. Testy Automatyczne (Regresja backendu)
Uruchomiono pełny pakiet testów jednostkowych w `app_cv`:
```bash
python -m unittest discover tests
```
Wynik: **171 na 171 testów zakończono powodzeniem (OK)**.
Czas wykonania: `0.339s`. Brak jakiejkolwiek regresji.

---

## 2. Testy Praktyczne Skanowania i Auto-Orientacji

Uruchomiono pełne przetwarzanie plików wejściowych w katalogu `scans_input` przy użyciu nowej logiki segmentacji tła i auto-orientacji.

### Arkusz `last_wia_scan.jpg` (2550x3510 px, Skan użytkownika):
* **Fizyczna liczba kart na skanie:** 4 karty.
* **Liczba wykrytych i wyciętych kart:** 4 na 4 karty (100% skuteczności!).
* **Autodetekcja tła (`--background auto`):** Pomyślnie wykryto tło jako **CIEMNE**.
* **Wykrycie ciemnej karty „Swords” (zlewającej się z czarnym tłem):** 
  - Karta została bezbłędnie wycięta jako `Test_05.webp`. 
  - Parametry konturu: `area=381590.0`, `solidity=0.72` (solidity zostało obniżone z powodu flar, ale nowa tolerancja `solidity >= 0.6` oraz krawędzie Canny'ego pomyślnie domknęły kształt!).
* **Auto-orientacja karty obróconej bokiem (`Test_05` i `Test_06`):**
  - Obie karty poziome zostały pomyślnie obrócone do pionu o 90 stopni w prawo (`rot_90_cw`).
  - Przykładowy scoring w logu: `selected_orientation=rot_90_cw (score=109.31)`, `orientation_scores={'rot_0': -108.39, 'rot_180': -108.39, 'rot_90_cw': 109.31, 'rot_90_ccw': 109.31}`. Wynik dodatni 109.31 zdecydowanie pokonał wariant pionowy -108.39!

### Arkusz `failed_scan_1780212179.jpg` (2550x3510 px):
* **Liczba wykrytych kart:** 1 karta (`Test_01.webp`).
* **Auto-orientacja:** Karta `Test_01.webp` (która wcześniej sprawiała problem, bo treść leżała bokiem) została pomyślnie i prawidłowo obrócona o 90 stopni (`rot_90_cw` o wyniku 67.30 vs -67.52 dla braku obrotu!).

### Arkusz `synthetic_scan_light.jpg` (2000x3000 px):
* **Autodetekcja tła (`--background auto`):** Pomyślnie wykryto tło jako **JASNE** (Otsu dało stabilny próg 62.0 dla odległości LAB).
* **Liczba wyciętych kart:** 2 karty.

---

## 3. Wygenerowane Pliki Wyjściowe

Wszystkie pliki zostały pomyślnie zapisane w folderze `scans_output/`:
* `Test_00.webp` do `Test_11.webp` (wycięte karty).
* Obrazy debugowe podglądu konturów:
  - `debug_last_wia_scan.jpg`
  - `debug_failed_scan_1780212179.jpg`
  - `debug_synthetic_scan_light.jpg`
  - (i inne).
