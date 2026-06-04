# TarotVision -- Hybrydowy System Wizualizacji Tarota

**System rozpoznawania kart tarota z cyfrowa wizualizacja AR dla kanalu YouTube.**

## Wizja

Kamera rozpoznaje fizycznie rozkladane karty tarota, a aplikacja generuje perfekcyjna cyfrowa wizualizacje w czasie rzeczywistym. Widz na YouTube widzi pieknie animowane karty + realne rece czytelniczki, slyszac autentyczna interpretacje.

## Status

**Proof of Concept ZREALIZOWANY** -- system dziala w czasie rzeczywistym z detekcja wielu kart, WebSocket i wizualizacja 3D.

Aktualny PoC rozpoznaje 22 karty Wielkich Arkanow Rider-Waite-Smith przez ORB/FLANN. Domyslna wizualizacja AR uzywa uporzadkowanego snap-to-layout, bo jest to lepsze dla czytelnego kadru YouTube. Dokladne odwzorowanie fizycznych pozycji kart pozostaje opcja na pozniejszy etap.

Nastepny kierunek rozwoju CV: architektura snapshot-first. System czeka na ustanie ruchu, wybiera najlepszy snapshot, opcjonalnie prostuje mate przez ArUco, wykrywa prostokaty kart, normalizuje cropy i rozpoznaje je przez dopasowanie cech do aktywnych talii. Nie utrzymujemy juz rownoleglego pipeline state-first, zeby nie mieszac decyzji runtime i uproscic diagnostyke. YOLO/ONNX/OpenVINO/CUDA traktujemy jako wariant benchmarkowy i mozliwy silnik produkcyjny dopiero po osobnej decyzji licencyjnej i testach na realnych nagraniach.

## Kluczowe cechy (zaimplementowane)

- **Rozpoznawanie kart** -- ORB feature matching z FLANN-LSH, CLAHE i walidacja geometryczna
- **Wizualizacja AR** -- Three.js z zaokraglonymi kartami 3D o zlotych brzegach (ExtrudeGeometry)
- **Snap-to-layout** -- wirtualne karty sa porzadkowane do czytelnej siatki produkcyjnej
- **Preloading GPU** -- 22 tekstury wczytywane przy starcie, zero stutteringu w OBS
- **WebSocket real-time** -- komunikacja Python <-> przegladarka z debouncing i EMA smoothing
- **Biblioteka talii** -- Rider-Waite-Smith, 22 karty Wielkie Arkana

## Architektura

```
[Kamera USB] -> [Python: OpenCV + ORB + FLANN] -> [WebSocket :8765] -> [Vite + Three.js :5173] -> [OBS] -> [YouTube]
```

### Docelowy pipeline CV

```
[Kamera C310] -> [ArUco mata + korekcja perspektywy] -> [detekcja prostokatow kart] -> [crop + deskew] -> [rozpoznawanie cropow] -> [confidence FSM] -> [WebSocket] -> [snap-to-layout AR]
```

### Docelowa logika stanu

```
UNSEEN -> CANDIDATE_NEW -> IDENTIFIED -> LOCKED_TRACKING -> NEEDS_REVERIFY -> LOST / REMOVED
```

Karty w stanie `LOCKED_TRACKING` nie powinny byc stale rozpoznawane od zera. Sa sledzone przez kontur/ROI, a pelne rozpoznawanie wraca tylko dla nowych, podejrzanych albo okresowo audytowanych kart.

## Stos technologiczny

| Komponent | Technologia |
|-----------|-------------|
| Detekcja kart | Python + OpenCV ORB + FLANN-LSH |
| Preprocessing | CLAHE, Homografia RANSAC, walidacja czworokatow |
| Wizualizacja 3D | Three.js (ExtrudeGeometry, PBR Materials) |
| Komunikacja | WebSocket (JSON, asyncio) |
| Build tool | Vite 8.x |
| Nagrywanie | OBS Studio (Browser Source) |

## Szybki start

### Wymagania
- Python 3.10+
- Node.js 18+
- Kamera USB (np. Anker Work C310)

### Instalacja

```bash
# 1. Zaleznosci Pythona
pip install -r requirements.txt

# 2. Zaleznosci Node.js
cd app_ar
npm install
cd ..
```

### Uruchomienie

**Najprosciej** -- kliknij dwukrotnie `start_tarotvision.bat`

Launcher uruchamia:

- frontend AR/Vite pod `http://localhost:5173/`,
- modul CV/Python z oknem OpenCV,
- WebSocket pod `ws://localhost:8765/`,
- zapis diagnostyki w katalogu `logs/`.

Najwazniejsze pliki diagnostyczne:

- `logs/cv_metrics.jsonl` -- probki metryk CV co okolo 1 sekunde,
- `logs/cv_runtime.log` -- zdarzenia CV/WebSocket,
- `logs/ar_vite.log` -- log terminala Vite,
- `logs/launcher.log` -- start launchera.

Przy starcie przez launcher `cv_metrics.jsonl`, `cv_runtime.log` i `ar_vite.log` opisuja biezacy przebieg testowy, zeby nowe pomiary nie mieszaly sie ze starymi.
W `runtime` widac profil pracy, indeks kamery, rozdzielczosc przechwytywania oraz status blokady focus/exposure.
W metrykach snapshot-first CV dochodza `motion_changed_ratio`, `stable_for_ms`, `snapshot_quality_score`, `snapshot_analysis_ms`, `snapshot_rejected_count`, `layout_publish_count`, `recognition_score`, `snapshot_candidate_validation_rejections` oraz `time_from_motion_to_publish_ms`.

### Tryb snapshot-first CV

Tryb snapshot-first jest jedyna produkcyjna sciezka CV. Uruchamia lekki watcher ruchu, czeka na stabilny uklad kart i analizuje pojedyncza dobra klatke zamiast stale rozpoznawac tozsamosc kart w kazdej klatce.

Startowe parametry sa konserwatywne: okolo 3 sekund stabilnosci, 3 snapshoty kontrolne i publikacja tylko zatwierdzonego ukladu. Overlay w przegladarce trzyma ostatni dobry wynik podczas ruchu lub odrzucenia snapshotu.

Metryki tego trybu obejmuja m.in. `stable_for_ms`, `snapshot_quality_score`, `snapshot_analysis_ms`, `snapshot_rejected_count`, `layout_publish_count`, `recognition_score`, `snapshot_candidate_validation_rejections` oraz `time_from_motion_to_publish_ms`.

### Benchmark snapshot recognition

Lokalne probki operatorskie trzymaj poza commitem w konwencji:

```text
testdata/snapshots/{deck_id}/{mat_id}/*.jpg
```

Kontrakt CSV benchmarku uruchamia:

```powershell
python scripts/benchmark_snapshot_recognition.py --input testdata/snapshots --output logs/snapshot_benchmark.csv
```

Pierwsza wersja skryptu stabilizuje format wejscia i wyjscia. Integracja z realnym `SnapshotAnalyzer` bedzie osobnym krokiem po zebraniu probek z fizycznej kamery.

### Konsola operatorska

Domyslny adres `http://localhost:5173/` pozostaje czystym overlayem do OBS. Panel diagnostyczno-strojeniowy jest dostepny tylko pod:

```text
http://localhost:5173/?operator=1
```

Konsola pokazuje metryki runtime, aktualne parametry strojenia, ostrzezenia operatora i status profili. Bezpieczne parametry snapshot-first CV, takie jak `SNAPSHOT_SETTLE_SECONDS`, `MOTION_CHANGED_RATIO` i `WORKSPACE_INFLATE_PERCENT`, moga byc zmieniane przez WebSocket bez restartu. Zmiany bardziej ryzykowne, takie jak `MIN_MATCH_COUNT`, `RATIO_THRESH` i `MIN_INLIER_RATIO`, sa oznaczane jako wymagajace kroku kalibracji/apply.

Profile strojenia zapisywane sa lokalnie w:

```text
logs/calibration_profiles/
```

### Live Auto Tune

Live Auto Tune jest narzedziem operatorskim w Studio, nie automatycznym trybem produkcyjnym. Operator uruchamia kalibracje dla pustej maty, jednej karty albo trzech kart. Backend zbiera stabilne snapshoty, zapisuje realne probki `candidate_count`, `accepted_count`, `recognition_score`, `candidate_validation_rejections` i czas analizy, ocenia kandydackie profile i pokazuje rekomendacje. Profil jest stosowany dopiero po kliknieciu Apply, a zapis do `logs/calibration_profiles/` wymaga komendy Save Profile.

Bezpieczna sekwencja pracy:

1. Uruchom Studio i upewnij sie, ze `CV Explain` pokazuje aktywna talie oraz skalibrowany stol ArUco.
2. W panelu `Auto Tune` wybierz scenariusz: `Pusta mata`, `1 karta` albo `3 karty`.
3. Poczekaj, az status autotuningu pokaze rekomendacje z `score`, `confidence` i parametrami profilu.
4. Kliknij `Apply` tylko wtedy, gdy rekomendacja jest zgodna z realnym obrazem kamery.
5. Zapisz profil dopiero po potwierdzeniu poprawy rozpoznawania w `CV Explain`.

Profil autotuningu zapisany przez backend ma format z metadanymi:

```json
{
  "name": "studio-live-20260602",
  "parameters": {
    "CARD_DETECT_MIN_AREA_RATIO": 0.001,
    "CARD_DETECT_MAX_CANDIDATES": 10.0,
    "WORKSPACE_INFLATE_PERCENT": 6.0
  },
  "source": "autotune",
  "score": 1.25,
  "confidence": "HIGH"
}
```

Probe parametrów kamery (`CAP_PROP_*`) jest teraz bezpiecznym odczytem-only: pokazuje wartosc odczytana, ale nie ustawia focusem, ekspozycja ani kontrastem. Dlaczego: samo wywolanie `cap.set()` dla focus/exposure potrafi przelaczyc niektóre kamery w tryb manualny i rozjechac ostrosc.

**Manualnie:**
```bash
# Terminal 1: Serwer CV
cd app_cv
python main.py

# Terminal 2: Serwer AR
cd app_ar
npm run dev
```

Otworz przegladarke: http://localhost:5173/

## Struktura projektu

```
TAROT/
├── AGENTS.md            # Zasady wspolpracy zespolu AI — PRZECZYTAJ NAJPIERW
├── app_ar/              # Frontend AR (Vite + Three.js)
│   ├── main.js          # Logika Three.js, WebSocket, animacje
│   ├── style.css        # Style CSS
│   └── public/karty/    # 22 tekstur .webp
├── app_cv/              # Backend CV (Python + OpenCV)
│   ├── main.py          # Orkiestracja snapshot-first CV i WebSocket server
│   ├── tarotvision/     # Pakiet snapshot-first CV (modul zespolowy)
│   │   ├── table_state.py       # FSM kart na stole
│   │   ├── motion.py            # Detekcja ruchu sceny
│   │   ├── roi_map.py           # Geometria ROI / IoU
│   │   ├── contour_tracking.py  # Sledzenie konturow (IoU matching)
│   │   ├── audit_policy.py      # Polityka reweryfikacji
│   │   ├── matching_schedule.py # Harmonogram matchingu
│   │   └── metrics.py           # Metryki EMA rolling-window
│   ├── tests/           # Testy jednostkowe (22 testy)
│   ├── test_camera.py   # Diagnostyka kamer
│   └── test_matching.py # Test dopasowania
├── biblioteka_talii/    # Assety graficzne
│   └── rider-waite-smith/
│       ├── produkcja/karty/      # Tekstury produkcyjne (.webp)
│       ├── produkcja/wzorce_cv/  # Wzorce dla CV (.jpg)
│       └── produkcja/miniatury/  # Miniatury (.webp)
├── docs/                # Dokumentacja
├── logs/                # Logi runtime generowane lokalnie przez launcher/CV
├── scripts/             # Skrypty pomocnicze
├── requirements.txt     # Zaleznosci Pythona
└── start_tarotvision.bat # Launcher (Windows)
```

## AI Workflow / Failover

Źródłem prawdy dla pracy agentów jest katalog `.ai/`.

Przed rozpoczęciem taska należy sprawdzić:

1. `.ai/PROJECT_STATE.md`
2. `.ai/TASKS_INDEX.md`
3. właściwy katalog `.ai/tasks/TASK-XXX/`
4. aktualny branch taska
5. wyniki CI / test report

Duże zmiany muszą być dzielone na małe taski obejmujące maksymalnie 1–3 pliki produkcyjne, chyba że Michał zatwierdzi Human Override.

## Dokumentacja

- [Zasady wspolpracy zespolu AI](AGENTS.md) ⬅ **PRZECZYTAJ NAJPIERW**
- [Plan koncepcyjny (FINAL)](docs/plan_koncepcyjny_v4.md)
- [Roadmapa wdrozenia CV](docs/superpowers/plans/2026-05-29-tarotvision-cv-roadmap.md)
- [Plan snapshot-first multideck recognition hardening](docs/superpowers/plans/2026-06-01-snapshot-first-multideck-recognition-hardening-plan.md)
- [Plan panelu kalibracji i auto-tuningu](docs/superpowers/plans/2026-05-29-tarotvision-auto-tuning-plan.md)
- [Synteza analiz AI](analizy/synteza/synteza_glowna.md)
- [Raporty poszczegolnych agentow](analizy/raporty/)

## Sprzet

- Kamera: Anker Work C310 (4K, autofokus AI; mozliwe blokowanie autofocusa i autoekspozycji)
- Laptop docelowy: HP EliteBook 830 G6
- PC developerski / alternatywny do nagran: AMD Ryzen 7 3700X, 16 GB RAM, RTX 3070
- Skaner: Epson Perfection V39II (4800 DPI)

## Zalozenia Wydajnosciowe

Projekt jest rozwijany na mocniejszym PC, ale powinien miec skalowalna sciezke uruchamiania:

- **Tryb baseline** -- klasyczne OpenCV na CPU, docelowo dzialajace rowniez na HP EliteBook 830 G6.
- **Tryb performance** -- ONNX/OpenVINO/CUDA lub YOLO jako opcja dla PC z RTX 3070, jesli benchmarki potwierdza lepsza skutecznosc albo stabilnosc.
- **Tryb produkcyjny kamery** -- podczas nagran blokujemy autofocus i autoekspozycje, zeby ograniczyc zmiany ostrosci, jasnosci i liczby punktow cech miedzy klatkami.

## Zespol

Projekt rozwijany przez **zespol kilku modeli AI** (Codex, Opus, Gemini) koordynowanych przez Michala. Kazdy model moze przejac kontynuacje prac innego modelu. Dzialamy jako spojny zespol — synergia i synteza, nie rywalizacja.

Szczegolowe zasady wspolpracy, konwencje kodu i workflow opisane sa w [AGENTS.md](AGENTS.md). **Kazdy agent AI MUSI przeczytac ten plik przed rozpoczeciem pracy.**

---

*Projekt rozwijany przy wsparciu Antigravity (AI vibe coding) — Codex · Opus · Gemini.*
