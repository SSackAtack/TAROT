# Stan Prac — TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001

## 1. Status Ogólny

* **Status:** `DONE`
* **Realizator (Owner):** Codex
* **Gałąź Git:** `task/cv-event-first-plan-001-clarify-autotune-runtime`
* **Data:** 2026-06-03

---

## 2. Stan Aktualny

Stage 1 Difference Detection został zatwierdzony:

```text
APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
```

Znane ograniczenie: regiony Stage 1 są regionami zmiany, nie finalnymi obrysami kart. Nie wolno używać ich bezpośrednio jako cropów kart.

---

## 3. Co Zostało Zrobione

- [x] Przeczytano dokumenty Stage 1, raport research i aktualny benchmark.
- [x] Przeanalizowano techniki segmentacji/refinementu regionów zgodne z OpenCV/NumPy.
- [x] Przygotowano matrycę kandydatów Stage 2.
- [x] Wskazano shortlistę `TEST_NOW`.
- [x] Oznaczono Stage 2 benchmark jako zablokowany do czasu akceptacji shortlisty przez Supervisora.

---

## 4. Co Pozostało do Zrobienia

- [ ] Supervisor akceptuje albo koryguje shortlistę `TEST_NOW`.
- [ ] Po akceptacji utworzyć osobny task implementacyjny `TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001`.
- [ ] Dopiero w następnym tasku dodać benchmark Stage 2 do `tools/cv_detection_lab/`.

## Session Status (2026-06-03 Codex)

Stan aktualny: Research Gate Stage 2 jest kompletny dokumentacyjnie.

Co zostało zrobione: zapisano rekomendacje dla metod region segmentation/refinement, z naciskiem na obsługę oversized bboxów, split cards i scenariusz state-first `one_card -> three_cards`.

Kolejne kroki: Supervisor powinien zaakceptować shortlistę `TEST_NOW`. Stage 2 benchmark must not begin until Supervisor accepts TEST_NOW shortlist.
