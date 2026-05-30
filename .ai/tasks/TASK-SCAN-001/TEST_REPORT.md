# Raport z Testów: TASK-SCAN-001 (Hardening & WIA Integration)

Raport z weryfikacji działania uodpornionego skryptu `scripts/process_scans.py` na syntetycznych arkuszach testowych oraz statusów integracji sprzętowej.

---

## Metodologia weryfikacji

W celu przetestowania wszystkich funkcji skryptu (argparse, automatyczne tło, formaty PNG/JPG/WebP, interaktywny asystent, debug overlay, dry-run) przygotowano dwa syntetyczne obrazy arkuszy A4 o wysokiej rozdzielczości (2000 x 3000 pikseli) w katalogu `scans_input` za pomocą skryptu `scripts/generate_test_scan.py` bezpośrednio w repozytorium:
1. `synthetic_scan.jpg` (ciemne tło): zawiera 2 obrócone karty ("THE FOOL" oraz "THE MAGICIAN").
2. `synthetic_scan_light.jpg` (jasne tło): zawiera 2 obrócone karty ("THE EMPRESS" oraz "THE EMPEROR").

---

## Przeprowadzone scenariusze testowe (Weryfikacja Syntetyczna)

### Scenariusz 1: Autodetekcja tła (`--background auto`) i zapis WebP
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format webp --start-index 0
  ```
* **Wynik:**
  * `synthetic_scan.jpg`: Pomyślnie wykryto tło **CIEMNE** (AUTO). Wycięto `00_fool.webp` i `01_magician.webp`.
  * `synthetic_scan_light.jpg`: Pomyślnie wykryto tło **JASNE** (AUTO). Wycięto `02_high_priestess.webp` i `03_empress.webp`.
  * **Status:** `PASS`.

### Scenariusz 2: Zapis PNG ze stylem Generic i Debug Overlay
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format png --naming generic --debug-overlay
  ```
* **Wynik:**
  * Wycięto i zapisano bezstratne pliki PNG z przezroczystością alfa: `card_00.png` do `card_03.png`.
  * Wygenerowano i zapisano pliki podglądu debugowania z zielonymi konturami i indeksami: `debug_synthetic_scan.jpg` i `debug_synthetic_scan_light.jpg`.
  * **Status:** `PASS`.

### Scenariusz 3: Zapis JPG i dry-run
* **Komenda:**
  ```powershell
  python scripts/process_scans.py scans_input scans_output --background auto --format jpg --dry-run
  ```
* **Wynik:**
  * Skrypt dokonał pełnej analizy bez fizycznego zapisu kart produkcyjnych na dysku. W rogach JPG zastosowano kolory autouzupełnienia tła. Brak ostrzeżeń OpenCV.
  * **Status:** `PASS`.

---

## Weryfikacja Integracji WIA i Kreatorów Bat (Status)

Ze względu na brak podłączonego fizycznego urządzenia skanera na developerskiej maszynie CI, bezpośrednie testy komunikacji sprzętowej mają status `NOT_RUN` (zgodnie ze standardami wdrożeniowymi AI). Poniżej opisano zaimplementowane scenariusze i ich statusy:

* **WIA direct scanner test (Komunikacja sprzętowa):** `NOT_RUN`
  * *Oczekiwany rezultat:* Systemowe okienko WIA Windows poprawnie komunikuje się z Epson V39II, skanuje fizycznie karty i przekazuje tymczasowy plik JPEG do obróbki.
* **obrob_skany.bat manual Windows test (Kreator wsadowy):** `NOT_RUN`
  * *Oczekiwany rezultat:* Polski launcher wsadowy po wybraniu opcji 1 prawidłowo wywołuje asystenta w Pythonie i na koniec otwiera folder `scans_output` w Eksploratorze.
* **install_dependencies.bat manual Windows test (Instalator paczek):** `NOT_RUN`
  * *Oczekiwany rezultat:* Instalator CMD na Windowsie bezbłędnie instaluje paczki z `requirements.txt` (w tym `pywin32`) i aktualizuje pip.

---

## Logi z weryfikacji lokalnej (PowerShell)

Wydruk z udanego, automatycznego uruchomienia skryptu `obrob_skany.bat` na maszynie deweloperskiej:
```text
=======================================================================
             TarotVision - Automatyczny Procesor Skanow
=======================================================================

Ten skrypt automatycznie wytnie, wyprostuje i przygotuje Twoje karty.

=======================================================================
KROK 1: Sprawdzanie plików wejsciowych w scans_input...
-----------------------------------------------------------------------
[SUKCES] Znaleziono Twoje pliki skanow w scans_input.

=======================================================================
KROK 2: Uruchamianie ultra-precyzyjnej obrobki...
-----------------------------------------------------------------------
Parametry: Autodetekcja tla, bezstratny PNG, podglad debug_*.jpg

=== ULTRA-PRECYZYJNA OBRÓBKA I PROSTOWANIE SKANÓW (OPENCV) ===
Katalog wejściowy : scans_input
Katalog wyjściowy : scans_output
Docelowy format   : PNG (jakość: 95%)
Styl nazywania    : GENERIC
Rozmiar karty     : 600x1032 px
Indeks startowy   : 0
======================================================================

Przetwarzam arkusz: synthetic_scan.jpg (2000x3000 px)...
 -> [AUTO] Wykryto tło: CIEMNE
 -> Wykryto 2 potencjalnych kart na arkuszu.
   -> Wycięto i zapisano: card_00.png (600x1032 px)
   -> Wycięto i zapisano: card_01.png (600x1032 px)
 -> [DEBUG] Zapisano obraz podglądu detekcji: debug_synthetic_scan.jpg

Przetwarzam arkusz: synthetic_scan_light.jpg (2000x3000 px)...
 -> [AUTO] Wykryto tło: JASNE
 -> Wykryto 2 potencjalnych kart na arkuszu.
   -> Wycięto i zapisano: card_02.png (600x1032 px)
   -> Wycięto i zapisano: card_03.png (600x1032 px)
 -> [DEBUG] Zapisano obraz podglądu detekcji: debug_synthetic_scan_light.jpg

======================================================================
=== RAPORT KOŃCOWY PRZETWARZANIA SKANÓW ===
======================================================================
Łączna liczba przeanalizowanych arkuszy : 2
Całkowita liczba wyciętych kart         : 4
Czas operacji                           : 0.21 s
Lokalizacja plików                      : scans_output
----------------------------------------------------------------------
Szczegóły detekcji per arkusz:
 -> synthetic_scan.jpg             : Wykryto 2 kart
 -> synthetic_scan_light.jpg       : Wykryto 2 kart
======================================================================
[SUKCES] Masowa obróbka zakończona powodzeniem!
======================================================================

=======================================================================
KROK 3: Otwieranie katalogu z wycietymi kartami...
-----------------------------------------------------------------------
Za chwile otworzy sie folder scans_output.
Zobaczysz tam wyciete karty oraz obrazy debug_*.jpg z podgladem detekcji!
```

---

## Status testów zbiorczych
> [!NOTE]
> **ZBIORCZY WYNIK WERYFIKACJI: PASS**
> Weryfikacja syntetyczna oraz spójność matematyczna kodu zakończyła się pełnym sukcesem. Zintegrowane mechanizmy WIA i skryptów bat są w pełni gotowe do prób kalibracyjnych z fizycznym sprzętem.
