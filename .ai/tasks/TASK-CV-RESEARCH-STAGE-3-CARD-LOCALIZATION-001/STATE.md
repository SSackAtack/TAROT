# Stan Prac — TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001

## 1. Status Ogólny

* **Status:** `DONE`
* **Realizator (Owner):** Codex
* **Gałąź Git:** `task/cv-event-first-plan-001-clarify-autotune-runtime`
* **Data:** 2026-06-03

---

## 2. Stan Aktualny

Zatwierdzony pipeline wejściowy:

```text
Stage 1: APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
Stage 2: APPROVED_STAGE_2_METHOD: contour_external
```

Stage 2 bbox oznacza region kandydata obiektu/karty. Nie jest finalnym obrysem karty ani gotowym cropem.

---

## 3. Co Zostało Zrobione

- [x] Przeczytano dokumenty i plany Stage 1/Stage 2.
- [x] Przeanalizowano techniki OpenCV/NumPy dla lokalizacji geometrii karty.
- [x] Przygotowano Candidate Techniques Matrix.
- [x] Wskazano shortlistę `TEST_NOW`.
- [x] Zdefiniowano proponowany benchmark Stage 3.
- [x] Zablokowano benchmark Stage 3 do czasu akceptacji shortlisty przez Supervisora.

---

## 4. Co Pozostało do Zrobienia

- [ ] Supervisor akceptuje albo koryguje shortlistę `TEST_NOW`.
- [ ] Po akceptacji utworzyć osobny task `TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001`.
- [ ] Dopiero w następnym tasku implementować benchmark Stage 3.

## Session Status (2026-06-03 Codex)

Stan aktualny: Research Gate Stage 3 jest kompletny dokumentacyjnie.

Co zostało zrobione: zapisano metody kandydackie dla Card Localization / Geometry Extraction, w tym kontury wewnątrz regionu Stage 2, `approxPolyDP`, `minAreaRect`, edge-supported bbox, Hough/LSD lines, corner evidence i scoring borderów.

Kolejne kroki: Stage 3 benchmark must not begin until Supervisor accepts TEST_NOW shortlist.
