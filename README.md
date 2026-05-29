# TarotVision -- Hybrydowy System Wizualizacji Tarota

**System rozpoznawania kart tarota z cyfrowa wizualizacja AR dla kanalu YouTube.**

## Wizja

Kamera rozpoznaje fizycznie rozkladane karty tarota, a aplikacja generuje perfekcyjna cyfrowa wizualizacje w czasie rzeczywistym. Widz na YouTube widzi pieknie animowane karty + realne rece czytelniczki, slyszac autentyczna interpretacje.

## Status

**Proof of Concept ZREALIZOWANY** -- system dziala w czasie rzeczywistym z detekcja wielu kart, WebSocket i wizualizacja 3D.

Aktualny PoC rozpoznaje 22 karty Wielkich Arkanow Rider-Waite-Smith przez ORB/FLANN. Domyslna wizualizacja AR uzywa uporzadkowanego snap-to-layout, bo jest to lepsze dla czytelnego kadru YouTube. Dokladne odwzorowanie fizycznych pozycji kart pozostaje opcja na pozniejszy etap.

Nastepny kierunek rozwoju CV: architektura state-first, czyli `identify once -> track cheaply -> reverify when needed`. System ma rozpoznawac nowa karte raz, usuwac ja z puli dostepnych kart, sledzic zablokowane karty tanio po konturze/ROI i uruchamiac pelna rewalidacje tylko przy podejrzeniu zmiany albo w interwale kontrolnym. Mata z markerami ArUco, korekcja perspektywy stolu, detekcja prostokatow kart, crop/deskew i rozpoznawanie cropow pozostaja docelowym pipeline. YOLO/ONNX/OpenVINO/CUDA traktujemy jako wariant benchmarkowy i mozliwy silnik produkcyjny, jesli testy na realnych nagraniach pokaza przewage nad klasycznym CV.

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
W `runtime` widac tez `schedule_mode` (`empty_scan`, `boost_scan`, `steady_scan`), `boost_frames_remaining`, `available_card_count`, `tracked_card_count`, `reverify_interval_frames` oraz `tracking_iou_threshold`.
W metrykach pomocniczych dla state-first CV dochodza `motion_changed_ratio`, `reverify_due_count`, `tracked_assignments`, `unoccupied_observed_boxes` i `tracking_reverify_count`.

### Konsola operatorska

Domyslny adres `http://localhost:5173/` pozostaje czystym overlayem do OBS. Panel diagnostyczno-strojeniowy jest dostepny tylko pod:

```text
http://localhost:5173/?operator=1
```

Konsola pokazuje metryki runtime, aktualne parametry strojenia, ostrzezenia operatora i status profili. Bezpieczne parametry state-first CV, takie jak `LOCK_DEAD_ZONE_POS`, `LOCK_DEAD_ZONE_ANGLE`, `TRACKING_IOU_THRESHOLD`, `REVERIFY_INTERVAL_FRAMES` i `BOOST_AFTER_LAYOUT_CHANGE_FRAMES`, moga byc zmieniane przez WebSocket bez restartu. Zmiany bardziej ryzykowne sa oznaczane jako wymagajace kroku kalibracji/apply.

Profile strojenia zapisywane sa lokalnie w:

```text
logs/calibration_profiles/
```

Probe parametrów kamery (`CAP_PROP_*`) pokazuje wartosc zadana i odczytana. Jesli sterownik kamery ignoruje dany parametr, UI ma traktowac go jako nieobslugiwany zamiast sugerowac, ze suwak dziala.

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
│   ├── main.py          # Detekcja ORB, FLANN, WebSocket server
│   ├── tarotvision/     # Pakiet state-first CV (modul zespolowy)
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

## Dokumentacja

- [Zasady wspolpracy zespolu AI](AGENTS.md) ⬅ **PRZECZYTAJ NAJPIERW**
- [Plan koncepcyjny (FINAL)](docs/plan_koncepcyjny_v4.md)
- [Roadmapa wdrozenia CV](docs/superpowers/plans/2026-05-29-tarotvision-cv-roadmap.md)
- [Plan fazy state-first CV](docs/superpowers/plans/2026-05-29-tarotvision-state-first-cv-plan.md)
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
