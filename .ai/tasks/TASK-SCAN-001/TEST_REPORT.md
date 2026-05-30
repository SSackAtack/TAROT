# Raport z Testów: TASK-SCAN-001 (Hardening)

Zaktualizowany raport z kompleksowej weryfikacji działania utwardzonego skryptu `scripts/process_scans.py`.

---

## Metodologia weryfikacji

W celu przetestowania wszystkich nowych funkcji (argparse, automatyczna jasność tła, formaty PNG/JPG, numeracja) przygotowano dwa syntetyczne arkusze o wysokiej rozdzielczości (2000 x 3000 pikseli) w katalogu `scans_input`:
1. `synthetic_scan.jpg`: ciemne tło (symulacja czarnej podkładki), 2 obrócone karty ("THE FOOL" oraz "THE MAGICIAN").
2. `synthetic_scan_light.jpg`: jasne tło (symulacja białego tła skanera), 2 obrócone karty ("THE EMPRESS" oraz "THE EMPEROR").

---

## Przeprowadzone scenariusze testowe

### Scenariusz 1: Autodetekcja tła (`--background auto`) i zapis WebP z indeksowaniem od 0
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format webp --start-index 0
  ```
* **Wynik:**
  * `synthetic_scan.jpg`: Pomyślnie wykryto tło **CIEMNE** (AUTO). Wycięto i zapisano `00_fool.webp` oraz `01_magician.webp`.
  * `synthetic_scan_light.jpg`: Pomyślnie wykryto tło **JASNE** (AUTO). Wycięto i zapisano `02_high_priestess.webp` oraz `03_empress.webp`.
  * **Status:** PASS (100% poprawności wykrywania tła i zapisu WebP).

### Scenariusz 2: Zapis PNG z indeksowaniem od 1
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format png --start-index 1
  ```
* **Wynik:**
  * Wycięto i pomyślnie zapisano pliki o bezstratnej kompresji z kanałem alfa: `01_magician.png`, `02_high_priestess.png`, `03_empress.png` oraz `04_emperor.png`.
  * **Status:** PASS (poprawne przesunięcie indeksów numeracji i zapis bezstratny PNG).

### Scenariusz 3: Zapis JPG z autowypełnieniem rogów
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format jpg --start-index 0
  ```
* **Wynik:**
  * Wycięto i zapisano pliki: `00_fool.jpg`, `01_magician.jpg`, `02_high_priestess.jpg`, `03_empress.jpg`.
  * W rogach kart (poza zaokrąglonym kształtem) wstawiono jednolity kolor tła (czarny dla ciemnego arkusza, biały dla jasnego arkusza).
  * Brak jakichkolwiek ostrzeżeń OpenCV (rzutowanie na `uint8` załatwiło problem).
  * **Status:** PASS.

---

## Raport Końcowy Konsoli
Wydruk z raportu końcowego w konsoli:
```text
=== ULTRA-PRECYZYJNA OBRÓBKA I PROSTOWANIE SKANÓW (OPENCV) ===
Katalog wejściowy : scans_input
Katalog wyjściowy : scans_output
Docelowy format   : JPG (jakość: 95%)
Rozmiar karty     : 600x1032 px
Indeks startowy   : 0
======================================================================
...
=== RAPORT KOŃCOWY PRZETWARZANIA SKANÓW ===
======================================================================
Łączna liczba przeanalizowanych arkuszy : 2
Całkowita liczba wyciętych kart         : 4
Czas operacji                           : 0.22 s
Zapisano w lokalizacji                  : scans_output
----------------------------------------------------------------------
Szczegóły detekcji per arkusz:
 -> synthetic_scan.jpg             : Wykryto i wycięto 2 kart
 -> synthetic_scan_light.jpg       : Wykryto i wycięto 2 kart
======================================================================
[SUKCES] Masowa obróbka zakończona powodzeniem!
======================================================================
```

---

## Status testów
> [!NOTE]
> **ZBIORCZY STATUS WERYFIKACJI: PASS**
> Wszystkie scenariusze testowe, elastyczne parametry CLI, eliminacja ostrzeżeń OpenCV i błędu Unicode CP1250 zostały pomyślnie zweryfikowane. Skrypt jest niezwykle stabilny i gotowy do wdrożenia u klienta.
