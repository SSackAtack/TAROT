# TASK-COMM-001: Standard komunikacji między modelami AI przez GitHub

## Goal
Ustandaryzować sposób przekazywania informacji między ChatGPT Supervisor, Gemini, Codex i Opus tak, aby Michał nie musiał ręcznie kopiować instrukcji między modelami ani decydować, czy informacja ma trafić do issue, komentarza, PR review czy pliku `.md`.

## Scope
- Dodać dokument `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`.
- Zaktualizować `.ai/AI_WORKFLOW_FAILOVER.md` o odwołanie do protokołu.
- Zaktualizować `.ai/PROJECT_STATE.md` o informację, że standard komunikacji został wdrożony.
- Zarejestrować task w `.ai/TASKS_INDEX.md`.

## Out of Scope
- Zmiany w kodzie produkcyjnym.
- Zmiany architektury aplikacji.
- Merge, zamykanie PR/issue, usuwanie plików.
- Automatyczne działania bez wywołania przez Michała.

## Files Allowed to Change
- `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`
- `.ai/AI_WORKFLOW_FAILOVER.md`
- `.ai/PROJECT_STATE.md`
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-COMM-001/TASK.md`
- `.ai/tasks/TASK-COMM-001/STATE.md`
- `.ai/tasks/TASK-COMM-001/CHANGELOG.md`
- `.ai/tasks/TASK-COMM-001/TEST_REPORT.md`

## Acceptance Criteria
- Modele AI mają jednoznaczny dokument opisujący, gdzie zapisywać informacje zależnie od sytuacji.
- Michał może używać prostych komend typu „Przekaż Gemini”, „Gemini skończył, sprawdź”, „Zapisz to w GitHubie”.
- Komenda „Zapisz to w GitHubie” jest ograniczona do komunikacji projektowej i nie oznacza zgody na zmianę kodu produkcyjnego.
- Dokument jest częścią repozytorium i będzie dostępny lokalnie po `git pull`.

## Tests Required
NOT_REQUIRED — zmiana dotyczy wyłącznie dokumentacji procesu. Nie zmienia kodu produkcyjnego, testów ani konfiguracji runtime.

## Reports Required
- `STATE.md`
- `CHANGELOG.md`
- `TEST_REPORT.md`

## Branch
`master` — dokumentacyjna aktualizacja wykonana na wyraźne polecenie Michała.

## Commit Message
`docs: add AI agent communication protocol`
