# CHANGELOG

## 2026-06-04

- Rozpoczęto offline-only benchmark identyfikacji Stage 6 na real-camera fixture.
- Dodano runner ORB/AKAZE i testy kontraktu.
- Przetworzono wszystkie 28 zatwierdzonych próbek bez modyfikacji sesji capture.
- ORB osiągnął Top-1 `0.80`, Top-3 `0.85`, wrong-deck FAR `0.00`.
- AKAZE osiągnął Top-1/Top-3 `0.70`, wrong-deck FAR `0.75`.
- Zachowano granicę offline-only; brak zmian runtime.
