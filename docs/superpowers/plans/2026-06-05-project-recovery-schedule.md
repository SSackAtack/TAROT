# TarotVision Project Recovery Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** przywrócić projekt TarotVision na właściwe tory przez 30-dniowy harmonogram, który najpierw domyka recording-ready MVP, a dopiero potem porządkuje dług techniczny i rozszerzenia.

**Architecture:** zachować snapshot-first jako produkcyjną ścieżkę CV i ograniczyć autotune do roli preflight/readiness check. Praca ma iść małymi taskami Green/Yellow Lane, z decyzją Michała tylko dla Red Lane i merge do `master`.

**Tech Stack:** Python/OpenCV backend `app_cv`, Vite/JavaScript Studio `app_ar`, WebSocket runtime, dokumentacja `.ai/`, `docs/superpowers/plans/`, `analizy/`.

---

## Stan docelowy

Na końcu harmonogramu projekt ma mieć:

- jeden recording-ready MVP workflow na talii Gilded,
- runbook operatora od startu aplikacji do nagrania,
- fizyczny smoke `empty`, `one_card`, `three_cards` sklasyfikowany jako GO/WARN/STOP,
- pierwsze krótkie nagranie demo albo jasny raport, który jeden blocker uniemożliwia nagranie,
- ograniczony i zrozumiały backlog,
- mniej formalny, ale nadal bezpieczny proces pracy agentów,
- brak nowych tasków autotune bez bezpośredniego wpływu na MVP.

## Funkcja kosztu

Minimalizujemy:

- czas tracony na autotuning bez produktu,
- liczbę otwartych gałęzi i nieaktualnych statusów,
- niepewność operatora podczas fizycznych testów,
- ryzyko ukrycia blockerów pod kolejnymi progami CV,
- koszt poznawczy dla kolejnego agenta.

Nie minimalizujemy teraz:

- liczby warningów kamery, jeśli preview i sample działają,
- liczby testów offline,
- liczby wspieranych talii,
- jakości architektury idealnej przed pierwszym MVP.

## Założenia

- Data startu harmonogramu: 2026-06-05.
- Główna talia MVP: Gilded.
- `app_ar/public/active_decks.json` pozostaje lokalną konfiguracją operatora i nie jest commitowany bez wyraźnej zgody.
- Autotune/Calibration Wizard nie są głównym produktem.
- Każdy agent może samodzielnie wykonywać Green Lane taski na branchu roboczym.
- Merge do `master` wymaga decyzji Michała.

## Fazy i terminy

| Faza | Termin | Cel | Decyzja końcowa |
|---|---:|---|---|
| 0. Lock recovery | 2026-06-05 do 2026-06-07 | zamrozić chaos i ustawić jeden kierunek | READY_FOR_MVP_SMOKE |
| 1. Operator runway | 2026-06-08 do 2026-06-10 | runbook, launcher, checklisty, aktywna talia | READY_FOR_PHYSICAL_TEST |
| 2. MVP physical smoke | 2026-06-11 do 2026-06-14 | `empty`, `one_card`, `three_cards`, preview | GO_TO_RECORDING / FIX_ONE_BLOCKER |
| 3. Recording demo | 2026-06-15 do 2026-06-18 | pierwsza krótka sesja nagraniowa | MVP_DEMO_PASS / MVP_DEMO_BLOCKED |
| 4. Stabilizacja po demo | 2026-06-19 do 2026-06-25 | naprawić tylko blockery z demo | READY_FOR_MASTER_PR |
| 5. Porządkowanie długu | 2026-06-26 do 2026-07-05 | dokumentacja, backlog, małe refaktory | RECOVERY_COMPLETE |

---

## Task 0: Recovery Governance Lock

**Termin:** 2026-06-05 do 2026-06-07
**Lane:** Green
**Cel:** zakończyć rozproszenie i wymusić jeden kierunek pracy.

**Files:**

- Modify: `.ai/PROJECT_STATE.md`
- Modify: `.ai/TASKS_INDEX.md`
- Modify: `docs/superpowers/plans/2026-06-05-mvp-recovery-plan.md`
- Read: `analizy/audyt_mvp_recovery_2026-06-05.md`
- Read: `analizy/audyt_zasad_wspolpracy_agentow_2026-06-05.md`

- [ ] **Step 1: Oznacz MVP Recovery Mode w stanie projektu**

W `.ai/PROJECT_STATE.md` dodaj lub zaktualizuj sekcję:

```markdown
## MVP Recovery Mode (2026-06-05)

Priorytet: recording-ready MVP na jednej talii Gilded.
Autotune/Calibration Wizard jest preflightem i diagnostyką, nie głównym produktem.

Freeze do czasu MVP:
- nowe profile autotune,
- dalsze luzowanie geometrii bez świeżego smoke `empty`,
- multi-deck hardening,
- duże refaktory runtime/UI,
- offline lab bez bezpośredniej decyzji dla MVP.
```

- [ ] **Step 2: Oznacz nieaktywne albo historyczne taski**

W `.ai/TASKS_INDEX.md` nie kasuj tasków. Dopisz w statusie review aktualnych tasków CV, które nie są potrzebne do MVP:

```markdown
Historyczne / nieaktywne w MVP Recovery Mode
```

Dotyczy tylko tasków, które nie są bieżącym blockerem `three_cards`, runbooka, preview albo recording demo.

- [ ] **Step 3: Ustal limit WIP**

W planie recovery dodaj sekcję:

```markdown
## WIP Limit

- maksymalnie 2 aktywne taski kodowe naraz,
- maksymalnie 1 task CV/tuning naraz,
- maksymalnie 1 branch oczekujący na decyzję Michała,
- każdy nowy task musi wskazać wpływ na MVP.
```

- [ ] **Step 4: Verification**

Run:

```powershell
git status
git diff -- .ai/PROJECT_STATE.md .ai/TASKS_INDEX.md docs/superpowers/plans/2026-06-05-mvp-recovery-plan.md
git diff -- app_ar/public/active_decks.json
```

Expected:

- zmieniona tylko dokumentacja procesu,
- `active_decks.json` nie jest staged,
- brak zmian kodu runtime.

- [ ] **Step 5: Commit**

```powershell
git add .ai/PROJECT_STATE.md .ai/TASKS_INDEX.md docs/superpowers/plans/2026-06-05-mvp-recovery-plan.md
git restore --staged app_ar/public/active_decks.json
git commit -m "docs: ustaw tryb MVP recovery"
git push
```

## Task 1: Operator MVP Runbook

**Termin:** 2026-06-08 do 2026-06-10
**Lane:** Green
**Cel:** operator ma jedną instrukcję uruchomienia i smoke testu.

**Files:**

- Create: `docs/operator/mvp_recording_runbook.md`
- Create: `docs/operator/mvp_physical_smoke_checklist.md`
- Modify: `README.md` only if launch instructions are stale

- [ ] **Step 1: Utwórz folder operatora**

Run:

```powershell
New-Item -ItemType Directory -Force docs/operator
```

Expected:

```text
docs/operator
```

- [ ] **Step 2: Utwórz runbook**

Create `docs/operator/mvp_recording_runbook.md`:

```markdown
# TarotVision MVP Recording Runbook

## Setup

- physical deck: Gilded
- active deck runtime: gilded
- camera resolution target: 1280x720
- WebSocket port: 8765
- Studio URL: http://localhost:5173/?studio=1

## Start

1. Zamknij stare okna backendu, Studio i terminale Node.
2. Uruchom launcher Studio.
3. Sprawdź, czy backend pokazuje aktywną talię `gilded`.
4. Sprawdź, czy preview kamery nie jest czarne.
5. Jeśli port 8765 jest zajęty, zamknij proces zgodnie z komunikatem launchera.

## Preflight

### EMPTY

Expected:
- samples: 3/3
- false positives: NIE
- HUD false warnings: NIE

### ONE_CARD

Expected:
- samples: 3/3
- accepted_total: 3
- detected_count: 1 dla każdej próbki albo czytelny powód odrzucenia

### THREE_CARDS

Expected:
- PASS albo FAIL z klasyfikacją: geometry / recognition / operator setup / camera

## Decision

GO:
- preview działa,
- active deck zgadza się z physical deck,
- EMPTY PASS,
- ONE_CARD PASS,
- THREE_CARDS PASS albo manual fallback jest dostępny.

WARN:
- kamera loguje warningi, ale preview i sample działają,
- confidence jest niskie, ale wynik jest stabilny.

STOP:
- preview czarne,
- active deck nie zgadza się z physical deck,
- EMPTY wykrywa fałszywe karty,
- nie można zebrać próbek.
```

- [ ] **Step 3: Utwórz checklistę smoke**

Create `docs/operator/mvp_physical_smoke_checklist.md`:

```markdown
# MVP Physical Smoke Checklist

Date:
Branch:
HEAD:
Physical deck:
Active deck:
Camera:

## EMPTY

- 3/3: PASS / FAIL
- false positives: TAK / NIE
- HUD warnings: TAK / NIE
- notes:

## ONE_CARD

- 3/3: PASS / FAIL
- accepted_total:
- detected_count per sample:
- top matches:
- notes:

## THREE_CARDS

- result: PASS / FAIL / NOT_RUN
- detected_count per sample:
- accepted_total:
- failure class: geometry / recognition / operator setup / camera / none
- notes:

## Preview

- Studio preview visible: TAK / NIE
- black preview: TAK / NIE
- camera warnings block test: TAK / NIE

## Decision

- GO / WARN / STOP:
- next action:
```

- [ ] **Step 4: Verification**

Run:

```powershell
git diff -- docs/operator
git diff -- app_ar/public/active_decks.json
```

Expected:

- runbook i checklist są samowystarczalne,
- `active_decks.json` nie jest staged.

- [ ] **Step 5: Commit**

```powershell
git add docs/operator/mvp_recording_runbook.md docs/operator/mvp_physical_smoke_checklist.md
git restore --staged app_ar/public/active_decks.json
git commit -m "docs: dodaj runbook operatora MVP"
git push
```

## Task 2: MVP Physical Smoke

**Termin:** 2026-06-11 do 2026-06-14
**Lane:** Yellow, bo obejmuje fizyczny runtime
**Cel:** zastąpić dalszy autotuning jednym testem produktowym.

**Files:**

- Create: `.ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001/TEST_REPORT.md`
- Create: `.ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001/STATE.md`
- Create: `.ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001/CHANGELOG.md`
- Modify: `.ai/TASKS_INDEX.md`
- Read: `docs/operator/mvp_physical_smoke_checklist.md`

- [ ] **Step 1: Przygotuj task smoke**

Run:

```powershell
New-Item -ItemType Directory -Force .ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001
```

- [ ] **Step 2: Wykonaj EMPTY**

Operator wykonuje scenariusz `EMPTY` w Studio.

Expected:

```text
samples: 3/3
false positives: NIE
stage_result: PASS
```

STOP if:

```text
false positives: TAK
```

- [ ] **Step 3: Wykonaj ONE_CARD**

Operator wykonuje scenariusz `ONE_CARD` na Gilded.

Expected:

```text
samples: 3/3
accepted_total: 3
stage_result: PASS
```

WARN if:

```text
camera warnings present but samples pass
```

- [ ] **Step 4: Wykonaj THREE_CARDS**

Operator wykonuje scenariusz `THREE_CARDS`.

Expected:

```text
stage_result: PASS
```

If FAIL, classify:

```text
failure_class: geometry / recognition / operator setup / camera
```

- [ ] **Step 5: Zapisz raport**

Create `.ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001/TEST_REPORT.md`:

```markdown
# TEST_REPORT — TASK-MVP-PHYSICAL-SMOKE-GILDED-001

## PHYSICAL_SMOKE_MVP_GILDED

Branch:
HEAD:
Physical deck: Gilded
Active deck:
Camera:

## EMPTY

- 3/3:
- false positives:
- HUD warnings:
- decision:
- notes:

## ONE_CARD

- 3/3:
- accepted_total:
- detected_count per sample:
- decision:
- notes:

## THREE_CARDS

- result:
- accepted_total:
- failure_class:
- decision:
- notes:

## Preview

- visible:
- black preview:
- camera warnings:

## Final Decision

GO_TO_RECORDING / FIX_ONE_BLOCKER / STOP_FALSE_POSITIVES / STOP_CAMERA
```

- [ ] **Step 6: Decision**

Use:

```text
GO_TO_RECORDING
```

only if:

- `EMPTY` PASS,
- `ONE_CARD` PASS,
- `THREE_CARDS` PASS or manual fallback is explicitly available,
- preview visible.

- [ ] **Step 7: Commit**

```powershell
git add .ai/tasks/TASK-MVP-PHYSICAL-SMOKE-GILDED-001 .ai/TASKS_INDEX.md
git restore --staged app_ar/public/active_decks.json
git commit -m "docs: zapisz smoke test MVP Gilded"
git push
```

## Task 3: One-Blocker Fix Window

**Termin:** 2026-06-14 do 2026-06-16
**Lane:** Yellow or Red depending on blocker
**Cel:** jeśli smoke failuje, naprawić tylko jeden blocker, nie zaczynać nowego cyklu autotuningu.

**Files:**

- Modify only files directly tied to the classified blocker.
- Test files must be added or updated for code changes.

- [ ] **Step 1: Classify blocker**

Allowed classes:

```text
false_positive_empty
camera_no_preview
three_cards_geometry
three_cards_recognition
operator_runbook_gap
manual_fallback_missing
```

- [ ] **Step 2: Stop non-blocker work**

Do not start:

```text
new_autotune_profile
multi_deck_hardening
offline_lab_extension
main_py_refactor
studio_redesign
```

- [ ] **Step 3: Pick one fix**

Examples:

```text
false_positive_empty -> tighten empty rejection only, then rerun EMPTY
camera_no_preview -> launcher/camera recovery only, then rerun preview check
three_cards_geometry -> targeted detector fix, then rerun EMPTY + THREE_CARDS
three_cards_recognition -> recognition diagnostic, then rerun ONE_CARD + THREE_CARDS
manual_fallback_missing -> minimal operator override, then run recording rehearsal
```

- [ ] **Step 4: Verification**

For code changes run:

```powershell
python -m unittest discover tests
```

If frontend changed run:

```powershell
cd app_ar
npm run build
```

Always rerun the physical scenario that failed.

- [ ] **Step 5: Commit**

Use one narrow commit:

```powershell
git add <changed-files>
git restore --staged app_ar/public/active_decks.json
git commit -m "fix: usuń blocker MVP smoke <class>"
git push
```

## Task 4: Recording Demo

**Termin:** 2026-06-15 do 2026-06-18
**Lane:** Yellow
**Cel:** nagrać krótki materiał demonstracyjny albo jednoznacznie wskazać ostatni blocker.

**Files:**

- Create: `.ai/tasks/TASK-MVP-RECORDING-DEMO-001/TEST_REPORT.md`
- Create: `.ai/tasks/TASK-MVP-RECORDING-DEMO-001/STATE.md`
- Modify: `.ai/TASKS_INDEX.md`
- Optional Create: `docs/operator/mvp_recording_demo_notes.md`

- [ ] **Step 1: Przygotuj scenariusz demo**

Use:

```text
Deck: Gilded
Spread: 3 cards
Duration target: 3-5 minutes
Mode: operator-assisted
```

- [ ] **Step 2: Uruchom preflight**

Required:

```text
EMPTY: PASS
ONE_CARD: PASS
THREE_CARDS: PASS or manual fallback available
Preview: visible
```

- [ ] **Step 3: Nagraj demo**

Record:

```text
intro -> spread placement -> recognition/AR result -> short operator correction if needed -> outro
```

- [ ] **Step 4: Zapisz raport**

Create `.ai/tasks/TASK-MVP-RECORDING-DEMO-001/TEST_REPORT.md`:

```markdown
# TEST_REPORT — TASK-MVP-RECORDING-DEMO-001

## MVP_RECORDING_DEMO

Date:
Branch:
HEAD:
Deck:
Duration:

## Preflight

- EMPTY:
- ONE_CARD:
- THREE_CARDS:
- Preview:

## Recording

- completed:
- AR result visible:
- operator interventions:
- camera warnings:
- recording saved:

## Decision

MVP_DEMO_PASS / MVP_DEMO_BLOCKED

## Blocking Issues

- issue:
- class:
- required next task:
```

- [ ] **Step 5: Decision**

If demo passes:

```text
MVP_DEMO_PASS
```

Then move to Task 5.

If demo is blocked:

```text
MVP_DEMO_BLOCKED
```

Then open exactly one blocker task, not a new tuning program.

## Task 5: Stabilization After Demo

**Termin:** 2026-06-19 do 2026-06-25
**Lane:** Yellow
**Cel:** poprawić tylko problemy ujawnione w demo i przygotować PR/merge strategy.

**Files:**

- Modify: `.ai/PROJECT_STATE.md`
- Modify: `.ai/TASKS_INDEX.md`
- Modify: `README.md`
- Modify code only for demo blockers.

- [ ] **Step 1: Split demo findings**

Create a short list:

```markdown
## Demo Findings

### Blockers
- ...

### Annoyances
- ...

### Backlog
- ...
```

- [ ] **Step 2: Fix only blockers**

Rule:

```text
Blocker = prevents recording-ready MVP.
Annoyance = visible but does not block demo.
Backlog = improvement after MVP.
```

- [ ] **Step 3: Update README**

README must answer:

```text
How to run MVP demo?
Which deck?
What is expected to work?
What is known limitation?
```

- [ ] **Step 4: Verification**

Run based on changed files:

```powershell
python -m unittest discover tests
```

If frontend changed:

```powershell
cd app_ar
npm run build
```

If runtime changed:

```text
rerun impacted physical smoke scenario
```

- [ ] **Step 5: Prepare merge decision**

Create:

```markdown
READY_FOR_MASTER_PR

Branch:
Head:
MVP demo:
Tests:
Physical smoke:
Known limitations:
Decision requested:
```

## Task 6: Debt Reduction Sprint

**Termin:** 2026-06-26 do 2026-07-05
**Lane:** Green/Yellow per task
**Cel:** po MVP zmniejszyć koszt utrzymania bez rozbijania działającego workflow.

**Files likely involved:**

- `app_cv/main.py`
- `app_cv/tarotvision/pipelines/snapshot_first.py`
- `app_cv/tarotvision/calibration_wizard_scoring.py`
- `app_ar/src/studio/studioConsole.js`
- `.ai/PROJECT_STATE.md`
- `README.md`

- [ ] **Step 1: Create debt inventory**

Create `analizy/debt_inventory_after_mvp_2026-06.md`:

```markdown
# Debt Inventory After MVP

## Runtime
- `app_cv/main.py`: orchestration overload
- `snapshot_first.py`: mixed runtime/diagnostics responsibilities

## Studio
- `studioConsole.js`: oversized module

## Docs
- stale README sections
- stale test counts

## Do Not Fix Yet
- multi-deck robustness
- advanced autotune
- ML migration
```

- [ ] **Step 2: Pick max 3 debt tasks**

Allowed:

```text
extract runtime command handlers
extract calibration wizard service
split studio panel module
sync README/project state
```

Not allowed:

```text
rewrite runtime
replace CV approach
add new model family
expand decks
```

- [ ] **Step 3: Run each debt task as independent branch**

For each task:

```powershell
git switch -c codex/<short-debt-task>
```

Each debt task must have:

```text
one goal
one owner
one test command
one commit range
```

- [ ] **Step 4: Verify no behavior drift**

After each debt task:

```powershell
python -m unittest discover tests
```

If frontend changed:

```powershell
cd app_ar
npm run build
```

If runtime orchestration changed:

```text
run at least ONE_CARD physical smoke or documented operator check
```

## Cadence

### Daily rhythm

- Start: `git status`, current branch, active task.
- Work: one task, one narrow scope.
- Verify: targeted tests first, full relevant suite before commit.
- End: commit + push or explicit note why not.

### Weekly rhythm

- Monday: choose max 3 active tasks.
- Wednesday: kill or narrow stuck tasks.
- Friday: update project state and decide GO/WARN/STOP.

### WIP limits

- max 2 active coding branches,
- max 1 active CV/tuning branch,
- max 1 pending merge decision,
- max 1 physical smoke blocker at a time.

## Stop Rules

Stop and ask Michał for Red Lane decision if:

- proposed work changes architecture,
- proposed work changes stack,
- task requires deleting tests,
- task requires deleting large code areas,
- merge to `master` is requested,
- physical MVP criteria need to be redefined.

Stop current task and narrow scope if:

- it touches more than 3 production modules without prior plan,
- it starts adding autotune features,
- it expands deck support before MVP,
- it cannot define one user-visible outcome.

## Metrics

Track weekly:

- number of active branches,
- number of tasks waiting for review,
- latest physical smoke decision,
- latest demo decision,
- test command and result,
- whether `active_decks.json` was excluded from commits.

Healthy target by 2026-07-05:

```text
active coding branches <= 2
MVP demo decision recorded
README current
PROJECT_STATE current
no active autotune expansion task
one clear next product milestone
```

## Integration Plan

1. Finish documentation lock on current recovery branch.
2. Execute operator runbook task.
3. Execute physical MVP smoke.
4. If smoke is GO/WARN, run recording demo.
5. If demo passes, prepare master PR with known limitations.
6. If demo blocks, open exactly one blocker task.
7. After MVP demo decision, start debt reduction sprint.

## Session Status (2026-06-05)

Codex prepared this schedule after the MVP recovery audit and lightweight autonomy update. No production code was changed. The plan is intended to be executed by autonomous agents using Green/Yellow/Red Lane classification.
