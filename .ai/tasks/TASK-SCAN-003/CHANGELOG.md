# Rejestr Zmian (CHANGELOG) — TASK-SCAN-003

Precyzyjny rejestr zmian wprowadzonych w ramach wdrożenia nowej talii Zodiak.

## Dodane pliki i foldery

### Narzędzia
* [prepare_zodiak.py](file:///e:/Antigravity/Projekty/TAROT/scripts/prepare_zodiak.py) — Skrypt asystenta importu talii.

### Biblioteka talii
* [biblioteka_talii/zodiak/info.json](file:///e:/Antigravity/Projekty/TAROT/biblioteka_talii/zodiak/info.json) — Metadane nowej talii.
* `biblioteka_talii/zodiak/mastery/` — Bezstratne pliki źródłowe PNG.
* `biblioteka_talii/zodiak/produkcja/karty/` — Lekkie pliki `.webp` wysokości 1200px z przezroczystością.
* `biblioteka_talii/zodiak/produkcja/miniatury/` — Lekkie miniatury `.webp` o wysokości 150px.
* `biblioteka_talii/zodiak/produkcja/wzorce_cv/` — Zoptymalizowane JPG 500px na czarnym tle do CV.

### Frontend
* `app_ar/public/karty/Zodiak_00.webp` do `Zodiak_77.webp` i `Zodiak_back.webp` — Kopia tekstur AR w publicznym folderze frontendu.

---

## Modyfikowane pliki produkcyjne

### Backend CV
* [app_cv/main.py](file:///e:/Antigravity/Projekty/TAROT/app_cv/main.py) — Dynamiczne ładowanie wzorców z wybranej katalogu talii na podstawie zmiennej środowiskowej `TAROTVISION_DECK`.

### Frontend AR
* [app_ar/src/renderer/textureCache.js](file:///e:/Antigravity/Projekty/TAROT/app_ar/src/renderer/textureCache.js) — Rozszerzenie `cardNames` o dynamiczny preload i wsparcie w locie dla obu talii (RWS i Zodiak).

### Skrypty uruchomieniowe
* [start_tarotvision.bat](file:///e:/Antigravity/Projekty/TAROT/start_tarotvision.bat) — Interaktywne menu wyboru talii w języku polskim oraz przekazanie zmiennej środowiskowej do procesu serwera CV.

### Dokumentacja AI
* [.ai/PROJECT_STATE.md](file:///e:/Antigravity/Projekty/TAROT/.ai/PROJECT_STATE.md) — Dodanie opisu integracji nowej talii do listy ukończonych prac.
* [.ai/TASKS_INDEX.md](file:///e:/Antigravity/Projekty/TAROT/.ai/TASKS_INDEX.md) — Dodanie wpisu o TASK-SCAN-003.
