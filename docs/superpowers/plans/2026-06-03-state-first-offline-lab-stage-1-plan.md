# State-First Offline Lab Stage 1 Plan

## Status ogólny

Nowy kierunek projektu zakłada zakończenie łatania obecnego runtime pipeline i budowę nowego silnika state-first w izolowanym offline labie.

Stan aktualny: wykonano Research Gate dla Stage 1 Difference Detection. Następnym bezpiecznym krokiem jest mały benchmark offline, który porówna kilka prostych metod różnicowania obrazów na zatwierdzonych fixture.

## Session Status (2026-06-03 Codex)

Co zrobiono: utworzono task `TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001`, zapisano macierz technik oraz plan benchmarku. Nie zmieniono runtime, Studio, WebSocket, ArUco ani rozpoznawania kart.

Commit hash: do uzupełnienia po commicie sesji.

## Stan aktualny

Zatwierdzone fixture lokalne:

```text
logs/live_fixtures/event_first_current_debug_verified/
  empty/analysis_frame_0.png
  one_card/analysis_frame_1.png
  three_cards/analysis_frame_3.png
```

Manualna prawda fizyczna:

- `empty`: pusta mata, 4 markery ArUco, brak kart.
- `one_card`: dokładnie jedna karta.
- `three_cards`: dokładnie trzy karty.

## Co zostało zrobione

- [x] Zdefiniowano Research Gate Stage 1.
- [x] Wybrano shortlistę metod `TEST_NOW`.
- [x] Zdefiniowano obowiązkowe pary testowe.
- [x] Zdefiniowano format outputów `matrix.csv`, `report.json`, `report.md` i debug obrazów.
- [x] Zablokowano zmiany runtime w pierwszym etapie.

## Taski

- [x] `TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001`: Research Gate Stage 1 Difference Detection.
- [x] `TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001`: Implementacja izolowanego benchmarku offline.
- [ ] `TASK-CV-OFFLINE-LAB-STAGE-1-DECISION-001`: Supervisor decision po benchmarku.

## Session Status (2026-06-03 Codex benchmark)

Stan aktualny: benchmark offline działa i został uruchomiony na realnych fixture.

Co zostało zrobione: dodano `tools/cv_detection_lab/`, metody Stage 1, CLI benchmarku oraz testy jednostkowe. Benchmark wygenerował `42` wiersze macierzy i `126` obrazów debug w `logs/offline_replay/stage1_diff/`.

Wynik: `gray_absdiff_gaussian` jest aktualną rekomendacją, bo uzyskał `PASS` na wszystkich sześciu parach przy niskim runtime. `gray_absdiff_median`, `lab_absdiff_weighted` i `hsv_absdiff_weighted` również uzyskały komplet `PASS`, ale są wolniejsze albo bardziej kosztowne. `gray_absdiff_otsu` i `illumination_normalized_gray_absdiff` failują na scenariuszach trzech kart przez nadmierną fragmentację albo zbyt duże regiony.

Kolejne kroki: decyzja supervisorska Stage 1. Jeżeli overlaye są zgodne z fizyczną prawdą, zatwierdzić `gray_absdiff_gaussian` jako `APPROVED_STAGE_METHOD` i przejść do Stage 2 Region Segmentation.

## Plan wykonanego taska: TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001

### Cel

Zaimplementować minimalny offline benchmark detekcji różnic między obrazami na fixture `empty`, `one_card`, `three_cards`.

### Scope

Dozwolone:

- `tools/cv_detection_lab/`
- `app_cv/tests/test_cv_detection_lab_*.py` albo testy narzędzia w konwencji repo
- `.ai/tasks/TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001/`

Zakazane:

- zmiany `app_cv/tarotvision/pipelines/snapshot_first.py`
- zmiany `app_cv/tarotvision/snapshot_analyzer.py`
- zmiany `app_cv/tarotvision/change_detection.py`
- zmiany `app_cv/main.py`
- zmiany `app_ar/`
- nowe biblioteki bez approval

### Minimalna architektura narzędzia

```text
tools/cv_detection_lab/
  README.md
  stage1_diff_benchmark.py
  methods.py
  report.py
```

Minimalny CLI:

```powershell
python tools/cv_detection_lab/stage1_diff_benchmark.py `
  --fixture logs/live_fixtures/event_first_current_debug_verified `
  --output logs/offline_replay/stage1_diff
```

### Metody do zaimplementowania w benchmarku

- `gray_absdiff_fixed`
- `gray_absdiff_gaussian`
- `gray_absdiff_median`
- `lab_absdiff_weighted`
- `hsv_absdiff_weighted`
- `gray_absdiff_otsu`
- `illumination_normalized_gray_absdiff`

### Pary testowe

- `empty -> empty`
- `empty -> one_card`
- `empty -> three_cards`
- `one_card -> three_cards`
- `one_card -> empty`
- `three_cards -> empty`

### Output

```text
logs/offline_replay/stage1_diff/
  matrix.csv
  report.json
  report.md
  <method>/<pair>/diff.png
  <method>/<pair>/mask.png
  <method>/<pair>/regions_overlay.png
```

### Kryteria akceptacji

- Benchmark uruchamia się offline bez kamery i bez Studio.
- Benchmark używa zatwierdzonych fixture jako wejścia.
- Każda metoda generuje metryki i debug obrazy.
- `matrix.csv` zawiera co najmniej: method, pair, runtime_ms, changed_area_ratio, region_count, expected_region_count, verdict.
- `report.md` wskazuje rekomendowaną metodę i backup method albo jasno mówi, że Stage 1 wymaga zmian.
- Testy jednostkowe sprawdzają parsing fixture, uruchomienie co najmniej jednej metody na syntetycznych obrazach i zapis raportu.

## Kolejne kroki

Natychmiastowy następny krok dla kolejnego modelu: przejrzeć `logs/offline_replay/stage1_diff/gray_absdiff_gaussian/*/regions_overlay.png` oraz `gray_absdiff_median` jako backup. Po zatwierdzeniu Stage 1 utworzyć `TASK-CV-OFFLINE-LAB-STAGE-1-DECISION-001` albo bezpośrednio plan Stage 2 Region Segmentation, jeżeli Michał zaakceptuje wynik.
