# [TASK-WF-001] — AI Workflow, CI i PR Bootstrap

## 1. Cel i Tło Techniczne

Celem tego zadania jest stworzenie i wdrożenie oficjalnego systemu automatycznej kontroli jakości (CI), rygorystycznych reguł współpracy zespołowej AI (Workflow Failover) oraz szablonów Pull Requestów. Zapobiega to regresji technicznej przy wprowadzaniu kolejnych funkcjonalności w projekcie TarotVision i zapewnia ciągłość pracy przy przejmowaniu zadań przez różne modele AI.

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

### Pliki Nowo Utworzone
* `[NEW]` `.ai/AI_WORKFLOW_FAILOVER.md`
* `[NEW]` `.ai/PROJECT_STATE.md`
* `[NEW]` `.ai/TASKS_INDEX.md`
* `[NEW]` `.ai/tasks/README.md`
* `[NEW]` `.ai/tasks/_TEMPLATE/` (szablony dokumentacji zadań)
* `[NEW]` `app_cv/requirements.txt` (dependencies dla środowiska testowego)
* `[NEW]` `.github/workflows/ci.yml` (konfiguracja GitHub Actions CI)
* `[NEW]` `.github/pull_request_template.md` (szablon PR)

### Pliki Modyfikowane
* `[MODIFY]` `README.md` (dodanie sekcji AI Workflow)
* `[MODIFY]` `AGENTS.md` (dodanie sekwencji startowej agenta)

---

## 3. Poza Zakresem (Out of Scope)

* Brak zmian w algorytmach detekcji kart tarota.
* Brak modyfikacji logiki WebSocket / Protocol.
* Brak jakichkolwiek zmian w kodzie produkcyjnym konsoli Studio oraz widoku AR.

---

## 4. Kryteria Akceptacji (Acceptation Criteria)

- [x] Katalog `.ai` wraz z plikami PROJECT_STATE, TASKS_INDEX i AI_WORKFLOW_FAILOVER istnieje.
- [x] Plik `.github/workflows/ci.yml` jest poprawnie skonfigurowany i przygotowany na uruchomienie w GitHub Actions.
- [x] Szablon Pull Requesta `.github/pull_request_template.md` istnieje.
- [x] Pliki `README.md` i `AGENTS.md` wskazują katalog `.ai` jako jedyne źródło prawdy dla agentów.
- [x] Wszystkie testy jednostkowe Pythona (171 testów) i produkcyjny build Vite przechodzą pomyślnie na nowej gałęzi `workflow/ci-bootstrap`.
