# Changelog: TASK-SCAN-001 (Hardening)

Wszystkie modyfikacje wprowadzone w ramach zadania **TASK-SCAN-001** w celu pełnego uodpornienia i parametryzacji skryptu masowej obróbki skanów kart tarota.

---

## [MODIFY] `scripts/process_scans.py`

* **Wdrożono pełną obsługę parametrów CLI (Linii komend) przy użyciu modułu `argparse`:**
  * Dodano opcję `--background {dark,light,auto}` do sterowania typem tła (domyślnie `dark`).
  * Dodano opcję `--format {png,jpg,webp}` pozwalającą zapisać pliki w bezstratnym PNG, zoptymalizowanym JPG lub WebP (domyślnie `webp`).
  * Dodano opcję `--start-index {0,1}` do wyboru indeksu startowego numeracji (domyślnie `0`).
  * Dodano opcje `--target-width` i `--target-height` do konfiguracji docelowego rozmiaru kart.
  * Dodano opcję `--quality` (domyślnie `95`) regulującą jakość kompresji formatów JPG/WebP.

* **Zaimplementowano automatyczną detekcję jasności tła (`--background auto`):**
  * Dodano funkcję `detect_background_dark(img_gray)`, która pobiera próbki pikseli wzdłuż ramki zewnętrznej arkusza (szerokość 15 px) i oblicza ich medianę.
  * Jeśli mediana jasności jest niska (< 100), tło klasyfikowane jest jako ciemne (np. czarna podkładka), w przeciwnym razie jako jasne (zamknięta biała pokrywa).

* **Ulepszono generowanie zaokrąglonych rogów i rzuty typów:**
  * Maska przezroczystości zaokrąglonych rogów jest aplikowana jako kanał alfa dla formatów PNG i WebP.
  * Dla formatu JPG, który nie obsługuje kanału alfa, rogi są automatycznie wypełniane kolorem tła (czarnym dla ciemnego tła, białym dla jasnego tła) z użyciem `np.where`.
  * Zaimplementowano rzutowanie typu na `uint8` za pomocą `.astype(np.uint8)` w operacjach na maskach JPG, co wyeliminowało ostrzeżenie OpenCV `depth image fallback to CV_8U`.

* **Wdrożono zaawansowane statystyki i raport końcowy:**
  * Po przetworzeniu wszystkich plików skrypt wyświetla w konsoli premium tabelę ze szczegółowym podsumowaniem: łączna liczba arkuszy, liczba wyciętych kart, czas wykonania operacji oraz dokładne zliczenie kart dla każdego pliku wejściowego.

* **Zapewniono kompatybilność kodowania znaków:**
  * Usunięto znaki Unicode (strzałki `➔`) z komunikatów `print`, zastępując je standardowymi znakami ASCII `->` w celu całkowitego zapobieżenia błędom `UnicodeEncodeError` w terminalu Windows (kodowanie CP1250).
