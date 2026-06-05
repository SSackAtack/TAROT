# TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001

## Cel

Przygotować Research Gate dla Stage 2 Region Segmentation / Region Refinement nowego offline labu state-first.

Stage 1 jest zatwierdzony jako:

```text
APPROVED_STAGE_1_METHOD: gray_absdiff_gaussian
```

Stage 2 ma zaproponować metody, które przekształcą regiony zmiany ze Stage 1 w stabilne kandydaty regionów kart albo w precyzyjniejsze maski/bboxy do kolejnego benchmarku. Ten task nie implementuje benchmarku Stage 2.

## Zakres

Dozwolone:

- analiza metod OpenCV/NumPy bez nowych zależności,
- zapis raportu badawczego,
- wskazanie shortlisty `TEST_NOW`,
- aktualizacja indeksu zadań i planu wykonawczego.

Zakazane:

- zmiany `tools/cv_detection_lab/*`,
- zmiany `app_cv/*`,
- zmiany `app_ar/*`,
- zmiany runtime, ArUco, ORB, WebSocket lub Studio UI,
- uruchamianie albo implementacja Stage 2 benchmarku.

## Pliki Dozwolone do Zmiany

- `.ai/tasks/TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001/TASK.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001/STATE.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001/CHANGELOG.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001/TEST_REPORT.md`
- `.ai/tasks/TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001/RESEARCH_REPORT.md`
- `.ai/TASKS_INDEX.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-1-plan.md`
- `docs/superpowers/plans/2026-06-03-state-first-offline-lab-stage-2-plan.md`

## Kryteria Akceptacji

- Raport zawiera wszystkie wymagane sekcje research.
- Raport odpowiada na pytania o stabilny region obiektu, odróżnianie karty od refleksu/tła, oversized bbox, split card i przygotowanie do modelu state-first.
- Raport zawiera matrycę kandydatów z metodami wymaganymi w handoffie.
- Raport kończy się shortlistą `TEST_NOW`.
- Stage 2 benchmark jest zablokowany do czasu akceptacji shortlisty przez Supervisora.

## Testy Wymagane

```text
Automated tests: NOT_RUN — documentation-only research gate.
Manual verification: git diff reviewed manually.
```
