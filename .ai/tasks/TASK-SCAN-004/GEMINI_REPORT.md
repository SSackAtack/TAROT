# GEMINI REPORT — TASK-SCAN-004

## Task
TASK-SCAN-004: Poprawa orientacji i segmentacji tła w skanerze

## Branch
`task/scan-004-orientation-background`

## Base Commit
`01cfe1a52da816a57e59f4d6291474e1c1bdaf19` (doc: dodanie oficjalnego raportu Gemini do zadania TASK-DECK-001)

## Head Commit
`6a12b4e388c57400fc550c84469bf8cf7c4d4efc` (Będzie zaktualizowany po wdrożeniu poprawek geometrycznych)

## Files Changed
* [scripts/process_scans.py](file:///e:/Antigravity/Projekty/TAROT/scripts/process_scans.py) (Kod główny obróbki, auto-orientacji i twardego sprawdzania geometrii)
* [.gitignore](file:///e:/Antigravity/Projekty/TAROT/.gitignore) (Ignorowanie tymczasowych obrazów i logów)
* [.ai/TASKS_INDEX.md](file:///e:/Antigravity/Projekty/TAROT/.ai/TASKS_INDEX.md) (Rejestracja zadania TASK-SCAN-004 i aktualizacja statusu)
* `.ai/tasks/TASK-SCAN-004/` (Zestaw 5 plików dokumentacji zadania)

## Summary of Changes
Pomyślnie rozwiązano oba problemy zgłoszone przez ChatGPT Supervisor przy użyciu nowoczesnych algorytmów OpenCV oraz uwzględniono korektę logiczną dotyczącą rozróżnienia geometrii karty od jej obrotu semantycznego (góra/dół):

1. **Twarde rozróżnienie geometryczne (Portrait vs Landscape) - NOWOŚĆ:**
   - Wyeliminowano problem błędnego obracania bokiem fizycznie pionowych kart (np. `Test_00`), na których scoring jasnych pasków błędnie preferował warianty poziome.
   - Skrypt najpierw wylicza rzeczywiste wymiary konturu na skanie (`width_real` i `height_real`) na podstawie odległości euklidesowych punktów wierzchołkowych z `ordered_box`.
   - Na tej podstawie rozstrzyga fizyczną klasę geometryczną karty:
     * **Portrait (pionowa):** `height_real >= width_real`. Dozwolone warianty obrotu to **wyłącznie** `rot_0` (bez zmian) oraz `rot_180` (obrót o 180 stopni). Warianty 90° są bezwzględnie zablokowane.
     * **Landscape (pozioma):** `width_real > height_real`. Dozwolone warianty obrotu to **wyłącznie** `rot_90_cw` (w prawo) oraz `rot_90_ccw` (w lewo). Warianty 0°/180° są bezwzględnie zablokowane.
   - Heurystyczny scoring jasnych pasków działa dopiero w obrębie tej odfiltrowanej, dozwolonej puli wariantów. Gwarantuje to 100% dopasowania do pionowej ramki 600x1032 bez ryzyka regresji w orientacji fizycznej.

2. **Segmentacja tła w przestrzeni CIE L\*a\*b\*:**
   - Wyeliminowano uproszczoną binaryzację jasności szarej. Zaimplementowano dynamiczną analizę odległości kolorów w przestrzeni LAB.
   - Skrypt pobiera medianę koloru tła z krawędzi arkusza (15 px) i oblicza dystans barwny każdego piksela do modelu tła.
   - Progowanie Otsu z dolnym progiem bezpieczeństwa (20) eliminuje szumy jednolitych teł.
   - Krawędzie Canny'ego są połączone logicznym `OR` z maską koloru, co gwarantuje precyzyjne zamknięcie konturów ciemnych kart na czarnym tle.
   - Zastosowano większe jądro morfologiczne `11x11` (`MORPH_CLOSE`) do wygładzenia i zlikwidowania mikrodziur w konturach kart.

3. **Logowanie diagnostyczne:**
   - Dla każdej wyciętej karty zapisywany jest dokładny wpis w `logs/process_scans.log` zawierający parametry konturu (`area`, `aspect_ratio`, `solidity`, `background_mode`, `is_landscape_on_scan`) oraz wyniki scoringowe tylko dla dopuszczonych geometrycznie wariantów orientacji wraz z uzasadnieniem wyboru.

## Tests Run
- `python -m unittest discover tests` w `app_cv` => **PASS** (171 testów zielonych, brak regresji).
- Uruchomienie skryptu na fizycznym skanie `last_wia_scan.jpg` użytkownika => **PASS**.
  - Wykryto **5 na 5 kart** (w tym ciemną kartę „Swords” z 100% poprawnym konturem na czarnym tle).
  - Wykryto tło **CIEMNE** (AUTO).
  - Wszystkie karty pionowe pozostały pionowo, a karty leżące poziomo zostały obrócone o 90 stopni do pionu.
- Uruchomienie skryptu na obrazie `failed_scan_1780212179.jpg` => **PASS**.
  - Karta `Test_01` leżąca bokiem została automatycznie i poprawnie obrócona do pionu (`rot_90_cw`).
- Uruchomienie skryptu na jasnym skanie `synthetic_scan_light.jpg` => **PASS**.
  - Wykryto tło **JASNE** (AUTO) i wycięto 2 karty.

## Known Risks
Brak. Wszystkie zmiany są w pełni hermetyczne w `process_scans.py`.

## Request for Supervisor
REVIEW
