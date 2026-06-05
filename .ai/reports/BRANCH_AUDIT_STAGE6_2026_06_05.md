# BRANCH AUDIT — task/cv-stage-6-rws-expansion-benchmark-001

## Executive Summary

Branch `task/cv-stage-6-rws-expansion-benchmark-001` jest kluczowym, ale niezwykle obszernym odgałęzieniem (monolitem), integrującym prace z całego etapu rozwoju Computer Vision (CV) w czerwcu 2026 roku.

Prace obejmują:
1. **Live Auto-Tuning & Scoring:** Pełna implementacja mechanizmu automatycznego dostrajania parametrów detekcji w locie (Python backend + Three.js/Vite frontend).
2. **Offline Lab (Stages 1-6):** Kompletny potok testowo-laboratoryjny służący do detekcji różnic, segmentacji, ekstrakcji geometrii, kadrowania i rozpoznawania kart.
3. **Real Camera Fixtures & Quality Gates:** Systemy eliminacji flar/odblasków (glare) i automatycznej weryfikacji jakości zdjęć z fizycznej kamery.
4. **RWS Expansion Benchmark:** Walidacja algorytmu ORB na rzeczywistych próbkach talii Rider-Waite-Smith oraz projekt polityki zachowania runtime (Runtime Policy) dla OBS/AR.

**Kluczowy wniosek techniczny:** Wszystkie **433 testy jednostkowe backendu przechodzą pomyślnie (OK)**, co dowodzi wysokiej spójności i jakości kodu. Niemniej jednak, branch narusza zasadę małych kroków (243 zmienione pliki, +31 276 linii kodu/dokumentacji) i łączy niezależne funkcjonalnie zadania deweloperskie.

---

## Branch Statistics

### Commits

Poniższa tabela przedstawia pełną listę commitów na branchu względem gałęzi `master`:

| SHA | Data | Opis | Task ID | Typ zmiany |
| :--- | :--- | :--- | :--- | :--- |
| `b8ce385` | 2026-06-04 | docs: zatwierdz runtime policy design RWS stage6 | TASK-CV-STAGE-6-RWS-RUNTIME-POLICY-DESIGN-APPROVAL-DOC-001 | DOCS |
| `32a58ac` | 2026-06-04 | docs: zaprojektuj runtime policy RWS stage6 | TASK-CV-STAGE-6-RWS-RUNTIME-POLICY-DESIGN-001 | DOCS |
| `e3f9f80` | 2026-06-04 | docs: zatwierdz robustness fix benchmarku RWS stage6 | TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-APPROVAL-DOC-001 | DOCS |
| `b9c0175` | 2026-06-04 | fix: uszczelnij raportowanie benchmarku RWS stage6 | TASK-CV-STAGE-6-RWS-BENCHMARK-ROBUSTNESS-FIX-001 | BENCHMARK / TEST |
| `9fec4ac` | 2026-06-04 | docs: zatwierdz offline benchmark RWS expansion stage6 | TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-APPROVAL-DOC-001 | DOCS |
| `2c1f2bf` | 2026-06-04 | feat: dodaj benchmark RWS expansion stage6 | TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001 | BENCHMARK / TEST |
| `beace78` | 2026-06-04 | docs: zatwierdz RWS expansion fixture | TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-EXPANSION-001 | DOCS |
| `b791943` | 2026-06-04 | docs: przygotuj paczke review rws expansion stage6 | - | DOCS |
| `5f5cd33` | 2026-06-04 | docs: przygotuj paczke review rws expansion stage6 | - | DOCS |
| `470d403` | 2026-06-04 | docs: wyczysc handoff report stage6 rws | - | DOCS |
| `7530fbb` | 2026-06-04 | fix: przygotuj handoff wizarda rws stage6 | TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001 | OTHER |
| `cc6d4df` | 2026-06-04 | fix: diagnozuj zajeta kamere w wizardzie stage6 | TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001 | OTHER |
| `9f41218` | 2026-06-04 | fix: skieruj wizard stage6 na ekspansje RWS | TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001 | OTHER |
| `e70d44f` | 2026-06-04 | feat: dodaj minimalny wizard ekspansji RWS stage6 | TASK-CV-STAGE-6-RWS-WIZARD-HANDOFF-FIX-001 | OTHER |
| `d32797b` | 2026-06-04 | docs: przygotuj rozszerzenie fixture real-camera stage6 | - | DOCS |
| `7944890` | 2026-06-04 | docs: zatwierdz offline quality gate stage6 | TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-APPROVAL-DOC-001 | DOCS |
| `17590c5` | 2026-06-04 | feat: dodaj benchmark quality gate real-camera stage6 | TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-BENCHMARK-001 | BENCHMARK |
| `8f76d62` | 2026-06-04 | docs: zaprojektuj quality gate real-camera stage6 | TASK-CV-STAGE-6-REAL-CAMERA-QUALITY-GATE-DESIGN-001 | DOCS |
| `9f64867` | 2026-06-04 | docs: potwierdz ground truth real-camera stage6 | TASK-CV-STAGE-6-REAL-CAMERA-GROUND-TRUTH-REVIEW-001 | DOCS |
| `677d9ae` | 2026-06-04 | feat: dodaj analize bledow real-camera stage6 | TASK-CV-STAGE-6-REAL-CAMERA-ERROR-ANALYSIS-001 | BENCHMARK |
| `1aded61` | 2026-06-04 | feat: dodaj real-camera benchmark identyfikacji stage6 | TASK-CV-STAGE-6-REAL-CAMERA-IDENTIFICATION-BENCHMARK-001 | BENCHMARK |
| `87c1bd5` | 2026-06-04 | docs: przygotuj paczke review stage6 real-camera | - | DOCS |
| `5afe763` | 2026-06-04 | docs: oznacz capture stage6 real-camera jako gotowy | - | DOCS |
| `fd51a49` | 2026-06-04 | fix: uzyj ustawien kamery backendu w wizardzie stage6 | - | OTHER |
| `6daa70d` | 2026-06-04 | feat: dodaj tryb aparatu do wizarda stage6 | - | OTHER |
| `3a64d99` | 2026-06-04 | fix: doprecyzuj diagnostyke capture wizard | - | OTHER |
| `3f60887` | 2026-06-04 | chore: dodaj launcher wizard stage6 | - | CONFIG |
| `1927efb` | 2026-06-04 | fix: wymagaj realnych id kart w wizardzie stage6 | - | OTHER |
| `5f784a6` | 2026-06-04 | feat: dodaj wizard capture stage6 real-camera | TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001 | OTHER |
| `bb0588e` | 2026-06-04 | docs: zapisz review phase a stage6 real-camera | - | DOCS |
| `db744e7` | 2026-06-04 | feat: dodaj offline tooling real-camera fixture stage6 | TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001 | BENCHMARK |
| `1dd00ab` | 2026-06-04 | docs: zaplanuj real-camera fixture stage6 | - | DOCS |
| `5d35eb5` | 2026-06-04 | docs: zaprojektuj real-camera fixture stage6 | - | DOCS |
| `694a531` | 2026-06-04 | docs: zatwierdz syntetyczna walidacje stage6 | TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001 | DOCS |
| `faefe6b` | 2026-06-04 | feat: dodaj syntetyczny benchmark walidacyjny stage6 | TASK-CV-OFFLINE-LAB-STAGE-6-SYNTHETIC-VALIDATION-BENCHMARK-001 | BENCHMARK |
| `501481e` | 2026-06-04 | docs: popraw rejestr planu walidacji stage6 | - | DOCS |
| `73672e7` | 2026-06-04 | docs: zaplanuj syntetyczny benchmark walidacyjny stage6 | - | DOCS |
| `c2efc30` | 2026-06-04 | docs: zaprojektuj walidacje identyfikacji stage6 | - | DOCS |
| `a20b7ec` | 2026-06-04 | docs: zatwierdz metode identyfikacji stage6 | - | DOCS |
| `2bcfff9` | 2026-06-04 | docs: przygotuj paczke manual review stage6 | - | DOCS |
| `8934f0c` | 2026-06-04 | feat: uruchom benchmark identyfikacji stage6 | TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001 | BENCHMARK |
| `c06c906` | 2026-06-04 | docs: popraw status preflight stage6 | - | DOCS |
| `b8b2389` | 2026-06-04 | data: potwierdz etykiety ground truth stage6 | TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001 | CONFIG |
| `3fa2163` | 2026-06-04 | data: dodaj deck profile i ground truth stage6 | TASK-CV-OFFLINE-LAB-STAGE-6-DECK-PROFILE-GROUNDTRUTH-001 | CONFIG |
| `b59ea9e` | 2026-06-04 | feat: dodaj preflight referencji stage6 | TASK-CV-OFFLINE-LAB-STAGE-6-REFERENCE-GROUNDTRUTH-PREFLIGHT-001 | BENCHMARK |
| `7237fb9` | 2026-06-04 | docs: przygotuj research stage6 card identification | TASK-CV-RESEARCH-STAGE-6-CARD-IDENTIFICATION-001 | DOCS |
| `ef8e1d0` | 2026-06-04 | docs: zatwierdz stage5 crop quality | - | DOCS |
| `9b4bd35` | 2026-06-04 | fix: dodaj powody ostrzezen stage5 | - | TEST |
| `0d77acd` | 2026-06-04 | docs: przygotuj paczke manual review stage5 | TASK-CV-OFFLINE-LAB-STAGE-5-MANUAL-REVIEW-PACK-001 | DOCS |
| `91a3e41` | 2026-06-04 | fix: popraw metryki marginesu stage5 | - | BENCHMARK |
| `62d2bc6` | 2026-06-04 | feat: uruchom benchmark stage5 crop quality | TASK-CV-OFFLINE-LAB-STAGE-5-CROP-QUALITY-VALIDATION-BENCHMARK-001 | BENCHMARK |
| `2b58bbc` | 2026-06-04 | docs: przygotuj research stage5 crop quality | TASK-CV-RESEARCH-STAGE-5-CROP-QUALITY-VALIDATION-001 | DOCS |
| `cbcf017` | 2026-06-04 | docs: zatwierdz stage4 crop pipeline | - | DOCS |
| `2b80ec5` | 2026-06-04 | docs: zapisz przygotowanie paczki review stage4 | - | DOCS |
| `3ed3016` | 2026-06-04 | fix: generuj placeholder review sheet stage4 | - | BENCHMARK |
| `e61b656` | 2026-06-04 | feat: uruchom benchmark stage4 crop deskew normalize | TASK-CV-OFFLINE-LAB-STAGE-4-CROP-DESKEW-NORMALIZE-BENCHMARK-001 | BENCHMARK |
| `729c13d` | 2026-06-03 | docs: przygotuj research stage4 crop deskew normalize | TASK-CV-RESEARCH-STAGE-4-CROP-DESKEW-NORMALIZE-001 | DOCS |
| `b114f56` | 2026-06-03 | docs: zatwierdz stage3 geometry method | - | DOCS |
| `8b12b4e` | 2026-06-03 | docs: zapisz przygotowanie paczki review stage3 | - | DOCS |
| `1fc5b1b` | 2026-06-03 | feat: uruchom benchmark stage3 card localization | TASK-CV-OFFLINE-LAB-STAGE-3-CARD-LOCALIZATION-BENCHMARK-001 | BENCHMARK |
| `809d435` | 2026-06-03 | docs: przygotuj research stage3 card localization | TASK-CV-RESEARCH-STAGE-3-CARD-LOCALIZATION-001 | DOCS |
| `15a2fb2` | 2026-06-03 | docs: zatwierdz stage2 region method | - | DOCS |
| `b1d4d7a` | 2026-06-03 | docs: zapisz przygotowanie paczki review stage2 | - | DOCS |
| `20e60e1` | 2026-06-03 | feat: uruchom benchmark stage2 region segmentation | TASK-CV-OFFLINE-LAB-STAGE-2-REGION-BENCHMARK-001 | BENCHMARK |
| `350ae4e` | 2026-06-03 | docs: przygotuj research stage2 region segmentation | TASK-CV-RESEARCH-STAGE-2-REGION-SEGMENTATION-001 | DOCS |
| `aaded3a` | 2026-06-03 | docs: zatwierdz stage1 diff method | - | DOCS |
| `79a4d5b` | 2026-06-03 | docs: zapisz przygotowanie paczki review stage1 | - | DOCS |
| `998fc15` | 2026-06-03 | fix: doprecyzuj metryki regionow stage1 diff | - | BENCHMARK |
| `c235d8b` | 2026-06-03 | feat: uruchom offline lab detekcji roznic | TASK-CV-OFFLINE-LAB-STAGE-1-DIFF-BENCHMARK-001 | BENCHMARK |
| `fd8b475` | 2026-06-03 | fix: zabezpiecz fixture przed nadpisaniem | - | TEST |
| `594f7c8` | 2026-06-03 | fix: oznacz obrazy fixture scenariuszem | - | TEST |
| `e5fd02a` | 2026-06-03 | feat: dodaj zapis fixture live smoke | - | TEST |
| `e972cbd` | 2026-06-03 | feat: dodaj diagnostyke jakosci cropow roi | - | RUNTIME / BENCHMARK |
| `cba883a` | 2026-06-03 | docs: zapisz smoke diagnostyki roi trzech kart | - | DOCS |
| `e19b866` | 2026-06-03 | docs: zapisz handoff po roi diagnostics passthrough | - | DOCS |
| `991ba87` | 2026-06-03 | fix: przepusc diagnostyke roi do pipeline metrics | - | RUNTIME |
| `09db040` | 2026-06-03 | feat: dodaj diagnostyke multi roi | - | RUNTIME |
| `35f0011` | 2026-06-03 | docs: zatwierdz red smoke trzech kart | - | DOCS |
| `98623d7` | 2026-06-03 | docs: zapisz red smoke trzech kart | - | DOCS |
| `f5b9dc8` | 2026-06-03 | docs: zapisz smoke jednej karty event-first | - | DOCS |
| `290051e` | 2026-06-03 | fix: ustaw referencje zdarzen po pustej macie | - | RUNTIME |
| `20f7a39` | 2026-06-03 | fix: rozdziel status pustej referencji od detektora | - | RUNTIME |
| `4c41784` | 2026-06-03 | fix: nie publikuj false positive podczas pustej maty | - | RUNTIME |
| `790e1f6` | 2026-06-03 | feat: pokaz powod odrzucenia snapshotu | - | RUNTIME |
| `36f8485` | 2026-06-03 | docs: zapisz next action po red live smoke | - | DOCS |
| `7b301f9` | 2026-06-03 | docs: zapisz supervisor review red live smoke | - | DOCS |
| `0a044c2` | 2026-06-03 | docs: zapisz red live smoke event-first | - | DOCS |
| `7a7e5cf` | 2026-06-02 | feat: wyjasnij regiony zmian w cv explain | TASK-STUDIO-CV-EXPLAIN-001 | RUNTIME / FRONTEND |
| `aa51d47` | 2026-06-02 | fix: zbieraj pusta referencje przy no-change | - | RUNTIME |
| `d24e178` | 2026-06-02 | feat: zapisz pusta mate jako referencje tla | - | RUNTIME |
| `99dc923` | 2026-06-02 | fix: zachowaj layout przy global shift i no-change | - | RUNTIME |
| `dba730a` | 2026-06-02 | feat: uzyj regionow zmian w snapshot-first | - | RUNTIME |
| `6f12d6b` | 2026-06-02 | feat: ogranicz analize snapshotu do regionow zmian | - | RUNTIME |
| `ccd7799` | 2026-06-02 | feat: dodaj detekcje zmian miedzy snapshotami | - | RUNTIME |
| `1f64e48` | 2026-06-02 | feat: ustabilizuj model pustej maty | - | RUNTIME |
| `833ff3c` | 2026-06-02 | docs: scal errate event-first z glownym planem | - | DOCS |
| `b5034c0` | 2026-06-02 | docs: dodaj raport erraty event-first planu | - | DOCS |
| `86cea78` | 2026-06-02 | docs: zapisz status erraty event-first planu | - | DOCS |
| `6fad915` | 2026-06-02 | docs: zapisz errate event-first planu | - | DOCS |
| `f58c31f` | 2026-06-02 | docs: popraw semantyke roi i walidacje empty reference | - | DOCS |
| `c8d0970` | 2026-06-02 | docs: doprecyzuj role autotuningu i event-first runtime | - | DOCS |
| `3cff13a` | 2026-06-02 | docs: zaplanuj event-first background diff | - | DOCS |
| `6177839` | 2026-06-02 | fix: wymus probki autotune po kliknieciu etapu | - | RUNTIME |
| `2eef823` | 2026-06-02 | fix: usun limit rozmiaru pip w studio | - | FRONTEND |
| `36f4421` | 2026-06-02 | fix: pokaz kontrolki widoku studio | - | FRONTEND |
| `b45408a` | 2026-06-02 | feat: dodaj wizard auto tune z logami sesji | - | FRONTEND |
| `14cea2a` | 2026-06-02 | feat: uporzadkuj panel studio jako akordeon | - | FRONTEND |
| `47c72e7` | 2026-06-02 | docs: zapisz kontynuacje weryfikacji live autotuningu | - | DOCS |
| `61731f6` | 2026-06-02 | fix: odrzucaj odblaski przed rozpoznawaniem kart | - | RUNTIME |
| `8509cfb` | 2026-06-02 | fix: popraw status aruco w cv explain | - | RUNTIME |
| `0ed5804` | 2026-06-02 | feat: podlacz probki autotuningu i diagnostyke rozpoznan | - | RUNTIME / FRONTEND |
| `41da41f` | 2026-06-02 | feat: dodaj regulacje rozmiaru pip w studio | - | FRONTEND |
| `ed2b5eb` | 2026-06-02 | feat: dodaj tryby widoku stol kamera pip w studio | - | FRONTEND |
| `8e85465` | 2026-06-02 | docs: zapisz automatyczna weryfikacje live autotuningu | - | DOCS |
| `351a602` | 2026-06-02 | docs: opisz live autotuning i runbook operatora | - | DOCS |
| `15cf71f` | 2026-06-02 | feat: zapisuj rekomendacje autotuningu jako profil | - | RUNTIME |
| `f7616e3` | 2026-06-02 | feat: dodaj panel auto tune w studio | - | FRONTEND |
| `096db9e` | 2026-06-02 | feat: podlacz backend live autotuningu | TASK-CV-AUTOTUNE-LIVE-001 | RUNTIME |
| `057e6aa` | 2026-06-02 | feat: dodaj protokol komend live autotuningu | TASK-CV-AUTOTUNE-LIVE-001 | RUNTIME |
| `ddf137c` | 2026-06-02 | docs: zapisz pelna weryfikacje live autotuningu | - | DOCS |
| `aec8e7b` | 2026-06-02 | docs: zapisz status live autotuningu | - | DOCS |
| `325e45c` | 2026-06-02 | feat: dodaj stan sesji live autotuningu | - | RUNTIME |
| `7acd1dd` | 2026-06-02 | feat: dodaj bezpieczne profile kandydackie autotuningu | - | RUNTIME |
| `83ddba6` | 2026-06-02 | feat: dodaj scoring live autotuningu | - | RUNTIME |
| `4492741` | 2026-06-02 | feat: wyjasnij roznice kandydatow i rozpoznan | - | RUNTIME / FRONTEND |
| `51a0b1f` | 2026-06-02 | docs: zatwierdz fundament offline autotuningu | - | DOCS |

### Files Changed

Branch modyfikuje łącznie **243 pliki** (z czego wiele to pliki testowe i historyczne raporty w `.ai/tasks/`).

Podsumowanie modyfikacji według warstw systemu:
- **Runtime Backend (`app_cv/`):** 17 plików produkcyjnych (logika serwera WebSocket, orkiestracja autotuningu, scoringu, detekcja zmian w tle, explainability).
- **Runtime Frontend (`app_ar/`):** 2 pliki produkcyjne (`studioConsole.js`, `studio.css`).
- **Narzędzia laboratoryjne / skrypty (`tools/cv_detection_lab/`, baty):** 24 pliki narzędziowe (nie wpływają bezpośrednio na runtime).
- **Testy jednostkowe (`app_cv/tests/`):** 34 pliki testów jednostkowych (zapewniają pokrycie nowej i zmodyfikowanej logiki).
- **Dokumentacja i metadane zadań (`.ai/tasks/`, `docs/`):** 166 plików (raporty zadań, implementacja planów wdrożenia).

### Tasks Found

Na branchu zidentyfikowano realizację **32 powiązanych zadań deweloperskich**:
1. `TASK-STUDIO-CV-EXPLAIN-002` (Doprecyzowanie komunikatów).
2. `TASK-CV-AUTOTUNE-LIVE-001` (Live auto-tuning w locie).
3. `TASK-CV-RESEARCH-STAGE-1-DIFF-DETECTION-001` do `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001` (16 zadań tworzących cały potok deweloperski Offline Lab).
4. `TASK-CV-STAGE-6-REAL-CAMERA-FIXTURE-REVERSED-WRONG-DECK-001` do `TASK-CV-STAGE-6-RWS-RUNTIME-POLICY-DESIGN-APPROVAL-DOC-001` (14 zadań związanych z testowaniem na fizycznych klatkach, detekcją odblasków i ostatecznym benchmarkiem RWS).

---

## Task Review

W poniższej sekcji opisano kluczowe logiczne bloki zadań wdrożone na branchu.

### 1. Live Auto-Tuning & Diagnostic UI (TASK-CV-AUTOTUNE-LIVE-001)
* **Status:** `DONE` (Ukończono integrację)
* **Risk:** MEDIUM (Wpływa na główną pętlę i WebSocket w `main.py`)
* **Tests:** backend tests (PASS: `test_autotune_*.py`), manual tests (zweryfikowane w Studio Console UI).
* **Scope:** `app_cv/main.py`, `app_cv/tarotvision/autotune_*.py`, `app_ar/src/studio/studioConsole.js`, `app_ar/studio.css`.
* **Opis:** Umożliwia operatorowi automatyczne przetestowanie konfiguracji CV dla 1, 3 kart lub pustej maty bezpośrednio z poziomu UI i zapisanie zoptymalizowanego profilu detekcji.

### 2. Event-First Change Detection (TASK-CV-EVENT-FIRST-PLAN-001 / Errata)
* **Status:** `DONE` (Ukończono wdrożenie w snapshot-first)
* **Risk:** MEDIUM (Modyfikuje moment wyzwalania i logikę snapshot-first)
* **Tests:** backend tests (PASS: `test_change_detection.py`), manual tests (potwierdzono w smoke testach).
* **Scope:** `app_cv/tarotvision/change_detection.py`, `app_cv/tarotvision/pipelines/snapshot_first.py`.
* **Opis:** System wykrywa różnice klatka do klatki w regionach kart. Pozwala to na uniknięcie ciągłego sprawdzania całego obrazu i publikowanie overlay AR bez migotania.

### 3. Offline Lab Stages 1-6 (Zestaw 16 zadań laboratoryjnych)
* **Status:** `APPROVED` (Zatwierdzony potok)
* **Risk:** LOW (Zmiany dotyczą wyłącznie skryptów testowych i deweloperskich w `tools/`)
* **Tests:** backend tests (PASS: `test_cv_detection_lab_stage*.py`), manual benchmarks (wyniki zapisane w raportach).
* **Scope:** `tools/cv_detection_lab/*`.
* **Opis:** Zbudowano kompletny potok deweloperski: od prostej detekcji różnic (Stage 1), przez segmentację konturów (Stage 2), lokalizację geometrii kart (Stage 3), korekcję perspektywy i normalizację (Stage 4), ocenę jakości ROI (Stage 5), po dopasowanie cech ORB i walidację (Stage 6).

### 4. Real Camera Verification & Glare Quality Gate (Zestaw 7 zadań)
* **Status:** `APPROVED` (Zweryfikowano offline)
* **Risk:** LOW (Kod produkcyjny nie został zmieniony; bramka jakości działa jako offline benchmark)
* **Tests:** backend tests (PASS: `test_cv_detection_lab_stage6_real_camera_quality_gate.py`), manual tests (uruchomiony wizard przechwytywania klatek z kamery fizycznej).
* **Scope:** `tools/cv_detection_lab/stage6_real_camera_*.py`.
* **Opis:** Opracowano i zaimplementowano detektor odblasków (glare detection) oraz benchmark jakościowy, który ze 100% dokładnością blokuje prześwietlone klatki i kwalifikuje klatki bezodblaskowe.

### 5. RWS Expansion Benchmark & Runtime Policy (Zestaw 6 zadań)
* **Status:** `APPROVED` / `DONE` (Projekt i benchmark gotowe)
* **Risk:** LOW (Zmiany w benchmarku deweloperskim i dokumentacji)
* **Tests:** backend tests (PASS: `test_cv_detection_lab_stage6_rws_expansion_benchmark.py`), manual tests (potwierdzony odczyt 8 fizycznych próbek).
* **Scope:** `tools/cv_detection_lab/stage6_rws_expansion_benchmark.py`, `docs/superpowers/plans/2026-06-04-stage-6-rws-runtime-policy-design.md`.
* **Opis:** Uruchomiono benchmark rozpoznawania dla 8 fizycznych próbek talii RWS (50% ogólnej skuteczności z uwagi na odblaski, 100% skuteczności po przejściu bramki jakościowej). Zaprojektowano model bezpiecznego runtime (RETRY_CAPTURE, MANUAL_REVIEW itp.) chroniący OBS przed migotaniem obrazu.

---

## Runtime Impact

Branch wprowadza istotne modyfikacje w kodzie uruchomieniowym aplikacji:

1. **`app_cv/main.py`:**
   - Dodano obsługę nowych komend WebSocket (`studio_live_autotune`, `studio_get_autotune_status`, `studio_set_pip_mode`).
   - Wdrożono przesyłanie obrazów diagnostycznych i próbek ROI do frontendu.
   - *Ryzyko regresji:* Niskie/Średnie. Nowe komendy są izolowane w parserze i nie blokują pętli głównej CV.
2. **`app_cv/tarotvision/pipelines/snapshot_first.py`:**
   - Zintegrowano Change Detector i model pustej maty jako bramki stabilności.
   - *Ryzyko regresji:* Średnie. Zmiana wpływa na detekcję obecności kart i moment wykonywania snapshotu. Wymaga weryfikacji z fizyczną kamerą w trybie ciągłym.
3. **`app_ar/src/studio/studioConsole.js`:**
   - Rozbudowano interfejs o panel strojenia autotuning, sterowanie PIP oraz akordeon do zarządzania widgetami.
   - *Ryzyko regresji:* Niskie. Zmiana dotyczy wyłącznie konsoli operatora (`?studio=1`), publiczny overlay AR dla widzów (`/`) pozostaje nienaruszony.

---

## Architecture Impact

Ocena zgodności z założeniami projektowymi:
* **Roadmapa Stage 6:** Zgodna. Benchmarki i weryfikacja realnych próbek to bezpośredni cel Stage 6.
* **Snapshot-First:** Zachowany. Cały potok rozwija i optymalizuje ten produkcyjny pipeline.
* **Legacy State-First:** Brak powrotu. Stary potok nie został przywrócony.
* **Rozszerzenie WebSocket:** Uzasadnione. Komunikacja służy wyłącznie wymianie parametrów strojenia i statusów diagnostycznych operatora.
* **Rozrost `main.py`:** Występuje (dodano 235 linii kodu). Handler komend WebSocket i logika diagnostyczna powinny w przyszłości zostać zrefaktoryzowane do osobnego modułu (np. `tarotvision/ws_handlers.py`), by odciążyć `main.py`.

---

## Merge Readiness

### Safe To Merge

* Wszystkie **433 testy jednostkowe przechodzą pomyślnie**.
* Narzędzia offline labu (`tools/cv_detection_lab/`) są całkowicie odseparowane od kodu produkcyjnego i są w 100% bezpieczne do scalenia.
* Dokumentacja w `.ai/tasks/` i `docs/` jest kompletna i poprawna.

### Not Safe To Merge

* Integracja Live Auto-Tuning i Change Detection w kodzie produkcyjnym (`main.py`, `snapshot_first.py`) jest bardzo obszerna i nie przeszła jeszcze ostatecznego, ciągłego testu dymnego z fizyczną kamerą (Live Smoke Test) na stanowisku operatorskim.
* Monolityczna wielkość PR (243 pliki) utrudnia ewentualny rollback w przypadku problemów z fizycznym hardwarem (focus/glare kamery).

---

## Supervisor Recommendations

W celu zachowania maksymalnego bezpieczeństwa systemu przed wdrożeniem produkcyjnym, zaleca się:

1. **Podział brancha na dwa etapy (Split):**
   - **PR 1 (Offline Lab & Benchmarks):** Scalenie wszystkich narzędzi deweloperskich (`tools/cv_detection_lab/`), testów jednostkowych benchmarków oraz dokumentacji zadań. Zmiany te są w 100% bezpieczne i nie wpływają na runtime.
   - **PR 2 (Runtime Production Changes):** Osobny proces review i wdrożenia dla Live Auto-tuning, WebSocket handlerów i Change Detection (`main.py`, `snapshot_first.py`, `studioConsole.js`).
2. **Refaktoryzacja WebSocketów w przyszłości:** Wydzielenie obsługi komend autotuningu z `main.py` do dedykowanego kontrolera.
3. **Live Smoke Test:** Przeprowadzenie przez operatora 10-minutowego testu stabilności z podpiętą kamerą fizyczną na branchu roboczym przed ostatecznym scaleniem kodu produkcyjnego do `master`.

---

## Final Recommendation

```text
SPLIT_BRANCH_FIRST
```

**Uzasadnienie:** Branch jest zbyt duży i łączy kod narzędziowy offline z krytycznymi zmianami produkcyjnymi w pętli CV. Najbezpieczniejszą ścieżką jest scalenie offline labu i benchmarków w pierwszej kolejności, a następnie przeprowadzenie weryfikacji na fizycznej kamerze dla zmian runtime przed ich wdrożeniem do mastera.
