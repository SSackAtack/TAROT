# YOLO / ONNX / CUDA Experiment

> **Ten eksperyment jest ścieżką wydajnościową, NIE automatycznym
> zastąpieniem klasycznego pipeline CV.**

## Warunki rozpoczęcia ewaluacji

YOLO/ONNX/OpenVINO/CUDA można ewaluować **dopiero gdy istnieją**:

- [x] Skany realnej talii (RWS 22 Wielkie Arkana — `biblioteka_talii/`)
- [ ] Realne nagrania wideo z kamery C310 (min. 5 scenariuszy)
- [ ] Wyniki benchmarku klasycznego CV (`analizy/benchmark_results.csv`)
- [ ] Przegląd implikacji licencyjnych modeli YOLO
- [ ] Testy na obu docelowych platformach (laptop + PC)

## Kryteria sukcesu

YOLO/ONNX/OpenVINO/CUDA może zastąpić lub uzupełnić klasyczny CV
**tylko jeśli** pobije baseline na **wszystkich** poniższych metrykach:

| Metryka | Baseline (ORB/FLANN) | YOLO musi być |
|---------|---------------------|---------------|
| Accuracy | TBD (z benchmarku) | Wyższa |
| False positive rate | TBD | Niższa |
| Frame time (HP EliteBook) | TBD | Nie gorsza |
| Frame time (Ryzen 7 + RTX 3070) | TBD | Lepsza |
| Stabilność pod okluzją ręki | TBD | Nie gorsza |
| Nakład utrzymania kodu | Niski | Porównywalny |

## Architektura ewaluacji

```
Nagranie MP4
    └── benchmark_video.py (klasyczny CV) → CSV baseline
    └── benchmark_yolo.py (przyszły)      → CSV YOLO
         └── Porównanie → Decyzja
```

## Rozważane warianty

1. **YOLOv8-nano** — ultra-lekki, CPU-friendly
2. **YOLOv8-medium + EfficientNet-B0** — dwuetapowy (detekcja + klasyfikacja)
3. **ONNX Runtime** — optymalizacja CPU inference
4. **OpenVINO** — Intel-specific optymalizacja (HP EliteBook)
5. **CUDA/TensorRT** — GPU inference (RTX 3070)

## Dataset

Szczegóły planowanego datasetu do treningu YOLO — patrz
[dataset_notes.md](dataset_notes.md).
