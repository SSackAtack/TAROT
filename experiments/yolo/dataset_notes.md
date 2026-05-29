# Dataset Notes — YOLO Training

## Źródła danych

### Obecne zasoby
- **22 Wielkie Arkana RWS** — skany 300 DPI w `biblioteka_talii/`
- **Referencje CV** — przycięte wzorce `.jpg` w `wzorce_cv/`

### Potrzebne do treningu YOLO
- **Nagrania wideo** z kamery C310 pod różnymi warunkami
- **Augmentowane zdjęcia** (obroty, skala, oświetlenie, perspektywa)
- **Negatywne próbki** — puste tło, ręce, inne obiekty

## Szacowana wielkość datasetu

Na podstawie rekomendacji z raportów analitycznych:

| Źródło | Rekomendacja |
|--------|-------------|
| DeepSeek | ~100 zdjęć/kartę (augmentowane) |
| Kimi | 15k-23k obrazów łącznie |
| GLM | Transfer learning z pretrained YOLO |

### Realistyczny plan minimum
- 22 klasy (Wielkie Arkana) × 100 zdjęć = 2200 zdjęć
- Augmentacja 5x = ~11 000 próbek treningowych
- Walidacja: 20% holdout

## Format annotacji

YOLO format (`.txt` per image):
```
<class_id> <x_center> <y_center> <width> <height>
```

Wartości znormalizowane do [0, 1] względem rozmiaru obrazu.

## Narzędzia annotacji

Rozważane:
- **CVAT** (Computer Vision Annotation Tool) — open source
- **Label Studio** — open source, UI webowy
- **Roboflow** — semi-auto annotation z exportem YOLO

## Uwagi

- Autorska talia (konsensus 6/6 raportów AI) wymaga osobnego
  datasetu — ale format annotacji pozostaje ten sam.
- Transfer learning z COCO-pretrained YOLO jest preferowany
  nad treningiem od zera.
