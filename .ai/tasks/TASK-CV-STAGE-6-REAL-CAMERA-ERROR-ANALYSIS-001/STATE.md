# STATE

## Status

`DONE`

## Result

- Błędy Top-1 ORB: `4`.
- Błędy poza Top-3: `3`.
- `image_quality_or_crop`: `3`.
- `ground_truth_mismatch_suspected`: `1`.

Podejrzana etykieta:

```text
sample_id: f8d6d84b5ddb5729fa07
ground truth: Gilded_45
strong ORB prediction: Gilded_67
```

Wizualny review planszy wskazuje, że crop przedstawia `Gilded_67`, dlatego
ground truth wymaga ponownego ręcznego potwierdzenia.

## Decision Boundary

Analiza jest offline-only. Nie zmieniono ground truth, runtime ani thresholdów.

## Required Next Action

Supervisor/operator ręcznie potwierdza etykietę `f8d6d84b5ddb5729fa07`. Po
ewentualnej korekcie należy ponownie uruchomić benchmark i analizę.
