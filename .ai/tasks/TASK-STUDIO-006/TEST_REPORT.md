# TASK-STUDIO-006 — Raport z Testów

## 1. Testy Automatyczne

### Backend CV (Python)
- **Komenda**: `python -m unittest discover tests` w katalogu `app_cv`
- **Status**: `PASS` (Green)
- **Wynik**: 176 testów zakończonych pełnym sukcesem (`OK`) w czasie 0.339 sekundy.

```text
Ran 176 tests in 0.339s

OK
========================================
[TAROT VISION] Computer Vision Module v2.0 (Audited)
========================================
[LOG] Katalog logow: E:\Antigravity\Projekty\TAROT\logs
[INFO] Wykryto 3 aktywne talie do zaladowania w locie: ['rider-waite-smith', 'zodiak', 'magic']
...
```

### Frontend AR (Vite/Node)
- **Komenda**: `npm run build` w katalogu `app_ar`
- **Status**: `PASS` (Green)
- **Wynik**: Kod został z sukcesem przetranspilowany, zminifikowany i spakowany. Brak jakichkolwiek błędów w konsoli budowania.

```text
vite v8.0.14 building client environment for production...
transforming...✓ 25 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:   0.31 kB
dist/assets/index-BO9koHBq.css   18.55 kB │ gzip:   4.43 kB
dist/assets/index-Capq_Fqa.js   617.04 kB │ gzip: 158.60 kB
✓ built in 621ms
```

---

## 2. Testy Manualne (Scenariusz Weryfikacyjny)

### Krok 1: Test Launchera
1. Uruchom plik `start_tarotvision_studio.bat` znajdujący się w katalogu głównym projektu.
2. Zostanie wyświetlone konsolowe okno wyboru talii startowej. Wybierz np. `1` (Rider-Waite-Smith).
3. Upewnij się, że automatycznie otwiera się przeglądarka pod adresem `http://localhost:5173/?studio=1`.

### Krok 2: Weryfikacja UI Konsoli
1. Po wejściu pod adres `http://localhost:5173/?studio=1`, upewnij się, że widzisz interfejs Konsoli Studio (z miedzianym brandingiem premium, safe-guides, mikserem itp.).
2. Odszukaj kartę **Diagnostyka CV Health** po prawej stronie.
3. Powinny być tam widoczne wskaźniki (FPS, Cards, Stable Ms, Snapshot).
4. Domyślnie (brak ostrzeżeń) kontener ostrzeżeń jest całkowicie niewidoczny (nie zajmuje niepotrzebnie miejsca na ekranie).

### Krok 3: Weryfikacja Działania Ostrzeżenia
1. Wyślij lub zasymuluj wysłanie payloadu WebSocket, w którym klucz `warnings` posiada tablicę z ostrzeżeniem (np. `["SLABE OSWIETLENIE - Zwieksz jasnosc stolu"]`).
2. W Konsoli Studio natychmiastowo powinien pojawić się stylowy, ciemnoczerwony boks oznaczony jako `⚠️ Ostrzeżenie CV`.
3. Tekst powinien dokładnie odpowiadać wysłanemu ostrzeżeniu.
4. Krawędzie boksu powinny płynnie, dynamicznie pulsować w odcieniach czerwieni i miedzi (`warning-pulse`).
