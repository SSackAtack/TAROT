# TarotVision Benchmarking

## Cel

Obiektywna ocena wydajności pipeline CV na nagraniach wideo z kamery
Anker Work C310, bez konieczności uruchamiania systemu na żywo.

## Nagrywanie klipów testowych

Nagraj 5-10 krótkich klipów (10-30 sekund każdy) pod realnymi
warunkami oświetleniowymi. Rekomendowane scenariusze:

1. **Jedna karta** — centrowana na stole
2. **Trzy karty** — rozkład w rzędzie
3. **Sześć kart** — pełny Celtic Cross setup
4. **Zakrywanie ręką** — hand occlusion
5. **Test odblasków** — źródło światła pod kątem
6. **Szybkie układanie** — karta kładzona w trakcie nagrania
7. **Niskie oświetlenie** — przyciemnione pomieszczenie

## Uruchomienie benchmarku

```powershell
python app_cv\benchmark_video.py --video sciezka\do\nagrania.mp4 --output analizy\benchmark_results.csv
```

### Opcje

| Flaga | Opis |
|-------|------|
| `--video` | Ścieżka do pliku wideo (MP4, AVI) — **wymagane** |
| `--output` | Ścieżka do pliku CSV z wynikami (domyślnie: `analizy/benchmark_results.csv`) |
| `--max-frames` | Maksymalna liczba klatek do przetworzenia |
| `--no-display` | Nie wyświetlaj okna podglądu (headless) |

## Metryki w CSV

Każdy wiersz odpowiada jednej klatce wideo:

| Kolumna | Opis |
|---------|------|
| `frame_number` | Numer klatki (0-indexed) |
| `timestamp_sec` | Czas w sekundach |
| `preprocess_ms` | Czas preprocessingu (grayscale + CLAHE) |
| `aruco_ms` | Czas detekcji ArUco markerów |
| `aruco_calibrated` | Czy kalibracja stołu aktywna (True/False) |
| `aruco_markers` | Liczba wykrytych markerów |
| `card_detect_ms` | Czas detekcji prostokątów kart |
| `card_quads_found` | Liczba wykrytych prostokątów |
| `feature_detect_ms` | Czas ekstrakcji ORB features |
| `total_frame_ms` | Łączny czas przetwarzania klatki |

## Profil sprzętowy

Zawsze notuj na jakim sprzęcie uruchomiono benchmark:

- **HP EliteBook 830 G6** — docelowy laptop
- **AMD Ryzen 7 3700X + RTX 3070** — PC produkcyjny
- Stan kamery: focus lock, exposure lock, rozdzielczość

## Wyniki przed YOLO

> **Ważne:** Nie dodawaj YOLO/ONNX/OpenVINO do ścieżki produkcyjnej,
> dopóki benchmark nie pokaże, że klasyczny pipeline CV jest
> niewystarczający. Benchmark jest źródłem prawdy.
