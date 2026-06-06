# TarotVision MVP Recovery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan when multiple independent work items can be split across agents. Use `superpowers:verification-before-completion` before marking any implementation task complete.

**Goal:** odzyskać koncentrację projektu na pierwszym używalnym MVP: operator-assisted recording workflow z jedną talią, stabilnym preview, kontrolowanym smoke testem i możliwością nagrania krótkiej sesji.

**Architecture:** zachować obecny snapshot-first runtime jako ścieżkę produkcyjną. Autotune/Calibration Wizard traktować jako preflight i diagnostykę, nie jako główny produkt ani obszar dalszego rozrostu przed MVP.

**Tech Stack:** Python/OpenCV backend w `app_cv`, Vite/JavaScript Studio w `app_ar`, lokalny WebSocket runtime, dokumentacja w `.ai/`, `docs/` i `analizy/`.

---

## Status ogólny

### Stan aktualny

Projekt ma działającą ścieżkę snapshot-first i ostatni fizyczny smoke `one_card` na Gilded zakończył się `PASS`, `3/3`, `accepted_total=3`. To oznacza, że obecny kierunek CV jest wystarczająco obiecujący dla MVP.

Jednocześnie proces prac zaczął dryfować w stronę autotuningu, kalibracji i diagnostyki jako celu samego w sobie. To tworzy dużo aktywności, ale nie prowadzi liniowo do pierwszego nagrania.

### Co zostało zrobione

- Potwierdzono, że problem `one_card` nie jest już twardym blockerem po spójnej konfiguracji Gilded.
- Zidentyfikowano autotuning jako główną ślepą uliczkę procesową.
- Zdefiniowano MVP jako recording-ready operator workflow, a nie perfekcyjny optimizer.
- Ustalono, że `active_decks.json` jest lokalną konfiguracją operatora i nie może być commitowany w taskach kodowych/dokumentacyjnych.

### Kolejne kroki

Wykonać poniższe zadania w kolejności. Nie zaczynać nowych prac tuningowych przed zakończeniem Task 1 i Task 2.

---

## WIP Limit

- Maksymalnie 2 aktywne taski kodowe naraz.
- Maksymalnie 1 aktywny task CV/tuning naraz.
- Maksymalnie 1 branch oczekujący na decyzję Michała.
- Każdy nowy task musi wskazać bezpośredni wpływ na MVP.
- Task autotune jest dopuszczalny tylko, jeśli usuwa konkretny blocker smoke/demo albo redukuje złożoność.
- `app_ar/public/active_decks.json` pozostaje lokalną konfiguracją operatora i nie jest commitowany bez wyraźnej zgody.

---

## Task 1: MVP Recovery Lock

**Status:** wykonane 2026-06-06
**Cel:** jawnie zamrozić rozrost autotuningu i ustawić wspólną definicję sukcesu MVP.

### Files

- `.ai/PROJECT_STATE.md`
- `.ai/TASKS_INDEX.md`
- `README.md`
- `analizy/audyt_mvp_recovery_2026-06-05.md`

### Step 1: Update project state

W `.ai/PROJECT_STATE.md` dopisać sekcję:

```markdown
## MVP Recovery Mode (2026-06-05)

Aktualny priorytet: pierwsze recording-ready MVP na jednej kontrolowanej talii.
Autotune/Calibration Wizard jest traktowany jako preflight i diagnostyka, nie jako główny cel produktu.

Freeze do czasu MVP:
- nowe profile autotune,
- dalsze luzowanie geometrii bez regresji smoke,
- multi-deck hardening,
- duże refaktory runtime/UI.
```

### Step 2: Verify task index status

Status taska recognition acceptance został skorygowany w audycie na `DONE`, ponieważ live smoke `one_card` Gilded przeszedł `3/3`. Przy kolejnej aktualizacji indeksu tylko potwierdzić, że notatka pozostaje zgodna z rzeczywistością:

```markdown
one_card Gilded live smoke PASS 3/3; następny krok to MVP smoke three_cards/recording, nie dalszy autotuning
```

### Step 3: Update README

Usunąć lub skorygować nieaktualne opisy sugerujące wyłącznie stary PoC 22 Major Arcana RWS, jeśli kolidują z aktualnym stanem projektu.

### Verification

Run:

```powershell
git diff -- .ai/PROJECT_STATE.md .ai/TASKS_INDEX.md README.md
git diff -- app_ar/public/active_decks.json
```

Expected:

- dokumentacja opisuje MVP Recovery Mode,
- `active_decks.json` nie jest staged,
- brak zmian kodu runtime.

---

## Task 2: Operator MVP Runbook

**Status:** zaplanowane
**Cel:** operator ma jedną instrukcję przejścia od startu aplikacji do gotowości nagrania.

### Files

- `docs/operator/mvp_recording_runbook.md`

### Step 1: Create runbook

Utworzyć dokument z sekcjami:

```markdown
# TarotVision MVP Recording Runbook

## Setup
- fizyczna talia:
- aktywna talia:
- kamera:
- mata:
- światło:

## Start
- uruchom backend/CV:
- uruchom Studio:
- sprawdź port 8765:
- sprawdź preview:

## Preflight
- EMPTY:
- ONE_CARD:
- THREE_CARDS:

## Decision
- GO:
- WARN:
- STOP:

## Recovery
- konflikt portu:
- czarne preview:
- warningi kamery:
- niezgodna talia:
```

### Step 2: Define warnings

W runbooku jawnie zapisać:

- same warningi kamery są `WARN`, jeśli preview i sample działają,
- czarne preview albo brak sampli to `STOP`,
- niezgodność talii fizycznej i aktywnej to `STOP`.

### Verification

Run:

```powershell
git diff -- docs/operator/mvp_recording_runbook.md
```

Expected:

- operator może przejść przez smoke bez czytania historii czatu,
- brak zależności od nowych zmian w kodzie.

---

## Task 3: MVP Physical Smoke

**Status:** zaplanowane
**Cel:** zastąpić dalszy autotuning jednym product-level smoke testem.

### Inputs

- fizyczna talia: Gilded
- aktywna talia runtime: `gilded`
- branch runtime: aktualna gałąź MVP/snapshot-first
- kamera: aktualna kamera operatora

### Protocol

1. `EMPTY`
   - oczekiwane: `3/3`
   - false positives: NIE
   - warningi HUD: brak fałszywych blokad
2. `ONE_CARD`
   - oczekiwane: `3/3`
   - `accepted_total=3`
   - detected count stabilny
3. `THREE_CARDS`
   - oczekiwane: PASS
   - jeśli FAIL, sklasyfikować: geometry / recognition / operator setup / camera
4. Studio preview
   - obraz widoczny
   - brak czarnego preview
5. Runtime
   - brak konfliktu portu 8765
   - warningi kamery tylko jako `WARN`, jeśli próbki przechodzą

### Output

Zapisać raport:

```markdown
PHYSICAL_SMOKE_MVP_GILDED

Branch:
HEAD:
Physical deck:
Active deck:

EMPTY:
ONE_CARD:
THREE_CARDS:
Preview:
Camera warnings:
Decision: GO / WARN / STOP
Next:
```

### Stop condition

- Jeśli `three_cards` przejdzie: nie tuningować dalej; przejść do recording demo.
- Jeśli `three_cards` nie przejdzie: ocenić manual fallback przed zmianą progów CV.
- Jeśli `empty` failuje: zatrzymać i naprawić false positives.

---

## Task 4: Manual Fallback Decision

**Status:** zaplanowane
**Cel:** upewnić się, że MVP da się nagrać nawet przy pojedynczym błędzie recognition.

### Step 1: Inspect current UI/runtime

Sprawdzić, czy istnieje mechanizm:

- ręcznego wyboru lub korekty karty,
- zatwierdzenia rozpoznanej karty,
- anulowania złego wyniku bez restartu sesji.

### Step 2: Decision

Jeśli mechanizm istnieje:

- opisać go w runbooku,
- przetestować w krótkim flow.

Jeśli mechanizm nie istnieje:

- zaplanować minimalny operator override jako osobny task,
- nie rozbudowywać autotune jako obejścia.

### Verification

Raport powinien odpowiedzieć:

```markdown
Manual fallback available: YES / NO
Can recover during recording: YES / NO
Needs implementation before MVP demo: YES / NO
```

---

## Task 5: Recording-Ready Demo

**Status:** zaplanowane
**Cel:** wykonać pierwszą krótką sesję demonstracyjną.

### Requirements

- Gilded jako jedyna aktywna talia.
- Preflight zakończony `GO` albo `WARN` bez twardych blockerów.
- Studio/AR pokazuje wynik.
- Operator ma fallback albo świadomie akceptuje ograniczenie.
- Sesja trwa wystarczająco długo, aby ocenić workflow, nie tylko pojedynczą próbkę.

### Output

Dokument:

```markdown
MVP_RECORDING_DEMO_REPORT

Date:
Branch:
Deck:
Duration:
Preflight decision:
Recognition result:
Operator interventions:
Blocking issues:
Backlog after demo:
MVP decision: PASS / FAIL
```

### Stop condition

Po udanym demo nie zaczynać nowego tuningu. Najpierw zaktualizować dokumentację, backlog i decyzję produktu.

---

## Quality Gates

### Do not start

Nie zaczynać zadań, które:

- dodają nowe profile autotune,
- luzują geometrię bez świeżego `empty` fail,
- rozszerzają talie,
- robią duży refaktor bez bezpośredniego wpływu na recording demo.

### Must verify

Każdy task przed commitem:

```powershell
git status
git diff -- app_ar/public/active_decks.json
git restore --staged app_ar/public/active_decks.json
```

Nie wykonywać:

```powershell
git restore app_ar/public/active_decks.json
```

bez zgody operatora.

---

## Session Status (2026-06-05)

Codex wykonał audyt i zapisał plan recovery. Nie zmieniono kodu runtime. `active_decks.json` pozostał lokalną konfiguracją operatora i ma być pominięty w commicie.

Commit hash: `a92ef1f`.

## Session Status (2026-06-06)

Codex rozpoczął wykonanie planu naprawczego od Task 0 / MVP Recovery Lock. Zaktualizowano stan projektu, dodano WIP limit i oznaczono stare taski autotune/offline jako historyczne względem MVP Recovery Mode. Nie zmieniono kodu runtime. `active_decks.json` pozostał lokalną konfiguracją operatora i ma być pominięty w commicie.

Commit hash: recorded in git history for `docs: ustaw tryb MVP recovery`.
