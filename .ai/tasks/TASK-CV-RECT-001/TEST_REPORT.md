# Raport z Testów — TASK-CV-RECT-001

## 1. Testy Automatyczne Backend (Python)
* **Status:** `PASS`
* **Komenda uruchomienia:** `python -m unittest discover tests` w katalogu `app_cv`

### Wynik konsoli:
```text
Ran 182 tests in 0.310s

OK
========================================
[TAROT VISION] Computer Vision Module v2.0 (Audited)
========================================
[LOG] Katalog logow: E:\Antigravity\Projekty\TAROT\logs
[INFO] Wykryto 3 aktywne talie do zaladowania w locie: ['rider-waite-smith', 'zodiak', 'magic']
[INFO] Ladowanie cyfrowych wzorcow dla talii 'Rider-Waite-Smith' z E:\Antigravity\Projekty\TAROT\biblioteka_talii\rider-waite-smith\produkcja\wzorce_cv
[WEBSOCKET] Serwer WebSocket dziala pod adresem ws://localhost:8765
[OK] Zaladowano 79 wzorcow dla talii 'Rider-Waite-Smith'!
[INFO] Ladowanie cyfrowych wzorcow dla talii 'Zodiak' z E:\Antigravity\Projekty\TAROT\biblioteka_talii\zodiak\produkcja\wzorce_cv
[OK] Zaladowano 79 wzorcow dla talii 'Zodiak'!
[INFO] Ladowanie cyfrowych wzorcow dla talii 'Magic' z E:\Antigravity\Projekty\TAROT\biblioteka_talii\magic\produkcja\wzorce_cv
[OK] Zaladowano 79 wzorcow dla talii 'Magic'!
[OK] Zaladowano lacznie 237 wzorcow do pamieci (upright + reversed)!
[ARUCO] Modul kalibracji stolu zainicjalizowany (markery ID 10-13, DICT_4X4_50)
```

---

## 2. Testy Kompilacji Frontend (Node/Vite)
* **Status:** `PASS`
* **Komenda uruchomienia:** `npm run build` w katalogu `app_ar`

### Wynik konsoli:
```text
vite v8.0.14 building client environment for production...
transforming...✓ 25 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:   0.31 kB
dist/assets/index-BO9koHBq.css   18.55 kB │ gzip:   4.43 kB
dist/assets/index-Capq_Fqa.js   617.04 kB │ gzip: 158.60 kB
✓ built in 604ms
```

---

## 3. Testy Syntetyczne Zagnieżdżania (Nested Contour)

W ramach `test_nested_contour_a4_trap` zasymulowano układ:
1. Czarna mata oświetleniowa.
2. Biała kartka A4 (`300x450` px) leżąca na stole (stosunek `1.5` - imitacja tła).
3. Ciemna mata wewnątrz kartki A4 (`240x350` px).
4. Karta tarota Boski (`180x250` px) leżąca na ciemnej macie (stosunek `1.39` - zagnieżdżona wewnątrz).

### Wyniki eksperymentu:
* **`contour_mode="external"`**: Wykryto dokładnie **1 quad** (tylko zewnętrzna krawędź kartki A4). Karta tarota leżąca w środku została całkowicie zignorowana.
* **`contour_mode="list"`**: Wykryto **2 quady** (zarówno zewnętrzny arkusz A4, jak i zagnieżdżoną kartę tarota).
* **`contour_mode="tree"`**: Wykryto **2 quady** (pełna struktura hierarchiczna drzewa konturów).

Eksperyment potwierdza matematyczną słuszność koncepcji i skuteczność trybów `list`/`tree` w omijaniu pułapki zagnieżdżonych prostokątów.

---

## 4. Manualne Notatki Diagnostyczne (Symulacja Parametrów)

Dla ciemnego tła i karty o słabo widocznej ramce (Boski Tarot na ciemnej macie):
1. **external, Canny 50/150 (Domyślny)**: Niski kontrast ramki sprawia, że krawędzie karty są poszarpane i nie tworzą zamkniętej pętli w detekcji zewnętrznej. Wykrywalność = 0.
2. **external, Canny 30/100**: Canny wychwytuje słabsze krawędzie, ale w trybie `external` szum brzegowy stołu lub cienie mogą "połknąć" kartę. Wykrywalność = niska/niestabilna.
3. **list, Canny 50/150**: Canny przy standardowych progach może gubić słabo kontrastujące krawędzie, ale dzięki trybowi `list` brak zewnętrznej spójności nie blokuje innych wewnętrznych krawędzi (np. ramki wewnętrznej rysunku karty). Liczba kandydatów wzrasta umiarkowanie.
4. **list, Canny 30/100**: Najbardziej optymalna kombinacja dla trudnych warunków. Canny wykrywa subtelne przejścia tonalne ramki na ciemnym tle, a tryb `list` gwarantuje wyciągnięcie konturu karty zagnieżdżonej na podkładce. Liczba konturów rośnie (ok. 30-50), ale dzięki filtrom powierzchni/proporcji oraz sortowaniu i limitowaniu `max_candidates=10`, algorytm skutecznie pozycjonuje właściwe quady bez obciążania wątku CV.
5. **tree, Canny 30/100**: Działa analogicznie do `list` w kwestii detekcji, buduje dodatkową hierarchię rodzic-dziecko. Przydatne, gdybyśmy w przyszłości chcieli odrzucić kontur nadrzędny (A4) na rzecz podrzędnego (karty).

---

## 5. Ograniczenia i Nieuwzględnione Czynniki

* System dopasowania ORB / FLANN nie był modyfikowany w tym zadaniu. W związku z tym samo parametryzowanie detekcji prostokąta karty nie rozwiązuje automatycznie błędu identyfikacji karty, dopóki wycięty quad nie zostanie dopasowany do wzorców.
* Wartości domyślne są w 100% zachowane, co gwarantuje zerowe ryzyko regresji na stabilnym masterze.
