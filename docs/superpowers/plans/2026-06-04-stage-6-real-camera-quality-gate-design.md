# Stage 6 Real-Camera Quality Gate Design

## Status ogólny

Projekt offline-only. Nie zatwierdza runtime threshold ani integracji runtime.

## Stan aktualny

Po korekcie ground truth ORB osiąga:

```text
Top-1: 0.85
Top-3: 0.90
wrong-deck FAR: 0.00
```

Pozostały trzy błędy Top-1:

```text
47ba5f4ff2946f7d0c1d
377ce08663f0c7430c6b
c332dd59cef00d668e54
```

Manual review pokazuje silne odblaski zasłaniające grafikę. Istniejący Stage 5
quality suite klasyfikuje je jako `YELLOW`, ale daje readiness `0.678-0.777`,
`overexposed_pixel_ratio = 0.0` i `top_reflection_score = 0.0`.

## Problem

Obecne metryki bazują głównie na globalnym kontraście, ostrości, detalach,
borderach i pikselach powyżej `245`. Duży odblask może mieć jasność poniżej
progu clippingu, zachowując wysoki globalny kontrast i wiele krawędzi.

Quality gate musi wykrywać lokalną jasną, nisko-teksturalną plamę zasłaniającą
znaczącą część karty, nie tylko piksele bliskie czystej bieli.

## Proponowany kontrakt offline

```text
evaluate_stage6_quality_gate(crop, optional_match_diagnostics) ->
  decision: ACCEPT_FOR_IDENTIFICATION | RETRY_CAPTURE | MANUAL_REVIEW
  reasons[]
  metrics{}
```

Gate nie rozpoznaje karty i nie zmienia wyniku matchera.

## Sygnały TEST_NOW

1. `local_specular_component_ratio`
   - Progowanie adaptacyjne względem lokalnych percentyli jasności.
   - Jasny komponent musi mieć niski lokalny gradient/teksturę.
   - Raportuje największy komponent względem powierzchni cropu.

2. `highlight_occlusion_ratio`
   - Udział jasnych, nisko-teksturalnych komponentów w centralnym obszarze karty.
   - Ważniejszy niż highlight przy samym borderze.

3. `usable_detail_ratio`
   - Edge/texture density liczona poza wykrytymi highlightami.
   - Sprawdza, czy po odjęciu odblasku pozostaje wystarczająco dużo grafiki.

4. Istniejące sanity checks
   - `edge_cut_risk`, `border_continuity_score`, `card_fill_ratio`,
     `aspect_ratio_error_score`, `contrast_score`, sharpness i detail.

5. Opcjonalny sygnał diagnostyczny Stage 6
   - `confidence_score` i `confidence_gap` mogą podnieść decyzję z
     `ACCEPT_FOR_IDENTIFICATION` do `MANUAL_REVIEW` albo `RETRY_CAPTURE`.
   - Nie mogą samodzielnie ustalać jakości cropu ani finalnego threshold runtime.

## Logika decyzji do benchmarku

```text
RETRY_CAPTURE:
- duży centralny specular component, albo
- niski usable detail po usunięciu highlightu, albo
- twardy geometry sanity failure.

MANUAL_REVIEW:
- jakość niejednoznaczna, albo
- niska pewność/gap ORB przy braku twardego problemu jakości.

ACCEPT_FOR_IDENTIFICATION:
- brak twardych problemów jakości i wystarczający usable detail.
```

Wszystkie progi pozostają `BENCHMARK_HEURISTIC_ONLY`.

## Benchmark plan

Wejście:

```text
28 zatwierdzonych real-camera extracted crops
ground truth po korekcie Gilded_67
wyniki ORB
```

Wymagane metryki:

```text
bad_crop_retry_recall
good_crop_false_retry_rate
wrong_deck_false_retry_rate
ORB accuracy on ACCEPT subset
retry_count per category
manual_review_count
```

Kryterium jakości projektu:

- wszystkie trzy znane błędy `image_quality_or_crop` powinny otrzymać
  `RETRY_CAPTURE` albo `MANUAL_REVIEW`,
- poprawne upright/reversed/visually-similar nie mogą być masowo odrzucane,
- wynik musi raportować kompromis recall vs false retry,
- brak deklaracji finalnych progów runtime.

## Artefakty przyszłego benchmarku

```text
matrix.csv
report.json
report.md
quality_gate_review_pack/
  sample sheets z maską highlightu
  ACCEPT / RETRY / MANUAL_REVIEW indexes
```

## Ryzyka

- jasne elementy grafiki mogą wyglądać jak odblask,
- ciemne talie mogą mieć mały usable detail mimo dobrego cropu,
- fixture 28 próbek jest za mały do finalnych progów,
- powiązanie z ORB może nadmiernie dostroić gate do jednej metody.

## Co zostało zrobione

- [x] Potwierdzono trzy pozostałe błędy jakości/cropu.
- [x] Porównano je z istniejącymi metrykami Stage 5.
- [x] Zidentyfikowano lukę lokalnego specular highlight.
- [x] Zaprojektowano kontrakt i benchmark offline-only.

## Kolejne kroki

Po akceptacji Supervisora utworzyć mały offline benchmark implementujący
`local_specular_component_ratio`, `highlight_occlusion_ratio` i
`usable_detail_ratio`. Nie zmieniać runtime.

## Session Status (2026-06-04 Codex Quality Gate Benchmark)

Stan aktualny: projekt został zatwierdzony przez Supervisora i zaimplementowany
jako benchmark offline-only.

Co zostało zrobione: gate generuje adaptacyjną maskę lokalnych neutralnych
highlightów, mierzy największy komponent, centralne zasłonięcie i usable detail.
Opcjonalny niski sygnał ORB może eskalować ACCEPT do MANUAL_REVIEW, ale nie
zmienia wyniku identyfikacji.

Wynik: bad crop recall `1.0`, good crop false retry `0.0`, wrong-deck false
retry `0.0`, ORB accuracy na ACCEPT subset `1.0`.

Kolejne kroki: manual review masek i decyzja Supervisora. Progi pozostają
`BENCHMARK_HEURISTIC_ONLY`; brak zgody na runtime integration.
