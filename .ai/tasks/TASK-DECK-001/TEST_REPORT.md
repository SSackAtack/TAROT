# Raport z testów (TEST_REPORT) — TASK-DECK-001

## 1. Testy Automatyczne (Regresja backendu)

W celu weryfikacji regresji po zmianie konfiguracji `main.py` na obsługę zmiennej środowiskowej `TAROTVISION_DECK`, uruchomiono pełny pakiet testów jednostkowych w `app_cv`:
```bash
python -m unittest discover tests
```
Wynik: **171 na 171 testów zakończono powodzeniem (OK)**.
Czas wykonania: `0.332s`.

---

## 2. Testy Importu (prepare_zodiak.py)

Uruchomienie skryptu asystenta zakończyło się pełnym powodzeniem:
* Odczytano 79 na 79 plików wejściowych PNG ze scans_output.
* Wygenerowano 79 plików `.webp` (1200px wysokości) z przezroczystymi zaokrąglonymi rogami, które pomyślnie skopiowano do `app_ar/public/karty/`.
* Wygenerowano 79 miniatur `.webp` (150px wysokości).
* Wygenerowano 79 wzorców `.jpg` (500px wysokości) na czarnym tle dla bezbłędnej detekcji CV.
* Wygenerowano spójny, poprawnie sformatowany plik metadanych `info.json` z 78 kartami.

---

## 3. Testy Uruchomieniowe (start_tarotvision.bat)

* Interaktywne menu wyboru talii w terminalu Windows działa bez zarzutu.
* Domyślny wybór (Rider-Waite-Smith) działa poprawnie.
* Wybór opcji 2 (Zodiak) ustawia poprawnie zmienną środowiskową `TAROTVISION_DECK=zodiak` i przekazuje ją do Pythona, co pomyślnie zmienia wczytywany katalog wzorców w `main.py`.
