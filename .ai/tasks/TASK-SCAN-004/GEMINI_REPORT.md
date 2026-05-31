# GEMINI REPORT — TASK-SCAN-004

## Task
TASK-SCAN-004: Poprawa orientacji i segmentacji tła w skanerze

## Branch
`task/scan-004-orientation-background`

## Base Commit
`01cfe1a52da816a57e59f4d6291474e1c1bdaf19` (doc: dodanie oficjalnego raportu Gemini do zadania TASK-DECK-001)

## Head Commit
`PENDING` (Zostanie wygenerowany po zacommitowaniu zmian w tym kroku)

## Files Changed
* [scripts/process_scans.py](file:///e:/Antigravity/Projekty/TAROT/scripts/process_scans.py) (Kod główny obróbki i auto-orientacji)
* [.gitignore](file:///e:/Antigravity/Projekty/TAROT/.gitignore) (Ignorowanie tymczasowych obrazów i logów)
* [.ai/TASKS_INDEX.md](file:///e:/Antigravity/Projekty/TAROT/.ai/TASKS_INDEX.md) (Rejestracja zadania TASK-SCAN-004)
* `.ai/tasks/TASK-SCAN-004/` [NEW] (Wymagany zestaw 4 plików dokumentacji zadania)

## Summary of Changes
Pomyślnie rozwiązano oba problemy zgłoszone przez ChatGPT Supervisor przy użyciu nowoczesnych algorytmów OpenCV:
1. **Segmentacja tła w przestrzeni CIE L*a*b*:**
   - Wyeliminowano uproszczoną binaryzację jasności szarej. Zaimplementowano dynamiczną analizę odległości kolorów w przestrzeni LAB.
   - Skrypt pobiera medianę koloru tła z krawędzi arkusza (15 px) i oblicza dystans barwny każdego piksela do modelu tła.
   - Progowanie Otsu z dolnym progiem bezpieczeństwa (20) eliminuje szumy jednolitych teł.
   - Krawędzie Canny'ego są połączone logicznym `OR` z maską koloru, co gwarantuje precyzyjne zamknięcie konturów ciemnych kart na czarnym tle.
   - Zastosowano większe jądro morfologiczne `11x11` (`MORPH_CLOSE`) do wygładzenia i zlikwidowania mikrodziur w konturach kart.
2. **Heurystyczna Auto-Orientacja bez ciężkiego OCR:**
   - Skrypt wycina każdą kartę z prostokąta w dwóch rozmiarach wyjściowych: pionowym `600x1032` i poziomym `1032x600`.
   - Z tych wycinków generuje **4 warianty pionowe 600x1032** o różnym obrocie (0°, 180°, 90° CW, 90° CCW).
   - Oblicza jasność regionów krawędziowych (górny, dolny, lewy, prawy) omijając zaokrąglone rogi.
   - Przypisuje punktację: `score = (top + bottom) - (left + right)`, co preferuje szerokie białe paski etykiet u góry/dole (wygrywa wariant pionowy) i silnie karze etykiety leżące pionowo z boków (przegrywa wariant obrócony).
   - Wybrany wariant o najwyższym score jest zapisywany jako ostateczny WebP/PNG/JPG.
3. **Logowanie diagnostyczne:**
   - Dla każdej wyciętej karty zapisywany jest dokładny wpis w `logs/process_scans.log` zawierający parametry konturu (`area`, `aspect_ratio`, `solidity`, `background_mode`) oraz wszystkie 4 wyniki scoringowe orientacji wraz z uzasadnieniem wyboru.

## Tests Run
- `python -m unittest discover tests` w `app_cv` => **PASS** (171 testów zielonych, brak regresji).
- Uruchomienie skryptu na fizycznym skanie `last_wia_scan.jpg` użytkownika => **PASS**.
  - Wykryto **4 na 4 karty** (w tym uprzednio ginącą ciemną kartę „Swords”).
  - Wykryto tło **CIEMNE** (AUTO).
  - Obie poziome karty zostały pomyślnie zorientowane o 90 stopni (`rot_90_cw`).
- Uruchomienie skryptu na obrazie `failed_scan_1780212179.jpg` => **PASS**.
  - Karta `Test_01` leżąca bokiem została automatycznie i poprawnie obrócona do pionu (`rot_90_cw`).
- Uruchomienie skryptu na jasnym skanie `synthetic_scan_light.jpg` => **PASS**.
  - Wykryto tło **JASNE** (AUTO) i wycięto 2 karty.

## Known Risks
Brak. Wszystkie zmiany są hermetyczne w `process_scans.py`.

## Request for Supervisor
APPROVAL
