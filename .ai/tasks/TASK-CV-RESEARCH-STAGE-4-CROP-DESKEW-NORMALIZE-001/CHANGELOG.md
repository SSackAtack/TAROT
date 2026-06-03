# CHANGELOG

## 2026-06-03 Codex

- Utworzono Research Gate Stage 4 Crop / Deskew / Normalize.
- Udokumentowano zatwierdzony pipeline wejściowy Stage 1+2+3.
- Przygotowano Candidate Techniques Matrix dla crop, deskew i normalizacji.
- Wskazano shortlistę metod `TEST_NOW` do przyszłego benchmarku.
- Zaznaczono ograniczenia Stage 4: brak walidacji jakości cropa jako osobnego etapu, brak identyfikacji kart i brak integracji runtime.
- Zaktualizowano `.ai/TASKS_INDEX.md`.
- Zaktualizowano plan Stage 3 i dodano plan Stage 4.

## Decyzje

- Preferowany kierunek benchmarku to OpenCV/NumPy CPU-only bez nowych zależności.
- `ordered_quad_points` jest preferowanym wejściem do perspective transform, ale `rotated_bbox` i `bbox` pozostają potrzebne jako fallbacki.
- Safe padding powinien być testowany jako jawny parametr, bo za mały padding ucina kartę, a za duży wprowadza matę.
- Normalizacja obrazu ma być testowana ostrożnie; nie może usuwać cech potrzebnych do późniejszej identyfikacji.
