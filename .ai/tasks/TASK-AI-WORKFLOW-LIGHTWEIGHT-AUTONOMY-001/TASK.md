# TASK-AI-WORKFLOW-LIGHTWEIGHT-AUTONOMY-001

## Tytuł

Uproszczenie zasad współpracy agentów AI.

## Cel

Zmniejszyć ciężar formalnego review Supervisora i umożliwić każdemu agentowi samodzielną pracę nad kodem w zakresie niskiego ryzyka, bez ciągłego wymuszania kontroli ChatGPT/Codex Supervisora.

## Zakres dozwolony

- `AGENTS.md`
- `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`
- `.ai/PROJECT_STATE.md`
- `.ai/TASKS_INDEX.md`
- `analizy/audyt_zasad_wspolpracy_agentow_2026-06-05.md`
- `.ai/tasks/TASK-AI-WORKFLOW-LIGHTWEIGHT-AUTONOMY-001/`

## Poza zakresem

- kod produkcyjny,
- zmiany runtime,
- zmiany testów,
- merge do `master`,
- `app_ar/public/active_decks.json`.

## Kryteria ukończenia

- Zasady jasno rozróżniają Green / Yellow / Red Lane.
- Green Lane pozwala agentowi implementować, testować, commitować i pushować bez Supervisora.
- Yellow Lane rekomenduje review przed merge, ale nie blokuje pracy.
- Red Lane nadal wymaga decyzji Michała.
- Dokumenty nie sugerują już, że Supervisor jest obowiązkową bramką każdej pracy.
