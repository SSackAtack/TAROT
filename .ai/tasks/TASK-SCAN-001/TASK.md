# TASK-SCAN-001: Dostosowanie Skryptu Obróbki Skanów pod Skaner i Jakość Premium (WebP AR)

## Opis zadania
Zadanie obejmuje gruntowne ulepszenie skryptu `scripts/process_scans.py` służącego do automatycznego wycinania i prostowania zeskanowanych fizycznych kart tarota. Skrypt musi wspierać wysokiej jakości skany w wysokiej rozdzielczości DPI (Epson Perfection V39II) bez spowalniania działania, automatycznie prostować je z użyciem matematycznie stabilnego porządkowania narożników, wycinać z zaokrąglonymi przezroczystymi brzegami (kanał alfa) oraz zapisywać w formacie WebP z automatycznie przypisanymi nazwami Wielkich Arkanów.

## Wymagania techniczne
1. **Dwustopniowa skala (Downscaling):** Detekcja konturów na obrazie roboczym, a precyzyjna homografia na oryginalnym obrazie w pełnej rozdzielczości.
2. **Robust Corner Ordering:** Deterministyczne sortowanie 4 wierzchołków.
3. **Zaokrąglone rogi z kanałem Alfa:** Wycięcie czarnego tła w narożnikach karty i zamiana na gładką przezroczystość.
4. **Format WebP:** Zapis do lekkiego i nowoczesnego formatu `.webp`.
5. **Autonaming:** Mapowanie nazw do listy 22 Wielkich Arkanów w kolejności numerycznej.

## Dozwolony zakres zmian
* `scripts/process_scans.py`
