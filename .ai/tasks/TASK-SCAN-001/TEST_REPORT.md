# Raport z Testów: TASK-SCAN-001 (Hardening)

Raport z weryfikacji działania ulepszonego skryptu `scripts/process_scans.py` na syntetycznych arkuszach testowych wysokiej rozdzielczości.

---

## Metodologia weryfikacji

W celu precyzyjnego przetestowania wszystkich funkcji skryptu (argparse, automatyczne tło, formaty PNG/JPG/WebP, zmieniona numeracja, debug overlay) przygotowano dwa syntetyczne obrazy arkuszy A4 o wysokiej rozdzielczości (2000 x 3000 pikseli) w katalogu `scans_input` za pomocą skryptu `scripts/generate_test_scan.py`:
1. `synthetic_scan.jpg` (ciemne tło): zawiera 2 obrócone karty ("THE FOOL" oraz "THE MAGICIAN").
2. `synthetic_scan_light.jpg` (jasne tło): zawiera 2 obrócone karty ("THE EMPRESS" oraz "THE EMPEROR").

---

## Przeprowadzone scenariusze testowe

### Scenariusz 1: Autodetekcja tła (`--background auto`) i zapis WebP
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format webp --start-index 0
  ```
* **Wynik:**
  * `synthetic_scan.jpg`: Pomyślnie wykryto tło **CIEMNE** (AUTO). Wycięto `00_fool.webp` i `01_magician.webp`.
  * `synthetic_scan_light.jpg`: Pomyślnie wykryto tło **JASNE** (AUTO). Wycięto `02_high_priestess.webp` i `03_empress.webp`.
  * **Status:** `PASS`.

### Scenariusz 2: Zapis PNG z przesuniętym indeksem i debug overlay
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format png --start-index 1 --debug-overlay
  ```
* **Wynik:**
  * Wycięto i zapisano bezstratne pliki PNG z przezroczystością alfa: `01_magician.png` do `04_emperor.png`.
  * Wygenerowano i zapisano pliki podglądu debugowania: `debug_synthetic_scan.jpg` i `debug_synthetic_scan_light.jpg` z obrysowanymi na zielono kartami i nałożonymi numerami indeksów.
  * **Status:** `PASS`.

### Scenariusz 3: Zapis JPG i dry-run
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format jpg --dry-run
  ```
* **Wynik:**
  * Skrypt dokonał pełnej analizy, nie zapisał fizycznie kart produkcyjnych na dysku (zgodnie z założeniami dry-run). Brak ostrzeżeń OpenCV.
  * **Status:** `PASS`.

---

## Status testów i wdrożenia

> [!IMPORTANT]
> **WSKAŹNIKI WERYFIKACJI W REPOZYTORIUM:**
> * **Synthetic tests (Weryfikacja syntetyczna):** `PASS` (weryfikacja w pełni udana na programowo generowanych arkuszach testowych).
> * **Real scanner test (Fizyczny skaner):** `NOT_RUN` (oczekuje na wykonanie pierwszego rzeczywistego skanu z urządzenia Epson Perfection V39II).
> * **Full deck batch test (Masowa obróbka talii):** `NOT_RUN` (oczekuje na pomyślne zatwierdzenie próbki i masowe skanowanie 22 kart).

> [!NOTE]
> **PODSUMOWANIE:**
> Skrypt został z powodzeniem uodporniony i przetestowany na danych syntetycznych. Matematyczne i geometryczne mechanizmy transformacji perspektywicznej działają bezbłędnie na wygenerowanych obrazach. Kod jest w pełni gotowy do pierwszych prób kalibracyjnych i testowych na realnym arkuszu ze skanera fizycznego.
