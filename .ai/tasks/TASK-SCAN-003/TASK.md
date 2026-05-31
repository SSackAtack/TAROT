# TASK-SCAN-003: Wdrożenie nowej talii Zodiak i dynamiczny wybór w locie

## Opis zadania
Zadanie polega na pełnym zaimportowaniu nowej, fizycznie zeskanowanej talii kart o nazwie "Zodiak" do TarotVision, uelastycznieniu backendu CV, frontendu AR oraz skryptu startowego, tak by system dynamicznie obsługiwał wiele talii.

## Zakres (Scope)
* Przygotowanie asystenta importu i przetworzenie 78 awersów oraz 1 rewersu z formatu PNG (z `scans_output/Zodiak`) do formatu WebP (AR, miniatury) oraz JPG (wzorce CV) z optymalnym skalowaniem.
* Uelastycznienie backendu CV w `app_cv/main.py` – dynamiczne wczytywanie wzorców na podstawie zmiennej środowiskowej `TAROTVISION_DECK`.
* Uelastycznienie frontendu w `app_ar/src/renderer/textureCache.js` – automatyczny preload i wsparcie dla wczytywania w locie obu talii (RWS i Zodiak).
* Rozbudowanie skryptu startowego `start_tarotvision.bat` o interaktywne menu wyboru talii przed uruchomieniem serwera.

## Pliki dopuszczone do zmiany (Files Allowed to Change)
* `app_cv/main.py`
* `app_ar/src/renderer/textureCache.js`
* `start_tarotvision.bat`
* `.ai/TASKS_INDEX.md`
* `.ai/PROJECT_STATE.md`
* `scripts/prepare_zodiak.py` (Nowy)
* `biblioteka_talii/zodiak/` (Nowy)
* `app_ar/public/karty/Zodiak_*.webp` (Nowe)

## Kryteria akceptacji (Acceptance Criteria)
- Pomyślne przetworzenie 78 awersów i 1 rewersu talii Zodiak.
- Pełna integracja bez regresji na starych kartach RWS.
- Wszystkie 171 testów jednostkowych w `app_cv` muszą kończyć się sukcesem.
- Skrypt `.bat` poprawnie uruchamia wybraną talię.
