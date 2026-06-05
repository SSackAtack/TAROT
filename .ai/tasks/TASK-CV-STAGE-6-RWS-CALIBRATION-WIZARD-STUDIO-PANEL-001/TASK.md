# TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STUDIO-PANEL-001

## Context

Projekt TAROT / TarotVision ma już zakończone i zatwierdzone na `master` backendowe etapy Calibration Wizard:
- TASK-CV-STAGE-6-RWS-AUTOTUNE-RUNTIME-COMMANDS-001 (WebSocket lifecycle komend wizardu/autotune)
- TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SAMPLE-CAPTURE-001 (kontrolowane zbieranie próbek)
- TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SCORING-001 (scoring jakości)
- TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STATUS-SNAPSHOT-001 (stabilny kontrakt backendowy)

Backend wystawia już stabilny payload: `operator.calibration.autotune` z odpowiednimi polami.

Ten task jest pierwszym etapem frontendowym dla wizardu kalibracji.

---

## Goal

Dodać w Studio UI prosty panel Calibration Wizard, który wyświetla status backendowego asystenta kalibracji na podstawie istniejącego payloadu: `calibration.autotune`.
Panel ma pomóc operatorowi zobaczyć:
- czy wizard jest aktywny,
- jaki scenariusz jest aktualnie zbierany,
- ile próbek zebrano,
- czy można wykonać scoring,
- jaki jest wynik quality_report,
- jakie są komunikaty / ostrzeżenia / blokady,
- jaki jest następny sugerowany krok.

Ten task NIE ma zmieniać backendu.

Etykieta w UI: "Asystent kalibracji stanowiska" lub "Kalibracja stanowiska".

---

## Scope

W ramach taska wykonaj tylko frontendową prezentację statusu wizardu oraz bezpieczną interakcję poprzez komendy WebSocket.

### 1. Odczyt danych
Panel ma czytać dane ze stanu Studio UI: `operator.calibration.autotune`.
Bezpieczna obsługa braku danych (fallback na DEFAULT_CALIBRATION_WIZARD_STATUS).

### 2. Dodaj sekcję UI w Studio
Dodaj sekcję w panelu Studio, np. "Asystent kalibracji".
Pokazać:
- Stan (state, scenario, next_action)
- Postęp (collected_count / required_count, ready_to_score)
- Ocena (quality_report.score, quality_report.grade, current_step_ready, overall_wizard_ready)
- Komunikaty (operator_messages, warnings, blocking_issues)

### 3. Komendy
Jeśli to możliwe, zintegrować przyciski sterujące:
- `autotune_start` (z wyborem scenariusza: `empty`, `one_card`, `three_cards`)
- `autotune_calibrate` (czyli scoring / kalibracja)
- `autotune_cancel` (anulowanie)

---

## Out of Scope
- Żadnych zmian w `app_cv/*`
- Żadnych zmian w payloadzie WebSocket
- Żadnych nowych bibliotek frontendowych
- Żadnego dużego redesignu

---

## Files Allowed to Change
- `app_ar/src/studio/studioConsole.js`
- `app_ar/studio.css`
- `app_ar/index.html` (warunkowo)
- `app_ar/src/main.js` (warunkowo)
- Pliki w `.ai/tasks/TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STUDIO-PANEL-001/*`
- `.ai/TASKS_INDEX.md`
