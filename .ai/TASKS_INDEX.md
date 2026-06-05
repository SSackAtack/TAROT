# Indeks Zadań AI — TarotVision (TAROT)

Ten plik stanowi centralny rejestr wszystkich zadań (Tasks) realizowanych w projekcie TarotVision przez zespół AI. Każde zadanie musi posiadać swój wpis w tabeli oraz dedykowany katalog szczegółów w `.ai/tasks/TASK-XXX/`.

---

## Rejestr Zadań

| Task ID | Status | Gałąź (Branch) | Realizator (Owner) | Zakres (Scope) | Ostatnia aktualizacja | Status Review |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TASK-WF-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Scaffold struktury `.ai/` i standardy workflow | 2026-05-30 | ChatGPT Approved |
| **TASK-CI-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Konfiguracja GitHub Actions CI & requirements.txt | 2026-05-30 | Included in TASK-WF-001 |
| **TASK-PR-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Szablon Pull Request (.github/pull_request_template.md) | 2026-05-30 | Included in TASK-WF-001 |
| **TASK-DOC-001** | `DONE` | `workflow/ci-bootstrap` | Gemini | Aktualizacja README + AGENTS.md (startup sequence) | 2026-05-30 | Included in TASK-WF-001 |
| **TASK-CI-SMOKE-001** | `APPROVED` | `master` | Gemini | Weryfikacja dymna GitHub Actions na gałęzi master | 2026-05-30 | CI Confirmed Green (PASS) |
| **TASK-SCAN-001** | `APPROVED` | `master` | Gemini | Dostosowanie skryptu obróbki skanów pod skaner i jakość Premium | 2026-05-30 | ChatGPT Approved (PR #2) |
| **TASK-SCAN-002** | `APPROVED` | `master` | Gemini | Diagnostyka i uodpornienie skanowania WIA na flary i tła | 2026-05-31 | Confirmed 5/5 Green |
| **TASK-DECK-001** | `APPROVED` | `master` | Gemini | Wdrożenie nowej talii Zodiak i obsługa wielu talii w locie | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-002** | `APPROVED` | `master` | Gemini | Wdrożenie talii Magic i Gilded z integracją w launcherze i cache | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-003** | `APPROVED` | `master` | Gemini | Wdrożenie talii Marchetti z integracją w launcherze i cache | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-004** | `APPROVED` | `master` | Gemini | Wdrożenie talii Boski z integracją w launcherze i cache | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-SCAN-004** | `APPROVED` | `master` | Gemini | Usprawnienie auto-orientacji kart i segmentacji tła | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-COMM-001** | `APPROVED` | `master` | ChatGPT Supervisor | Standard komunikacji między modelami AI przez GitHub | 2026-05-31 | Self-documented, owner requested |
| **TASK-DECK-005** | `APPROVED` | `master` | Gemini | Wdrożenie talii Światło i Cień z integracją oraz uodpornieniem zapisu Unicode na Windowsie | 2026-05-31 | Confirmed 171/171 Green |
| **TASK-DECK-006** | `APPROVED` | `master` | Gemini | Manifest talii i konfiguracja aktywnych talii sesji 1–3 talie | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-007** | `APPROVED` | `master` | Gemini | Frontend lazy loading tylko aktywnych talii | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-008** | `APPROVED` | `master` | Gemini | Backend CV registry tylko dla aktywnych talii | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-009** | `APPROVED` | `master` | Gemini | WebSocket payload z deck_id + card_id | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-DECK-010** | `APPROVED` | `master` | Gemini | UI wyboru 1–3 talii w Studio / launcherze | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR (PR #4) |
| **TASK-STUDIO-006** | `APPROVED` | `master` | Gemini | Diagnostyka CV Health Minimal i Dedykowany Launcher Studio | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR (PR #5) |
| **TASK-STUDIO-007** | `APPROVED` | `master` | Gemini | Uodpornienie launchera Studio pod zajęty port 5173 | 2026-05-31 | APPROVED BY CHATGPT SUPERVISOR (PR #6 + PR #9 fix) |
| **TASK-STUDIO-CV-EXPLAIN-001** | `APPROVED` | `master` | Codex | Panel CV Explain z przyczynami problemów i następnym krokiem operatora | 2026-06-02 | Local merge approved after full verification |
| **TASK-STUDIO-CV-EXPLAIN-002** | `TODO` | `task/studio-cv-explain-002-candidate-accepted-gap` | Codex/Gemini | Doprecyzowanie komunikatu różnicy między kandydatami kart a zaakceptowanymi rozpoznaniami | 2026-06-02 | Zaplanowane po live smoke |
| **TASK-CV-RECT-001** | `DONE` | `task/cv-rect-001-parameterize-card-detection` | Gemini | Parametryzacja detekcji prostokątów kart pod autotuning | 2026-05-31 | Oczekuje na review |
| **TASK-CV-AUTOTUNE-001** | `DONE` | `task/cv-autotune-001-offline-single-frame` | Gemini | Prototyp offline autotunera detekcji prostokąta karty | 2026-05-31 | Oczekuje na review |
| **TASK-CV-SNAPSHOT-001** | `APPROVED` | `master` | Codex | Usunięcie legacy state-first i utrwalenie snapshot-first jako jedynego pipeline CV | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-002** | `APPROVED` | `master` | Codex | Unicode-safe image I/O i reference loader poza main.py | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-003** | `APPROVED` | `master` | Codex | Analiza snapshotu na klatce sprostowanej przez ArUco | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-004** | `APPROVED` | `master` | Codex | Diagnostyka porażek detekcji i rozpoznania snapshot-first | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-005** | `APPROVED` | `master` | Codex | Wieloprofilowa detekcja kart dla ciemnych talii i mat | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-006** | `APPROVED` | `master` | Codex | Opcjonalny model pustej maty dla background-diff | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-007** | `APPROVED` | `master` | Codex | Recognition-aware snapshot autotuning offline | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-008** | `APPROVED` | `master` | Codex | Lokalny benchmark snapshot recognition dla talii i mat | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-SNAPSHOT-LIVE-001** | `APPROVED` | `master` | Gemini + Michał | Live smoke test snapshot-first z kamerą i Studio | 2026-06-01 | Test na żywo zakończony pełnym sukcesem (GREEN), potwierdzony po merge |
| **TASK-CV-GEOMETRY-FALLBACK-001** | `APPROVED` | `master` | Codex | MinAreaRect fallback, diagnostyka detekcji i filtr ArUco dla snapshot-first live | 2026-06-01 | APPROVED BY CHATGPT SUPERVISOR (PR #14 + master smoke) |
| **TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Research Gate Stage 1: metody detekcji różnic dla offline labu state-first | 2026-06-03 | Research complete; pending Supervisor stage decision |
| **TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Codex | Offline benchmark Stage 1 Difference Detection na zatwierdzonych fixture | 2026-06-03 | Stage 1 method approved: gray_absdiff_gaussian; next: Research Stage 2 |
| **TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Research Gate Stage 2: region segmentation/refinement dla offline labu state-first | 2026-06-03 | Research complete; pending Supervisor shortlist approval |
| **TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Codex | Offline benchmark Stage 2 Region Segmentation na zatwierdzonych fixture | 2026-06-03 | Stage 2 method approved: contour_external; next: Research Stage 3 |
| **TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Research Gate Stage 3: card localization / geometry extraction dla offline labu state-first | 2026-06-03 | Research complete; pending Supervisor shortlist approval |
| **TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Codex | Offline benchmark Stage 3 Card Localization / Geometry Extraction na zatwierdzonym Stage 1+2 | 2026-06-03 | Stage 3 method approved: hybrid_edge_plus_contour; next: Research Stage 4 |
| **TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Research Gate Stage 4: crop / deskew / normalize dla offline labu state-first | 2026-06-03 | Research complete; pending Supervisor shortlist approval |
| **TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Gemini | Offline benchmark Stage 4 Crop / Deskew / Normalize na zatwierdzonym Stage 1+2+3 | 2026-06-04 | Stage 4 pipeline approved: quad_warp_perspective_fixed_aspect__resize_only_normalization; next: Research Stage 5 |
| **TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Research Gate Stage 5: crop quality validation dla offline labu state-first | 2026-06-04 | Research complete; pending Supervisor shortlist approval |
| **TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Codex | Offline benchmark Stage 5 Crop Quality Validation na zatwierdzonym Stage 1+2+3+4 | 2026-06-04 | Stage 5 method approved: quality_metric_suite_v1; next: Research Stage 6 |
| **TASK-CV-OFFLINE-LAB-STAGE-5-MANUAL-REVIEW-PACK-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Paczka 6 debug sheetow do manual review Stage 5 dla quality_metric_suite_v1 | 2026-06-04 | Ready for Michal manual review |
| **TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Research Gate Stage 6: card identification dla offline labu state-first | 2026-06-04 | Research complete; pending Supervisor shortlist approval |
| **TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Preflight Stage 6 dla reference deck, deck_profile.json i ground_truth.json | 2026-06-04 | Stage 6 preflight PASS after deck profile and manually confirmed ground truth were added |
| **TASK-CV-OFFLINE-LAB-STAGE-6-DECK-PROFILE-GROUNDTRUTH-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Dane wejściowe Stage 6: Gilded deck_profile.json i ground_truth.json | 2026-06-04 | Stage 6 input data added; preflight PASS; next: Stage 6 Card Identification benchmark or manual label confirmation |
| **TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001** | `DONE` | `task/cv-stage-6-offline-lab-core` | Codex | Manualne potwierdzenie etykiet Stage 6 dla fixture Gilded | 2026-06-04 | Ground truth manual_confirmed; preflight PASS; next: Stage 6 Card Identification benchmark |
| **TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Codex | Pierwsza fala offline benchmarku Stage 6 Card Identification | 2026-06-04 | APPROVED_STAGE_6_METHOD: orb_bfmatcher_ratio_test; current offline lab fixture only; no runtime integration approval; next: broader Stage 6 validation benchmark |
| **TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-offline-lab-core` | Codex | Deterministyczny synthetic validation benchmark Stage 6: ORB vs AKAZE, reversed i wrong deck | 2026-06-04 | APPROVED_BY_CHATGPT_SUPERVISOR; VALIDATION_PASS_OFFLINE_ONLY: orb_bfmatcher_ratio_test; next: TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001; no runtime integration |
| **TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Offline tooling i procedura dla real-camera fixture Stage 6 | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-GROUND-TRUTH-REVIEW-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Ręczne rozstrzygnięcie etykiet i review ground truth dla próbki f8d6d84b5ddb5729fa07 | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-ERROR-ANALYSIS-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Analiza błędnych próbek ORB z real-camera benchmarku Stage 6 | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-IDENTIFICATION-BENCHMARK-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Offline benchmark ORB/AKAZE na real-camera fixture Stage 6 | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-DESIGN-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Projekt offline-only quality gate dla Stage 6 (detekcja flar, cieni) | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Zaimplementować offline benchmark zatwierdzonego quality gate Stage 6 | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-APPROVAL-DOC-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Dokumentacja akceptacji offline benchmarku quality gate Stage 6 | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-EXPANSION-001** | `APPROVED` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Rozszerzenie real-camera fixture (8 próbek na jasnej macie) | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Poprawka starterów/wizardów capture i testów po integracji | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001** | `APPROVED` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Offline benchmark na rozszerzonym zestawie RWS (8 próbek) | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-APPROVAL-DOC-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Dokumentacja akceptacji benchmarku RWS Expansion | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001** | `APPROVED` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Poprawa stabilności raportowania i obsługi błędów w benchmarku RWS | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-APPROVAL-DOC-001** | `DONE` | `task/cv-stage-6-rws-real-camera-benchmarks` | Gemini | Dokumentacja akceptacji poprawki stabilności benchmarku RWS | 2026-06-05 | Weryfikacja offline |
| **TASK-CV-STAGE-6-RWS-PROTOCOL-FOUNDATIONS-001** | `DONE` | `task/cv-stage-6-rws-protocol-foundations` | Gemini | Dodanie definicji i walidacji protokołu WebSocket dla Autotune (etap 1 PR-F) | 2026-06-05 | Testy targeted i backend suite OK |
| **TASK-CV-STAGE-6-RWS-AUTOTUNE-RUNTIME-COMMANDS-001** | `APPROVED` | `master` | Gemini | Wdrożenie szkieletu komend WebSocket Autotune w runtime (etap 2 PR-F) | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SAMPLE-CAPTURE-001** | `APPROVED` | `master` | Gemini | Podłączenie kontrolowanego zbierania próbek jakościowych z pipeline CV (PR-F3A) | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SCORING-001** | `APPROVED` | `master` | Gemini | Ocenianie jakości próbek asystenta kalibracji stanowiska (PR-F3B) | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STATUS-SNAPSHOT-001** | `APPROVED` | `master` | Gemini | Ustabilizowanie backendowego status snapshot dla Calibration Wizard | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STUDIO-PANEL-001** | `APPROVED` | `master` | Gemini | Panel statusu Calibration Wizard w Studio UI | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-CALIBRATION-WIZARD-LIVE-CAMERA-SMOKE-001** | `APPROVED` | `master` | Gemini | Live smoke test Asystenta Kalibracji z fizyczną kamerą | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-CALIBRATION-WIZARD-CALIBRATE-BUTTON-FIX-001** | `APPROVED` | `master` | Gemini | Naprawa przycisku Skalibruj po zebraniu próbek | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-CALIBRATION-WIZARD-SCENARIO-BUTTONS-FIX-001** | `APPROVED` | `master` | Gemini | Naprawa przycisków startu w stanie gotowej rekomendacji | 2026-06-05 | APPROVED BY CHATGPT SUPERVISOR |
| **TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-DIAGNOSTIC-001** | `DONE` | `master` | Gemini | Diagnoza i naprawa kalibracji dla scenariusza one_card i three_cards | 2026-06-05 | Zweryfikowano jednostkowo (421/421 PASS), oczekuje na smoke test |
| **TASK-CV-STAGE-6-CALIBRATION-WIZARD-RESAMPLE-GATE-DIAGNOSTIC-001** | `PENDING_SMOKE` | `master` | Gemini | Diagnoza i poprawka ponownego zbierania próbek w kreatorze kalibracji | 2026-06-05 | MERGED_PENDING_PHYSICAL_SMOKE (PR #29) |

---

## Statusy Zadań:
* `TODO` — Zadanie zaplanowane, oczekuje na realizację.
* `IN_PROGRESS` — Zadanie jest w trakcie aktywnej realizacji przez przypisanego agenta AI.
* `DONE` — Prace kodowe zostały zakończone i zweryfikowane lokalnie.
* `APPROVED` — Zadanie pomyślnie przeszło review i zostało scalone z gałęzią główną (`master`).
