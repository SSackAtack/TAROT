# Wykaz Zmian (Changelog) — TASK-WF-001

## 1. Nowo Utworzone Pliki

### `.ai/AI_WORKFLOW_FAILOVER.md`
* Zasady i role w zespole AI oraz reguły failover.

### `.ai/PROJECT_STATE.md`
* Kompletne techniczne i operacyjne podsumowanie stanu projektu dla nowych agentów.

### `.ai/TASKS_INDEX.md`
* Rejestr i indeks wszystkich zadań AI.

### `.ai/tasks/README.md`
* Wyjaśnienie struktury zadań.

### `.ai/tasks/_TEMPLATE/`
* Szablony plików zadań: `TASK.md`, `STATE.md`, `CHANGELOG.md`, `TEST_REPORT.md`, `GEMINI_NOTES.md`, `OPEN_ISSUES.md`.

### `app_cv/requirements.txt`
* Plik zależności backendu potrzebny do poprawnego działania testów w środowisku CI.

### `.github/workflows/ci.yml`
* Plik konfiguracyjny GitHub Actions orkiestrujący automatyczne testy i kompilację backendu oraz kompilację produkcyjną frontendu.

### `.github/pull_request_template.md`
* Szablon Pull Requesta na GitHubie dla zespołu AI.

---

## 2. Modyfikowane Pliki

### `README.md`
* Wstrzyknięto sekcję `AI Workflow / Failover` wskazującą na katalog `.ai/` jako nadrzędne źródło prawdy dla zespołów AI.

### `AGENTS.md`
* Wstrzyknięto sekcję `Required startup sequence for AI agents` wymuszającą rygorystyczny proces startowy przed rozpoczęciem jakichkolwiek prac kodowych.
