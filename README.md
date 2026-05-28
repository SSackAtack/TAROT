# TarotVision -- Hybrydowy System Wizualizacji Tarota

**System rozpoznawania kart tarota z cyfrowa wizualizacja AR dla kanalu YouTube.**

## Wizja

Kamera rozpoznaje fizycznie rozkladane karty tarota, a aplikacja generuje perfekcyjna cyfrowa wizualizacje w czasie rzeczywistym. Widz na YouTube widzi pieknie animowane karty + realne rece czytelniczki, slyszac autentyczna interpretacje.

## Status

**Proof of Concept ZREALIZOWANY** -- system dziala w czasie rzeczywistym z detekcja wielu kart, sledzeniem przestrzennym AR i wizualizacja 3D.

## Kluczowe cechy (zaimplementowane)

- **Rozpoznawanie kart** -- ORB feature matching z FLANN-LSH, CLAHE i walidacja geometryczna
- **Wizualizacja AR** -- Three.js z zaokraglonymi kartami 3D o zlotych brzegach (ExtrudeGeometry)
- **Sledzenie przestrzenne** -- wirtualne karty plynnie podazaja za pozycja i rotacja fizycznych kart
- **Preloading GPU** -- 22 tekstury wczytywane przy starcie, zero stutteringu w OBS
- **WebSocket real-time** -- komunikacja Python <-> przegladarka z debouncing i EMA smoothing
- **Biblioteka talii** -- Rider-Waite-Smith, 22 karty Wielkie Arkana

## Architektura

```
[Kamera USB] -> [Python: OpenCV + ORB + FLANN] -> [WebSocket :8765] -> [Vite + Three.js :5173] -> [OBS] -> [YouTube]
```

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
├── app_ar/              # Frontend AR (Vite + Three.js)
│   ├── main.js          # Logika Three.js, WebSocket, animacje
│   ├── style.css        # Style CSS
│   └── public/karty/    # 22 tekstur .webp
├── app_cv/              # Backend CV (Python + OpenCV)
│   ├── main.py          # Detekcja ORB, FLANN, WebSocket server
│   ├── test_camera.py   # Diagnostyka kamer
│   └── test_matching.py # Test dopasowania
├── biblioteka_talii/    # Assety graficzne
│   └── rider-waite-smith/
│       ├── produkcja/karty/      # Tekstury produkcyjne (.webp)
│       ├── produkcja/wzorce_cv/  # Wzorce dla CV (.jpg)
│       └── produkcja/miniatury/  # Miniatury (.webp)
├── docs/                # Dokumentacja
├── scripts/             # Skrypty pomocnicze
├── requirements.txt     # Zaleznosci Pythona
└── start_tarotvision.bat # Launcher (Windows)
```

## Dokumentacja

- [Plan koncepcyjny (FINAL)](docs/plan_koncepcyjny_v4.md)
- [Synteza analiz AI](analizy/synteza/synteza_glowna.md)
- [Raporty poszczegolnych agentow](analizy/raporty/)

## Sprzet

- Kamera: Anker Work C310 (4K, autofokus AI)
- Skaner: Epson Perfection V39II (4800 DPI)

---

*Projekt rozwijany przy wsparciu Antigravity (AI vibe coding).*
