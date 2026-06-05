# AI Agent Communication Protocol — TarotVision

Ten dokument definiuje standard przekazywania informacji między modelami AI pracującymi nad projektem TAROT / TarotVision.

Cel: Michał nie musi kopiować instrukcji między modelami ani decydować, czy informacja ma trafić do issue, PR review, komentarza czy pliku `.md`. Model zapisujący informację wybiera właściwy kanał GitHuba.

Aktualizacja 2026-06-05: protokół nie wymusza stałej kontroli Supervisora. Każdy agent może samodzielnie realizować i weryfikować prace niskiego ryzyka na branchu roboczym. Supervisor review jest wymagane tylko wtedy, gdy Michał o to poprosi, zmiana jest podwyższonego ryzyka albo dotyczy merge do `master`.

---

## 1. Zasada główna

Michał może wybrać:

- który model zaczyna temat,
- który model ma sprawdzić wynik,
- czy informacja ma zostać zapisana w GitHubie.

Model AI wybiera miejsce zapisu.

Jeśli Michał zleca agentowi normalną pracę nad kodem, agent nie musi czekać na ChatGPT Supervisora przed implementacją. Agent klasyfikuje ryzyko zadania i działa zgodnie z poniższymi progami.

| Lane | Kiedy | Uprawnienia agenta | Review |
|---|---|---|---|
| Green | Mała/średnia zmiana w istniejącym zakresie, jasne testy, brak publicznego API | implementuj, testuj, commituj, pushuj na branch | niewymagane |
| Yellow | Kilka modułów, runtime, nowy moduł, kontrakt frontend/backend, niepełna weryfikacja | implementuj na branchu i oznacz ryzyka | rekomendowane przed merge |
| Red | Architektura, stack, model produktu, kasowanie danych/testów, merge do `master` | zatrzymaj się przed decyzją albo merge | decyzja Michała wymagana |

| Sytuacja | Kanał GitHuba |
|---|---|
| Nowy temat, brak PR | GitHub Issue |
| Nowy temat wysokiego ryzyka | GitHub Issue + `.ai/tasks/TASK-XXX/` |
| Istnieje PR | Komentarz w PR albo formalne PR Review |
| Problem dotyczy konkretnej linii diffu | Inline review comment |
| Decyzja jakościowa | Formalne PR Review |
| Wiedza długoterminowa / failover | Plik w `.ai/` albo `.ai/tasks/TASK-XXX/` |
| Brak potrzeby utrwalania | Tylko czat |

---

## 2. Komendy Michała

### Start u ChatGPT Supervisor

```text
ChatGPT, zacznij temat: <opis problemu>
```

Przekazanie do Gemini:

```text
Przekaż Gemini.
```

### Start u Gemini

```text
Gemini, zrób: <opis zadania>
```

Agent może wykonać Green Lane zadanie end-to-end bez osobnego review. Po zakończeniu wystarczy:

```text
Gemini/Codex/Opus, zrób, zweryfikuj i wypchnij na branch: <opis zadania>
```

Po zakończeniu Yellow/Red Lane albo gdy Michał chce niezależnego sprawdzenia:

```text
ChatGPT, Gemini skończył, sprawdź.
```

### Ponowna weryfikacja

```text
ChatGPT, Gemini poprawił, sprawdź ponownie.
```

---

## 3. Znaczenie komendy „Zapisz to w GitHubie”

Ta komenda oznacza zgodę na zapis komunikacji projektowej:

- issue,
- komentarza w PR lub issue,
- formalnego PR Review,
- pliku `.md` w `.ai/` albo `.ai/tasks/TASK-XXX/`.

Nie oznacza zgody na:

- zmianę kodu produkcyjnego,
- merge do `master`,
- kasowanie plików,
- zamykanie PR/issue,
- duży refaktor,
- zmianę architektury.

Takie działania wymagają osobnej zgody Michała, jeśli wpadają w Red Lane. Dla Green Lane zwykłe commit/push na branch roboczy jest częścią normalnej pracy agenta, o ile użytkownik nie zabronił zmian.

---

## 4. Handoff i review

Formalny handoff jest wymagany tylko dla Yellow/Red Lane, pracy wieloetapowej, przejęcia przez inny model albo review przed merge. Dla Green Lane wystarcza finalny opis zmian, testy i commit.

ChatGPT Supervisor może przekazać zadanie do Gemini w krótkim formacie:

```markdown
# SUPERVISOR HANDOFF — TASK-XXX

## Decision
DO_THIS_TASK / FIX_REQUIRED / BLOCKED / REVIEW_REQUESTED

## Goal
Krótki cel.

## Scope
Co wolno zrobić.

## Out of Scope
Czego nie wolno robić.

## Files Allowed to Change
- `path/to/file`

## Acceptance Criteria
- Warunek 1
- Warunek 2

## Tests Required
- Komenda testowa albo `NOT_REQUIRED` z uzasadnieniem.

## Reports Required
- Co Gemini ma zapisać po pracy.

## Branch
`task/...`

## Commit Message
`type: krótki opis`
```

---

## 5. Agent Report

Po wykonaniu Yellow/Red Lane albo pracy przekazywanej innemu agentowi wykonawca zostawia krótki raport:

```markdown
# AGENT REPORT — TASK-XXX

## Task
Nazwa / numer taska.

## Branch
Branch roboczy.

## Base Commit
Commit przed pracą.

## Head Commit
Commit po pracy.

## Files Changed
- `path/to/file`

## Summary
Co zmieniono.

## Tests Run
- `command` => PASS/FAIL/NOT_RUN

## Known Risks
- Ryzyko albo `brak`.

## Review Request
NOT_REQUIRED / REVIEW_RECOMMENDED / HELP / BLOCKER_DECISION
```

---

## 6. ChatGPT Supervisor Review

ChatGPT Supervisor review jest opcjonalne dla Green Lane i zalecane/wymagane zgodnie z progami ryzyka. Po review używa formatu:

```markdown
# CHATGPT_SUPERVISOR_REVIEW — TASK-XXX / PR-XXX

## Summary
Co sprawdzono.

## Decision
APPROVED_BY_CHATGPT_SUPERVISOR / CHANGES_REQUESTED_BY_CHATGPT_SUPERVISOR / REJECTED_BY_CHATGPT_SUPERVISOR / PROVISIONAL_BLOCKED

## Risk Level
LOW / MEDIUM / HIGH / CRITICAL

## Scope Check
Czy zmiana mieści się w zakresie taska.

## Task Size Check
Czy zachowano zasadę 1–3 plików produkcyjnych albo czy jest Human Override.

## Test Check
Jakie testy uruchomiono i czego nie sprawdzono.

## Critical Issues
Problemy blokujące merge.

## Important Issues
Problemy ważne przed merge albo do kolejnego taska.

## Improvement Ideas
Usprawnienia, tylko jeśli realnie wnoszą wartość.

## Architecture Notes
Wpływ na architekturę.

## Failover Readiness
Czy inny agent może przejąć pracę wyłącznie z repo.

## Required Next Action
Jedna konkretna rekomendacja.
```

---

## 7. Lokalna kopia

Ten plik jest częścią repozytorium. Po wykonaniu `git pull` instrukcja będzie lokalnie dostępna jako:

```text
.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md
```

Nie trzeba tworzyć osobnej lokalnej instrukcji poza repozytorium.
