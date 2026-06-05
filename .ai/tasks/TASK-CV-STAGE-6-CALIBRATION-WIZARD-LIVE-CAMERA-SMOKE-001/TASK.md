# TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001

## Goal
Zweryfikować pełny przepływ Asystenta Kalibracji Stanowiska na realnym stanowisku:
- laptop: HP EliteBook 830 G6,
- kamera: AnkerWork C310,
- backend CV,
- WebSocket,
- Studio UI z panelem Calibration Wizard,
- przyciski: Pusta mata, 1 karta, 3 karty, Skalibruj, Anuluj,
- realny obraz z kamery, a nie tylko mock / emulacja.

Celem taska jest **live smoke test**, nie rozwój nowych funkcji.

---

## Scope
Wykonaj wyłącznie test integracyjny live z fizyczną kamerą.

---

## Out of Scope
- Nie zmieniać algorytmów CV
- Nie zmieniać backendowego payloadu WebSocket
- Nie zmieniać kontraktu `operator.calibration.autotune`
- Nie dodawać nowych zależności
- Nie przebudowywać UI/CSS
- Nie oznaczanać jako `APPROVED BY CHATGPT SUPERVISOR` przed finalnym review.

---

## Files Allowed to Change
- `.ai/TASKS_INDEX.md`
- `.ai/tasks/TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001/*`
- `walkthrough.md` i screenshoty w tym katalogu.
