# STATE — TASK-AI-WORKFLOW-LIGHTWEIGHT-AUTONOMY-001

## Status

DONE — zasady współpracy uproszczone dokumentacyjnie.

## Branch

`codex/project-mvp-recovery-audit-2026-06-05`

## Stan aktualny

Dotychczasowe zasady były zbyt rygorystycznie interpretowane: ChatGPT/Codex Supervisor stał się domyślnym gatekeeperem nawet dla małych zmian. Nowy model wprowadza autonomię domyślną z progami ryzyka.

## Co zostało zrobione

- Dodano audyt zasad współpracy agentów.
- Zaktualizowano `AGENTS.md`.
- Zaktualizowano `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`.
- Zaktualizowano `.ai/PROJECT_STATE.md`.
- Dodano wpis w `.ai/TASKS_INDEX.md`.
- Nie zmieniono kodu produkcyjnego.

## Kolejne kroki

1. Stosować Green Lane do małych i średnich zmian bez wymuszania Supervisora.
2. Stosować Yellow Lane dla zmian runtime/API i oznaczać review jako rekomendowane przed merge.
3. Stosować Red Lane tylko dla architektury, destrukcyjnych zmian, stacku, modelu produktu i merge do `master`.
