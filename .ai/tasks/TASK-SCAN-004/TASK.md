# TASK-SCAN-004: Poprawa orientacji i segmentacji tła w skanerze

## Opis zadania
Zadanie polega na rozwiązaniu problemu z błędną orientacją wycinanych kart (treść obrócona bokiem) oraz słabą segmentacją tła (znikające ciemne karty na ciemnym tle) w skrypcie `scripts/process_scans.py`.

## Zakres (Scope)
* Wdrożenie automatycznej orientacji kart w `scripts/process_scans.py` opartej na heurystycznym scoringu jasnych etykiet (białych pasków) u góry/dole i karaniu pionowych jasnych pasków po bokach (bez użycia ciężkiego OCR).
* Wdrożenie nowej segmentacji opartej na modelu koloru tła (próbki z krawędzi skanu, różnica koloru w przestrzeni LAB/HSV), połączeniu z detektorem krawędzi Canny oraz morfologicznym domknięciu konturów (`MORPH_CLOSE`).
* Poprawa i rozbudowanie logowania oraz debug overlay o parametry wykrytych kart i uzasadnienie wybranej orientacji.

## Pliki dopuszczone do zmiany (Files Allowed to Change)
* `scripts/process_scans.py`
* opcjonalnie `obrob_skany.bat`
* `.ai/tasks/TASK-SCAN-004/*`

## Kryteria akceptacji (Acceptance Criteria)
1. Na skanie testowym z czarnym tłem skrypt wykrywa wszystkie widoczne karty, w tym ciemną kartę „Swords”.
2. Karty poziome (np. `Test_01`) są automatycznie i prawidłowo obracane do pionu.
3. Starsze testy syntetyczne nie wykazują regresji.
4. Opcje `--background auto|dark|light` działają prawidłowo, z nową ulepszoną segmentacją.
5. Log zawiera precyzyjny scoring i uzasadnienie wyboru orientacji dla każdej karty.
