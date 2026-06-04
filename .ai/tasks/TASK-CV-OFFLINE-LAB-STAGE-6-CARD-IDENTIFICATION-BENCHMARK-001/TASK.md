# TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001

## Cel

Zaimplementować i uruchomić izolowany benchmark Stage 6 Card Identification na zatwierdzonym pipeline Stage 1-5, referencjach Gilded i ręcznie potwierdzonym ground truth.

## Zakres

Pierwsza fala metod:

- `orb_bfmatcher_ratio_test`
- `akaze_bfmatcher`
- `histogram_similarity_hsv`
- `ssim_like_luma`
- `hybrid_orb_plus_histogram`

Benchmark mierzy:

- accuracy top1 i top3,
- confidence gap,
- ambiguous match rate,
- runtime,
- kontekst jakości cropa ze Stage 5.

## Poza Zakresem

- Brak zmian runtime.
- Brak integracji Studio / WebSocket.
- Brak OCR / ML / nowych zależności.
- Brak FLANN / BRISK / ensemble w pierwszej fali.

## Wynik

`orb_bfmatcher_ratio_test` jest `PROVISIONAL_RECOMMENDED` po osiągnięciu 100% top1/top3 przy niższym runtime niż AKAZE.
