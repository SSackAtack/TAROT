# TASK-SCAN-001: Dostosowanie Skryptu Obróbki Skanów pod Skaner i Jakość Premium (WIA & CLI Hardening)

## Opis zadania
Zadanie obejmuje gruntowne ulepszenie i utwardzenie skryptu `scripts/process_scans.py` służącego do automatycznego wycinania i prostowania zeskanowanych fizycznych kart tarota. Po rozszerzeniu zakresu, skrypt ma nie tylko obrabiać gotowe pliki, ale także bezpośrednio komunikować się z fizycznym skanerem na systemie Windows za pomocą protokołu WIA (Windows Image Acquisition) oraz prowadzić użytkownika krok po kroku przez proces masowego skanowania za pomocą interaktywnego asystenta.

## Wymagania techniczne
1. **Dwustopniowa skala (Downscaling):** Detekcja konturów na obrazie roboczym, a precyzyjna homografia na oryginalnym obrazie w pełnej rozdzielczości DPI.
2. **Robust Corner Ordering:** Deterministyczne, matematycznie stabilne sortowanie 4 wierzchołków (brak losowych obrotów kart).
3. **Zaokrąglone rogi z kanałem Alfa:** Wycięcie tła w narożnikach karty i zamiana na gładką przezroczystość (wsparcie dla PNG/WebP). Dla JPG automatyczne wypełnianie rogu kolorem tła.
4. **Bezpośrednia integracja sprzętowa (Windows WIA):** Moduł `win32com.client` wywołujący systemowe API WIA do pobrania skanu bezpośrednio z urządzenia (flaga `--scan`).
5. **Interaktywny asystent masowego skanowania:** Flaga `--interactive` uruchamia kreator pętli skanowania, pyta o nazwę talii i liczbę kart, monitoruje limit zliczeń i prowadzi przez kolejne arkusze.
6. **Centrum wsadowe (.bat):** Plik `obrob_skany.bat` dający proste, polskie menu wyboru oraz `install_dependencies.bat` do szybkiej konfiguracji paczek Pythona (w tym `pywin32` dla WIA).

## Ograniczenia i uwagi o jakości
* Bezpośrednie skanowanie WIA w systemie Windows wymusza tymczasowy zapis w formacie JPEG z powodu specyfiki obiektów COM systemu Windows.
* Dla bezkompromisowej jakości master referencyjnego (Master Quality) dla algorytmów CV, zalecany jest tradycyjny workflow: skanowanie do bezstratnego PNG/TIFF w programie zewnętrznym skanera, a następnie masowa obróbka folderu `scans_input`.

## Dozwolony zakres zmian
* `scripts/process_scans.py`
* `scripts/generate_test_scan.py`
* `obrob_skany.bat`
* `install_dependencies.bat`
* `requirements.txt`
