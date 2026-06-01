# GEMINI LIVE TEST HANDOFF — TASK-CV-GEOMETRY-FALLBACK-001

## Cel

Wykonac live smoke test po integracji Studio + podglad kamery + potwierdzane czyszczenie kart po zdjeciu ze stolu. Celem nie jest dodawanie nowych algorytmow, tylko zebranie twardych danych z aktualnej implementacji.

## Branch

`codex/snapshot-first-recognition-hardening`

## Co jest juz wdrozone

- Studio pokazuje realny podglad kamery z backendu CV przez `http://localhost:8766/video_feed.mjpg`.
- Launcher `start_tarotvision_studio.bat` domyslnie wylacza osobne okno OpenCV przez `TAROTVISION_DISABLE_OPENCV_PREVIEW=1`.
- W Studio dodano sekcje `Kamera sprzetowo` z przyciskiem `Odczyt kamery` i suwakami Focus/Exposure/Brightness/Contrast.
- Reczne ustawienia focusu sa zapisywane z wartosci zadanej przez operatora, a nie z wadliwego readbacku kamery.
- Detekcja kart ma fallback `minAreaRect` oraz metryki `snapshot_detection_*`.
- Po zabraniu karty pipeline czysci layout dopiero po 2 kolejnych pustych snapshotach.

## Procedura testu live

1. Uruchom system przez:

```bat
start_tarotvision_studio.bat
```

2. Potwierdz, ze:

- otwiera sie `http://localhost:5173/?studio=1`,
- w Studio widac realny obraz kamery,
- nie otwiera sie osobne okno OpenCV,
- w logu CV pojawia sie `Browser preview MJPEG: http://localhost:8766/video_feed.mjpg`.

3. W Studio kliknij `Odczyt kamery`, ustaw ostrosc suwakiem `Ostrosc`, potem zrestartuj backend CV i sprawdz, czy wartosc focusu wraca.

4. Test pustej maty:

- kliknij `Wyczysc mate (Clear)` z panelu operatora albo przez `?operator=1`, jesli potrzeba,
- przy pustej macie kliknij `Ucz maty (Capture)`,
- oczekiwane: `card_count=0`, brak false positives.

5. Test dodania karty:

- poloz jedna znana karte Gilded,
- zapisz fizyczna karte i wynik systemu,
- oczekiwane: `card_count=1`.

6. Test zabrania karty:

- zabierz karte ze stolu,
- oczekiwane: po 2 pustych snapshotach Studio przechodzi do `cards 0`,
- w logach powinno pojawic sie `cards_removed_count`.

7. Test trudnej karty z odblaskiem/tasma:

- poloz karte z problematycznym odblaskiem,
- sprawdz, czy `snapshot_min_area_rect_accepted` rosnie.

## Metryki do zapisania z `logs/cv_metrics.jsonl`

Dla kazdej proby zanotuj:

- fizyczna karta na stole,
- wynik `cards[].name`,
- `cards[].confidence`,
- `snapshot_quads_found`,
- `snapshot_detection_quads_final`,
- `snapshot_min_area_rect_candidates`,
- `snapshot_min_area_rect_accepted`,
- `snapshot_strict_quad_candidates`,
- `snapshot_recognition_attempts`,
- `snapshot_recognition_rejections`,
- `snapshot_background_mask_nonzero_ratio`,
- `cards_removed_count`,
- `layout_changed`,
- `runtime.table.marker_ids`.

## Interpretacja wynikow

- Jesli karta nie jest rozpoznana, ale `snapshot_min_area_rect_accepted > 0`, geometria juz generuje kandydata; kolejny problem jest w cropie, orientacji albo ORB.
- Jesli karta nie jest rozpoznana i `snapshot_min_area_rect_accepted = 0`, obecny fallback geometryczny nie wystarcza; nastepny krok to Hough diagnostics spike, jeszcze bez produkcyjnego 3/2/1-edge runtime.
- Jesli pusta mata daje `card_count > 0`, to jest blocker false positive i nie nalezy luzowac detekcji dalej.
- Jesli po zabraniu karty `cards_removed_count` nie rosnie, trzeba sprawdzic bramke snapshotu i czy w ogole dochodzi do pustych analiz.
- Jesli `runtime.table.marker_ids` gubi marker `13`, popraw ustawienie kamery/maty tak, zeby dolny prawy marker nie byl przy krawedzi kadru.

## Raport wymagany od Gemini

Po tescie dopisz wynik do `.ai/tasks/TASK-CV-GEOMETRY-FALLBACK-001/TEST_REPORT.md` albo utworz nowy raport live z takim formatem:

```markdown
# GEMINI LIVE REPORT — TASK-CV-GEOMETRY-FALLBACK-001

## Data

2026-06-01

## Sceny

| Scena | Fizyczny stan | Wynik systemu | Metryki kluczowe | Status |
|---|---|---|---|---|
| Pusta mata | ... | ... | ... | PASS/FAIL |
| Dodanie karty | ... | ... | ... | PASS/FAIL |
| Zabranie karty | ... | ... | ... | PASS/FAIL |
| Odblask/tasma | ... | ... | ... | PASS/FAIL |

## Wnioski

- ...

## Rekomendacja

CONTINUE_CURRENT / FIX_CROP_OR_ORB / HOUGH_DIAGNOSTICS_SPIKE / BLOCKER_FALSE_POSITIVE
```

## Zakres poza testem

Nie wdrazac od razu rekonstrukcji 3-edge, 2-edge ani 1-edge. Najpierw musza byc dane z powyzszych metryk.
