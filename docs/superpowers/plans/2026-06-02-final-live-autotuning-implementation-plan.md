# Final Live Autotuning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wdrozyc bezpieczny live autotuning TarotVision, ktory po nowych funkcjach rozpoznawania optymalizuje caly wynik pipeline snapshot-first, a nie tylko geometrie prostokata karty.

**Architecture:** Autotuning ma dzialac jako kontrolowana rekomendacja operatorska: zbiera probki z kamery, testuje kandydackie profile na snapshotach, punktuje je po geometrii, rozpoznaniu i stabilnosci, pokazuje rekomendacje w Studio, a dopiero po decyzji operatora wykonuje apply/rollback i zapis profilu. Nie wolno podlaczac autotunera jako automatycznego, cichego nadpisywania dzialajacych ustawien.

**Tech Stack:** Python stdlib `unittest`, OpenCV, NumPy, existing `tarotvision.auto_tuner`, `snapshot_autotune`, `runtime_config`, `tuning_protocol`, WebSocket status payload, Vite/Three.js/DOM/CSS Studio Console.

---

## Status ogolny

Projekt ma juz fundament pod autotuning:

- `app_cv/tarotvision/auto_tuner.py` potrafi offline dobrac parametry detekcji prostokatow kart.
- `app_cv/tarotvision/snapshot_autotune.py` dodaje recognition-aware scoring, ale tylko dla offline evaluation.
- `app_cv/tarotvision/runtime_config.py` ma walidowane parametry i `RuntimeConfigSession` z pending changes, commit stable i rollback.
- `app_cv/tarotvision/tuning_protocol.py` ma komendy `calibration_start`, `calibration_cancel`, `tuning_update`, `tuning_rollback`, `profile_save`, `profile_apply`.
- `app_cv/tarotvision/operator_explainability.py` daje kanal do jasnego komunikowania operatorowi, co system widzi i co nalezy zrobic.
- Live smoke po `TASK-STUDIO-CV-EXPLAIN-001` pokazal realny przypadek: 3 karty widoczne, 2 zaakceptowane rozpoznania. To jest dokladnie typ sygnalu, ktory autotuning musi umiec diagnozowac.

## Co zostalo zrobione

- `TASK-CV-RECT-001`: parametryzacja detekcji prostokatow kart pod autotuning, status `DONE`, oczekuje na review.
- `TASK-CV-AUTOTUNE-001`: offline single-frame autotune prototype, status `DONE`, oczekuje na review.
- `TASK-CV-SNAPSHOT-007`: recognition-aware snapshot autotuning, status `APPROVED`, ale w raporcie zapisano jasno: offline-only, bez live pipeline.
- `TASK-STUDIO-CV-EXPLAIN-001`: panel `CV Explain` zatwierdzony i scalony do `master`.
- `TASK-STUDIO-CV-EXPLAIN-002`: follow-up zaplanowany po live smoke, aby wyjasnic roznice miedzy kandydatami a zaakceptowanymi kartami.

## Session Status (2026-06-02 Codex Post-Task 10)

Po ponownym przeglądzie logiki rozpoznawania kart wykryto i domknięto dwie luki, które ograniczały sensowność live autotuningu:

- `AutotuneSession.add_sample()` był przygotowany, ale nie był podłączony do produkcyjnej ścieżki snapshot-first.
- `SnapshotAnalyzer` liczył odrzucone rozpoznania, ale nie publikował per-candidate przyczyn odrzucenia, rankingu top-matchy ani agregowanego `recognition_score`.

W tej sesji Codex dodał callback próbek autotuningu w `SnapshotFirstPipeline`, podłączył go w `main.py`, rozszerzył `recognize_card_crop_with_debug()` o ranking top-matchy i uzupełnił diagnostykę kandydatów w `SnapshotAnalyzer`. Manualny live smoke z fizyczną kamerą nadal pozostaje wymaganym krokiem przed oznaczeniem taska jako `DONE`.

## Session Status (2026-06-02 Codex glare false-positive hardening)

Po obserwacji live z jedną kartą i odblaskiem na macie wykryto trzecią lukę: detektor geometrii mógł zgłosić jasną plamę jako kandydat, a rozpoznawanie ORB nie miało wcześniejszej bramki „none-of-the-above”. Codex dodał `card_candidate_validation.py`, który przed rozpoznawaniem odrzuca cropy bez tekstury, krawędzi i śladów granicy karty. `SnapshotAnalyzer` publikuje `candidate_validation_rejections`, pipeline zapisuje tę metrykę do próbek autotuningu, a `CV Explain` wskazuje operatorowi odblask/tło zamiast sugerować problem z właściwą kartą.

Weryfikacja automatyczna: 267 testów backend PASS oraz `npm --prefix app_ar run build` PASS. Manualny live smoke z fizyczną kamerą nadal pozostaje wymagany przed zamknięciem taska.

## Session Status (2026-06-02 Codex Studio sidebar accordion)

Po uwadze operatorskiej o pomieszaniu aktywnych talii z diagnostyką Codex uporządkował prawy panel Studio. `Auto Tune` jest teraz osobną rozwijaną sekcją, `Aktywne Talie` zawiera tylko wybór talii, a pozostałe grupy bocznego panelu działają jako akordeony z lokalnym zapamiętywaniem zwinięcia. Weryfikacja: 268 testów backend PASS, `npm --prefix app_ar run build` PASS oraz Browser QA lokalnego Studio PASS bez błędów konsoli. Manualny live smoke z fizyczną kamerą nadal pozostaje wymagany przed oznaczeniem taska jako `DONE`.

## Session Status (2026-06-02 Codex Auto Tune wizard MVP)

Codex wdrożył minimalny workflow operatorski Auto Tune zgodny z intencją Michała: scenariusze `Pusta mata`, `1 karta` i `3 karty` zwracają jawny wynik etapu `COLLECTING`/`PASS`/`FAIL`, a `Skalibruj` jest osobną komendą uruchamiającą rekomendację po komplecie próbek. Dodano trwały logger sesji do `logs/autotune_sessions/autotune_*.json`, przyciski `Skalibruj` i `Save Profile` w Studio oraz automatyczną nazwę zapisywanego profilu `studio_live_YYYYMMDD_HHMMSS`. Weryfikacja automatyczna: 275 testów backend PASS, frontend build PASS, Browser QA PASS. Manualny live smoke z fizyczną kamerą nadal pozostaje wymagany przed oznaczeniem taska jako `DONE`.

## Session Status (2026-06-02 Codex preview controls visibility)

Po uwadze Michała o niewidocznych ustawieniach obrazu Codex otworzył domyślnie sekcję `Widok podglądu`, ignoruje wcześniejszy zapis localStorage zwijający tę sekcję i zmienił etykietę trybu `table` na `Wirtualny stół`. Weryfikacja: statyczne testy UI PASS, frontend build PASS, Browser QA PASS bez błędów konsoli.

## Decyzja strategiczna

Po nowych funkcjach rozpoznawania nie wolno implementowac autotuningu jako "znajdz najlepsze Canny/min_area". To byloby lokalne minimum: system moglby idealnie wykrywac prostokaty, ale nadal odrzucac karty przez ORB, homografie, threshold lub konflikt aktywnych talii.

Docelowy autotuning musi optymalizowac funkcje celu:

```text
score = geometry_score
      + recognition_score
      + stability_score
      + accepted_cards_score
      - false_positive_penalty
      - latency_penalty
      - operator_risk_penalty
```

Minimalna wersja produkcyjna nie musi optymalizowac wszystkich parametrow naraz. Ma optymalizowac mala, bezpieczna przestrzen parametrow i jasno powiedziec operatorowi, czy rekomendacja jest wiarygodna.

---

## Stan docelowy

Operator w Studio uruchamia `Auto Tune`.

System:

1. Prosi operatora o scenariusz: pusta mata, 1 karta, 3 karty.
2. Zbiera krotka serie stabilnych snapshotow z kamery.
3. Testuje kandydackie profile offline na zebranych snapshotach.
4. Punktuje kazdy profil na podstawie:
   - liczby kandydatow kart,
   - liczby zaakceptowanych rozpoznan,
   - recognition score / match count / inlier ratio,
   - stabilnosci miedzy snapshotami,
   - czasu przetwarzania,
   - ryzyka false positives na pustej macie.
5. Pokazuje rekomendacje w Studio: aktualny profil vs rekomendowany profil.
6. Operator wybiera `Apply`, `Rollback` albo `Save Profile`.
7. Wynik trafia do `logs/calibration_profiles/` i do raportu diagnostycznego.

---

## Zakres finalnego wdrozenia

### W zakresie

- Live collection snapshotow kalibracyjnych.
- Nowy model danych dla sesji autotuningu.
- Multi-snapshot scoring kandydackich profili.
- Integracja z `RuntimeConfigSession`.
- Status i rekomendacja w payloadzie `operator.calibration`.
- UI Studio: start/cancel/apply/rollback/save.
- Testy jednostkowe i statyczne.
- Dokumentacja operatora.

### Poza zakresem tej iteracji

- Automatyczna zmiana ustawien kamery bez potwierdzenia operatora.
- Trenowanie modelu ML.
- Zmiana algorytmu ORB/FLANN/RANSAC.
- Optymalizacja wszystkich mozliwych parametrow naraz.
- Pełna optymalizacja ekspozycji/focusu, jesli kamera nie potwierdza stabilnego readbacku.

---

## File Structure

- Create: `app_cv/tarotvision/autotune_session.py`
  Orkiestracja sesji live autotuningu: scenariusz, probki, kandydackie profile, rekomendacja.

- Create: `app_cv/tarotvision/autotune_scoring.py`
  Czyste funkcje scoringu multi-snapshot, niezalezne od WebSocket i kamery.

- Create: `app_cv/tarotvision/autotune_profiles.py`
  Definicje kandydackich profili i ograniczone przestrzenie wyszukiwania dla etapow MVP.

- Modify: `app_cv/tarotvision/auto_tuner.py`
  Zachowac dotychczasowe API, dodac helper przyjmujacy jawne parametry/profil i zwracajacy porownywalne telemetry.

- Modify: `app_cv/tarotvision/snapshot_analyzer.py`
  Upewnic sie, ze wynik analizy snapshotu zawiera debug potrzebny scoringowi: candidates, accepted, rejected, recognition stats.

- Modify: `app_cv/tarotvision/operator_explainability.py`
  Dodac komunikaty o luce kandydaci vs zaakceptowane i status sesji autotuningu.

- Modify: `app_cv/tarotvision/tuning_protocol.py`
  Dodac bezpieczne, jawne typy komend: `autotune_start`, `autotune_apply`, `autotune_save`, `autotune_cancel`.

- Modify: `app_cv/main.py`
  Orkiestracja komend, zbieranie snapshotow, publikacja statusu, apply/rollback przez `RuntimeConfigSession`.

- Modify: `app_ar/src/studio/studioConsole.js`
  UI Auto Tune w Studio, bez wplywu na zwykly overlay.

- Modify: `app_ar/studio.css`
  Style panelu Auto Tune zgodne ze Studio.

- Create: `app_cv/tests/test_autotune_scoring.py`
  Testy funkcji scoringu.

- Create: `app_cv/tests/test_autotune_session.py`
  Testy stanu sesji i rekomendacji.

- Modify: `app_cv/tests/test_tuning_protocol.py`
  Testy nowych komend WebSocket.

- Modify: `app_cv/tests/test_operator_explainability.py`
  Testy komunikatow kandydaci vs zaakceptowane i autotune status.

- Modify: `app_cv/tests/test_main_static_audit.py`
  Statyczny kontrakt, ze `main.py` publikuje status autotuningu i nie aplikuje rekomendacji bez komendy operatora.

- Modify: `app_cv/tests/test_camera_controls_static.py`
  Statyczny test obecnosci UI Auto Tune w Studio.

- Modify: `.ai/TASKS_INDEX.md`
  Dodac taski opisane nizej.

---

## Task 0: Review i domkniecie fundamentu offline

**Files:**
- Read: `.ai/tasks/TASK-CV-RECT-001/*`
- Read: `.ai/tasks/TASK-CV-AUTOTUNE-001/*`
- Read: `.ai/tasks/TASK-CV-SNAPSHOT-007/*`
- Modify: `.ai/TASKS_INDEX.md`

- [ ] **Step 1: Zweryfikuj status taskow offline**

Run:

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_auto_tuner app_cv.tests.test_snapshot_autotune app_cv.tests.test_runtime_config -v"
```

Expected: PASS.

- [ ] **Step 2: Jezeli testy sa zielone, zaktualizuj status review**

W `.ai/TASKS_INDEX.md` ustaw:

```markdown
| **TASK-CV-RECT-001** | `APPROVED` | `master` | Gemini | Parametryzacja detekcji prostokątów kart pod autotuning | 2026-06-02 | Approved as autotuning foundation |
| **TASK-CV-AUTOTUNE-001** | `APPROVED` | `master` | Gemini | Prototyp offline autotunera detekcji prostokąta karty | 2026-06-02 | Approved as offline foundation |
```

- [ ] **Step 3: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add .ai/TASKS_INDEX.md
git -C E:\Antigravity\Projekty\TAROT commit -m "docs: zatwierdz fundament offline autotuningu"
```

---

## Task 1: Candidate vs Accepted diagnostics

**Files:**
- Modify: `app_cv/tarotvision/operator_explainability.py`
- Modify: `app_cv/tests/test_operator_explainability.py`
- Modify: `app_ar/src/studio/studioConsole.js`
- Modify: `app_cv/tests/test_camera_controls_static.py`
- Update: `.ai/tasks/TASK-STUDIO-CV-EXPLAIN-002/*`

- [ ] **Step 1: Write failing backend test**

Dodaj w `app_cv/tests/test_operator_explainability.py`:

```python
    def test_candidate_gap_explains_rejected_cards(self):
        explain = build_cv_explainability(
            cards=[{"id": "gilded_01"}, {"id": "gilded_02"}],
            metrics={"snapshot_quads_found": 3},
            runtime={"aruco_calibrated": True, "aruco_markers": 4, "candidate_count": 3},
            layout={"state": "holding_last_good"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        recognition_step = next(step for step in explain["steps"] if step["id"] == "recognition")
        self.assertEqual(recognition_step["state"], "warn")
        self.assertIn("2/3", recognition_step["value"])
        self.assertIn("1", recognition_step["message"])
        self.assertEqual(explain["severity"], "warn")
        self.assertIn("jedna karta", explain["next_action"].lower())
```

- [ ] **Step 2: Run failing test**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_operator_explainability -v"
```

Expected: FAIL, because current recognition step only reports accepted card count.

- [ ] **Step 3: Implement minimal backend logic**

In `operator_explainability.py`, compute:

```python
accepted_count = len(cards)
rejected_count = max(0, int(candidate_count) - accepted_count)
has_candidate_gap = candidate_count > accepted_count and accepted_count > 0
```

Use recognition step:

```python
_step(
    "recognition",
    "Rozpoznanie",
    "warn" if has_candidate_gap else ("ok" if cards else "wait"),
    f"{accepted_count}/{candidate_count}" if candidate_count else str(accepted_count),
    (
        f"Zaakceptowano {accepted_count}, odrzucono {rejected_count}"
        if has_candidate_gap
        else ("Karty zaakceptowane" if cards else "Czeka na rozpoznanie")
    ),
)
```

Add decision branch before generic `elif cards`:

```python
    elif has_candidate_gap:
        severity = "warn"
        next_action = "Jedna karta wymaga poprawy rozpoznania: popraw swiatlo, kontrast albo odsun karte od innych."
```

- [ ] **Step 4: Run tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_operator_explainability app_cv.tests.test_camera_controls_static -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\tarotvision\operator_explainability.py app_cv\tests\test_operator_explainability.py .ai\tasks\TASK-STUDIO-CV-EXPLAIN-002
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: wyjasnij roznice kandydatow i rozpoznan"
```

---

## Task 2: Autotune scoring model

**Files:**
- Create: `app_cv/tarotvision/autotune_scoring.py`
- Create: `app_cv/tests/test_autotune_scoring.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_autotune_scoring.py`:

```python
import unittest

from tarotvision.autotune_scoring import score_autotune_profile, choose_best_profile_result


class AutotuneScoringTest(unittest.TestCase):
    def test_scores_recognition_over_geometry_only(self):
        geometry_only = {
            "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.001},
            "samples": [
                {"geometry_score": 0.95, "candidate_count": 3, "accepted_count": 0, "false_positive_count": 0, "matching_ms": 40.0}
            ],
        }
        recognized = {
            "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.002},
            "samples": [
                {"geometry_score": 0.70, "candidate_count": 3, "accepted_count": 2, "recognition_score": 0.80, "false_positive_count": 0, "matching_ms": 55.0}
            ],
        }

        self.assertGreater(score_autotune_profile(recognized)["score"], score_autotune_profile(geometry_only)["score"])

    def test_penalizes_false_positive_on_empty_mat(self):
        result = score_autotune_profile({
            "profile": {"CARD_DETECT_MIN_AREA_RATIO": 0.0001},
            "samples": [
                {"scenario": "empty", "geometry_score": 0.8, "candidate_count": 2, "accepted_count": 1, "recognition_score": 0.6, "false_positive_count": 1, "matching_ms": 40.0}
            ],
        })

        self.assertLess(result["score"], 0.0)
        self.assertIn("false_positive", result["reasons"][0])

    def test_choose_best_profile_result(self):
        low = {"profile": {"name": "low"}, "samples": [{"geometry_score": 0.2, "accepted_count": 0}]}
        high = {"profile": {"name": "high"}, "samples": [{"geometry_score": 0.7, "accepted_count": 2, "recognition_score": 0.8}]}

        best = choose_best_profile_result([low, high])

        self.assertEqual(best["profile"]["name"], "high")
        self.assertGreater(best["score"], 0.0)
```

- [ ] **Step 2: Run failing tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_autotune_scoring -v"
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement scoring**

Create `app_cv/tarotvision/autotune_scoring.py`:

```python
def _sample_score(sample):
    geometry = float(sample.get("geometry_score", 0.0))
    recognition = float(sample.get("recognition_score", 0.0))
    candidate_count = int(sample.get("candidate_count", 0))
    accepted_count = int(sample.get("accepted_count", 0))
    false_positive_count = int(sample.get("false_positive_count", 0))
    matching_ms = float(sample.get("matching_ms", 0.0))

    accepted_ratio = accepted_count / candidate_count if candidate_count > 0 else 0.0
    latency_penalty = max(0.0, matching_ms - 120.0) / 120.0

    score = (
        geometry * 0.35
        + recognition * 0.85
        + accepted_ratio * 0.70
        + accepted_count * 0.10
        - false_positive_count * 2.0
        - latency_penalty * 0.35
    )
    return score


def score_autotune_profile(profile_result):
    samples = profile_result.get("samples") or []
    if not samples:
        return {
            "profile": profile_result.get("profile", {}),
            "score": -999.0,
            "confidence": "LOW",
            "reasons": ["no_samples"],
        }

    sample_scores = [_sample_score(sample) for sample in samples]
    average = sum(sample_scores) / len(sample_scores)
    false_positive_total = sum(int(sample.get("false_positive_count", 0)) for sample in samples)
    accepted_total = sum(int(sample.get("accepted_count", 0)) for sample in samples)

    reasons = []
    if false_positive_total:
        reasons.append("false_positive_penalty")
    if accepted_total:
        reasons.append("accepted_cards_reward")
    if not reasons:
        reasons.append("geometry_only")

    if average >= 1.2 and accepted_total > 0 and false_positive_total == 0:
        confidence = "HIGH"
    elif average >= 0.5:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "profile": profile_result.get("profile", {}),
        "score": average,
        "confidence": confidence,
        "reasons": reasons,
        "sample_count": len(samples),
        "accepted_total": accepted_total,
        "false_positive_total": false_positive_total,
    }


def choose_best_profile_result(profile_results):
    scored = [score_autotune_profile(result) for result in profile_results]
    if not scored:
        return None
    return max(scored, key=lambda result: result["score"])
```

- [ ] **Step 4: Run tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_autotune_scoring -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\tarotvision\autotune_scoring.py app_cv\tests\test_autotune_scoring.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj scoring live autotuningu"
```

---

## Task 3: Candidate profile space

**Files:**
- Create: `app_cv/tarotvision/autotune_profiles.py`
- Create: `app_cv/tests/test_autotune_profiles.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_autotune_profiles.py`:

```python
import unittest

from tarotvision.autotune_profiles import generate_candidate_profiles


class AutotuneProfilesTest(unittest.TestCase):
    def test_generates_small_safe_profile_set(self):
        profiles = generate_candidate_profiles()

        self.assertGreaterEqual(len(profiles), 5)
        self.assertLessEqual(len(profiles), 30)
        for profile in profiles:
            self.assertIn("CARD_DETECT_MIN_AREA_RATIO", profile)
            self.assertIn("CARD_DETECT_MAX_CANDIDATES", profile)
            self.assertIn("WORKSPACE_INFLATE_PERCENT", profile)

    def test_profiles_do_not_change_orb_thresholds_in_mvp(self):
        profiles = generate_candidate_profiles()

        forbidden = {"MIN_MATCH_COUNT", "RATIO_THRESH", "MIN_INLIER_RATIO"}
        for profile in profiles:
            self.assertFalse(forbidden.intersection(profile.keys()))
```

- [ ] **Step 2: Run failing tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_autotune_profiles -v"
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement profile generator**

Create `app_cv/tarotvision/autotune_profiles.py`:

```python
def generate_candidate_profiles():
    profiles = []
    min_area_values = [0.0005, 0.001, 0.002, 0.005]
    max_candidate_values = [6.0, 10.0, 16.0]
    inflate_values = [0.0, 6.0]

    for min_area in min_area_values:
        for max_candidates in max_candidate_values:
            for inflate in inflate_values:
                profiles.append({
                    "CARD_DETECT_MIN_AREA_RATIO": min_area,
                    "CARD_DETECT_MAX_CANDIDATES": max_candidates,
                    "WORKSPACE_INFLATE_PERCENT": inflate,
                })

    return profiles
```

- [ ] **Step 4: Run tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_autotune_profiles -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\tarotvision\autotune_profiles.py app_cv\tests\test_autotune_profiles.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj bezpieczne profile kandydackie autotuningu"
```

---

## Task 4: Live autotune session state

**Files:**
- Create: `app_cv/tarotvision/autotune_session.py`
- Create: `app_cv/tests/test_autotune_session.py`

- [ ] **Step 1: Write failing tests**

Create `app_cv/tests/test_autotune_session.py`:

```python
import unittest

from tarotvision.autotune_session import AutotuneSession


class AutotuneSessionTest(unittest.TestCase):
    def test_collects_required_scenarios_before_ready(self):
        session = AutotuneSession(required_scenarios=("empty", "one_card", "three_cards"), samples_per_scenario=1)

        self.assertFalse(session.ready_to_score())
        session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})
        session.add_sample("one_card", {"candidate_count": 1, "accepted_count": 1})
        session.add_sample("three_cards", {"candidate_count": 3, "accepted_count": 2})

        self.assertTrue(session.ready_to_score())

    def test_rejects_unknown_scenario(self):
        session = AutotuneSession(required_scenarios=("empty",))

        with self.assertRaises(ValueError):
            session.add_sample("six_cards", {})

    def test_status_payload_is_operator_readable(self):
        session = AutotuneSession(required_scenarios=("empty", "one_card"), samples_per_scenario=2)
        session.add_sample("empty", {"candidate_count": 0, "accepted_count": 0})

        status = session.status()

        self.assertEqual(status["state"], "collecting")
        self.assertEqual(status["progress"]["empty"], "1/2")
        self.assertEqual(status["progress"]["one_card"], "0/2")
```

- [ ] **Step 2: Run failing tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_autotune_session -v"
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement session object**

Create `app_cv/tarotvision/autotune_session.py`:

```python
class AutotuneSession:
    def __init__(self, required_scenarios=("empty", "one_card", "three_cards"), samples_per_scenario=3):
        self.required_scenarios = tuple(required_scenarios)
        self.samples_per_scenario = int(samples_per_scenario)
        self.samples = {scenario: [] for scenario in self.required_scenarios}
        self.state = "collecting"
        self.recommendation = None

    def add_sample(self, scenario, sample):
        if scenario not in self.samples:
            raise ValueError(f"Unknown autotune scenario: {scenario}")
        if len(self.samples[scenario]) < self.samples_per_scenario:
            self.samples[scenario].append(dict(sample))
        if self.ready_to_score():
            self.state = "ready_to_score"

    def ready_to_score(self):
        return all(len(self.samples[scenario]) >= self.samples_per_scenario for scenario in self.required_scenarios)

    def all_samples(self):
        result = []
        for scenario, samples in self.samples.items():
            for sample in samples:
                copy = dict(sample)
                copy["scenario"] = scenario
                result.append(copy)
        return result

    def set_recommendation(self, recommendation):
        self.recommendation = recommendation
        self.state = "recommendation_ready"

    def status(self):
        return {
            "state": self.state,
            "progress": {
                scenario: f"{len(self.samples[scenario])}/{self.samples_per_scenario}"
                for scenario in self.required_scenarios
            },
            "recommendation": self.recommendation,
        }
```

- [ ] **Step 4: Run tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_autotune_session -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\tarotvision\autotune_session.py app_cv\tests\test_autotune_session.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj stan sesji live autotuningu"
```

---

## Task 5: WebSocket protocol for autotune

**Files:**
- Modify: `app_cv/tarotvision/tuning_protocol.py`
- Modify: `app_cv/tests/test_tuning_protocol.py`

- [ ] **Step 1: Write failing protocol tests**

Add to `test_tuning_protocol.py`:

```python
    def test_parses_autotune_start(self):
        msg = parse_control_message('{"type": "autotune_start", "scenario": "three_cards"}')
        self.assertEqual(msg.type, "autotune_start")
        self.assertEqual(msg.scenario, "three_cards")

    def test_parses_autotune_apply(self):
        msg = parse_control_message('{"type": "autotune_apply"}')
        self.assertEqual(msg.type, "autotune_apply")

    def test_rejects_invalid_autotune_scenario(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "autotune_start", "scenario": "twenty_cards"}')
```

Also extend `ControlMessage`:

```python
    scenario: str | None = None
```

- [ ] **Step 2: Run failing tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_tuning_protocol -v"
```

Expected: FAIL, unsupported message type.

- [ ] **Step 3: Implement parser support**

Add to `ALLOWED_TYPES`:

```python
    "autotune_start",
    "autotune_apply",
    "autotune_save",
    "autotune_cancel",
```

Add parser branch:

```python
    if message_type == "autotune_start":
        scenario = str(payload.get("scenario", "three_cards"))
        if scenario not in {"empty", "one_card", "three_cards"}:
            raise ControlMessageError(f"Invalid autotune scenario: {scenario}")
        return ControlMessage(type=message_type, scenario=scenario)

    if message_type in {"autotune_apply", "autotune_cancel"}:
        return ControlMessage(type=message_type)

    if message_type == "autotune_save":
        if "name" not in payload:
            raise ControlMessageError("autotune_save requires name")
        return ControlMessage(type=message_type, name=str(payload["name"]))
```

- [ ] **Step 4: Run tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_tuning_protocol -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\tarotvision\tuning_protocol.py app_cv\tests\test_tuning_protocol.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj protokol komend live autotuningu"
```

---

## Task 6: Backend orchestration in main.py

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tests/test_main_static_audit.py`
- Modify: `app_cv/tests/test_status_store.py`

- [ ] **Step 1: Write static audit tests**

Add to `test_main_static_audit.py`:

```python
    def test_main_handles_autotune_without_auto_apply(self):
        source = self._read_main_source()
        self.assertIn("autotune_start", source)
        self.assertIn("autotune_apply", source)
        self.assertIn("AutotuneSession", source)
        self.assertIn("set_recommendation", source)
        self.assertNotIn("auto_apply_recommendation", source)
```

- [ ] **Step 2: Run failing test**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit -v"
```

Expected: FAIL, strings not present.

- [ ] **Step 3: Implement orchestration**

In `main.py` import:

```python
from tarotvision.autotune_session import AutotuneSession
from tarotvision.autotune_profiles import generate_candidate_profiles
from tarotvision.autotune_scoring import choose_best_profile_result
```

Add global state near existing calibration state:

```python
autotune_session = None
autotune_candidate_profiles = []
```

In control handler:

```python
    if message.type == "autotune_start":
        autotune_session = AutotuneSession(required_scenarios=(message.scenario,), samples_per_scenario=3)
        autotune_candidate_profiles = generate_candidate_profiles()
        calibration_state = {"state": "collecting", "last_score": None, "autotune": autotune_session.status()}
        add_operator_warning(f"Autotuning: zbieram probki scenariusza {message.scenario}")
        return

    if message.type == "autotune_cancel":
        autotune_session = None
        autotune_candidate_profiles = []
        calibration_state = {"state": "idle", "last_score": None}
        add_operator_warning("Anulowano autotuning")
        return

    if message.type == "autotune_apply":
        if autotune_session is None or not autotune_session.recommendation:
            add_operator_warning("Brak rekomendacji autotuningu do zastosowania")
            return
        for name, value in autotune_session.recommendation["profile"].items():
            runtime_session.update(name, value)
        runtime_session.commit_stable()
        calibration_state = {"state": "applied", "last_score": autotune_session.recommendation["score"], "autotune": autotune_session.status()}
        add_operator_warning("Zastosowano rekomendacje autotuningu")
        return
```

During snapshot publish, when a stable analyzed snapshot is available, add a sample to `autotune_session`. The sample must contain:

```python
{
    "candidate_count": int(runtime.get("candidate_count", 0)),
    "accepted_count": len(cards),
    "geometry_score": float(metrics.get("best_candidate_score", 0.0)),
    "recognition_score": float(metrics.get("recognition_score", 0.0)),
    "false_positive_count": 0,
    "matching_ms": float(metrics.get("matching_ms", 0.0)),
}
```

If `autotune_session.ready_to_score()`, build profile results, call `choose_best_profile_result`, then `autotune_session.set_recommendation(best)`.

- [ ] **Step 4: Run targeted tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_main_static_audit app_cv.tests.test_tuning_protocol app_cv.tests.test_autotune_session app_cv.tests.test_autotune_scoring -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\main.py app_cv\tests\test_main_static_audit.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: podlacz sesje live autotuningu w backendzie"
```

---

## Task 7: Studio Auto Tune panel

**Files:**
- Modify: `app_ar/src/studio/studioConsole.js`
- Modify: `app_ar/studio.css`
- Modify: `app_cv/tests/test_camera_controls_static.py`

- [ ] **Step 1: Write static UI test**

Add to `test_camera_controls_static.py`:

```python
    def test_studio_has_autotune_controls(self):
        source = self._read_studio_source()
        self.assertIn("studio-autotune-panel", source)
        self.assertIn("autotune_start", source)
        self.assertIn("autotune_apply", source)
        self.assertIn("autotune_cancel", source)
```

- [ ] **Step 2: Run failing test**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_camera_controls_static -v"
```

Expected: FAIL.

- [ ] **Step 3: Add UI controls**

In Studio sidebar add panel:

```html
<div class="studio-autotune-panel" id="studio-autotune-panel">
    <div class="studio-autotune-header">
        <span class="studio-autotune-title">Auto Tune</span>
        <span class="studio-autotune-state" id="studio-autotune-state">IDLE</span>
    </div>
    <div class="studio-autotune-actions">
        <button type="button" data-studio-action="autotune_start" data-scenario="empty">Pusta mata</button>
        <button type="button" data-studio-action="autotune_start" data-scenario="one_card">1 karta</button>
        <button type="button" data-studio-action="autotune_start" data-scenario="three_cards">3 karty</button>
        <button type="button" data-studio-action="autotune_apply">Apply</button>
        <button type="button" data-studio-action="autotune_cancel">Cancel</button>
    </div>
    <div class="studio-autotune-result" id="studio-autotune-result">Brak rekomendacji.</div>
</div>
```

Add click handlers that send:

```javascript
sendStudioCommand({ type: 'autotune_start', scenario })
sendStudioCommand({ type: 'autotune_apply' })
sendStudioCommand({ type: 'autotune_cancel' })
```

Render status from:

```javascript
const autotune = data.operator?.calibration?.autotune
```

- [ ] **Step 4: Add CSS**

Use restrained Studio styling: no nested cards, no hero, no decorative blobs. Panel can mirror `studio-cv-explain-panel`.

- [ ] **Step 5: Run tests and build**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_camera_controls_static -v"
cmd.exe /c npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: PASS; Vite may repeat known chunk warnings.

- [ ] **Step 6: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_ar\src\studio\studioConsole.js app_ar\studio.css app_cv\tests\test_camera_controls_static.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: dodaj panel auto tune w studio"
```

---

## Task 8: Profile save/apply integration

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tests/test_profile_store.py`
- Modify: `app_cv/tests/test_main_static_audit.py`

- [ ] **Step 1: Write tests for saved recommendation shape**

Add a test that saved profile contains:

```python
{
    "name": "studio-live-YYYYMMDD",
    "parameters": {
        "CARD_DETECT_MIN_AREA_RATIO": 0.001,
        "CARD_DETECT_MAX_CANDIDATES": 10.0,
        "WORKSPACE_INFLATE_PERCENT": 6.0
    },
    "source": "autotune",
    "score": 1.25,
    "confidence": "HIGH"
}
```

- [ ] **Step 2: Implement save**

For `autotune_save`, use existing `ProfileStore` and write the recommended profile after validation through `RuntimeConfig`.

- [ ] **Step 3: Run tests**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest app_cv.tests.test_profile_store app_cv.tests.test_main_static_audit -v"
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add app_cv\main.py app_cv\tests\test_profile_store.py app_cv\tests\test_main_static_audit.py
git -C E:\Antigravity\Projekty\TAROT commit -m "feat: zapisuj rekomendacje autotuningu jako profil"
```

---

## Task 9: Documentation and operator runbook

**Files:**
- Modify: `README.md`
- Create: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TASK.md`
- Create: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`
- Create: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/CHANGELOG.md`
- Create: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`
- Modify: `.ai/TASKS_INDEX.md`

- [ ] **Step 1: Add task index entry**

Add:

```markdown
| **TASK-CV-AUTOTUNE-LIVE-001** | `IN_PROGRESS` | `task/cv-autotune-live-001-recommendation-flow` | Gemini/Codex | Live autotuning jako rekomendacja profilu z apply/rollback i zapisem profilu | 2026-06-02 | Plan zatwierdzony, implementacja etapowa |
```

- [ ] **Step 2: Add runbook text to README**

Add section:

```markdown
### Live Auto Tune

Live Auto Tune jest narzedziem operatorskim w Studio, nie automatycznym trybem produkcyjnym. Operator uruchamia kalibracje dla pustej maty, jednej karty albo trzech kart. Backend zbiera stabilne snapshoty, ocenia kandydackie profile i pokazuje rekomendacje. Profil jest stosowany dopiero po kliknieciu Apply, a zapis do `logs/calibration_profiles/` wymaga Save Profile.
```

- [ ] **Step 3: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add README.md .ai\TASKS_INDEX.md .ai\tasks\TASK-CV-AUTOTUNE-LIVE-001
git -C E:\Antigravity\Projekty\TAROT commit -m "docs: opisz live autotuning i runbook operatora"
```

---

## Task 10: Full verification and live smoke

**Files:**
- Modify: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/TEST_REPORT.md`
- Modify: `.ai/tasks/TASK-CV-AUTOTUNE-LIVE-001/STATE.md`

- [ ] **Step 1: Full backend test**

```bat
cmd /c "cd /d E:\Antigravity\Projekty\TAROT && set PYTHONPATH=C:\tmp\tarot_pydeps;app_cv && python -m unittest discover -s app_cv\tests -v"
```

Expected: PASS.

- [ ] **Step 2: Frontend build**

```bat
cmd.exe /c npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: PASS; known Vite warnings acceptable if unchanged.

- [ ] **Step 3: Manual live smoke**

Run:

```text
start_tarotvision_studio.bat
```

In Studio:

1. Confirm camera preview works.
2. Confirm ArUco table calibration works.
3. Run Auto Tune for `empty`.
4. Run Auto Tune for `one_card`.
5. Run Auto Tune for `three_cards`.
6. Confirm recommendation appears.
7. Click Apply.
8. Confirm `CV Explain` still reports meaningful status.
9. Click Rollback or apply previous saved profile if recognition regresses.

Expected:

```text
GREEN if:
- no JavaScript errors in Studio,
- backend does not crash,
- recommendation appears only after enough samples,
- settings are not applied before operator action,
- Apply changes runtime state,
- Rollback returns to stable state,
- profile save writes JSON under logs/calibration_profiles/.
```

- [ ] **Step 4: Update task state**

In `STATE.md` set:

```markdown
## Status

DONE

## Session Status (2026-06-02)

Live autotuning recommendation flow implemented and verified locally. Full backend tests PASS, frontend build PASS. Manual live smoke result: <GREEN/YELLOW/RED with short reason>.
```

- [ ] **Step 5: Commit**

```bat
git -C E:\Antigravity\Projekty\TAROT add .ai\tasks\TASK-CV-AUTOTUNE-LIVE-001
git -C E:\Antigravity\Projekty\TAROT commit -m "docs: zapisz weryfikacje live autotuningu"
```

---

## Kryteria jakosci calego wdrozenia

Wdrozenie jest gotowe do review dopiero gdy:

- Backend test suite przechodzi w calosci.
- Frontend build przechodzi.
- Studio nie pokazuje Auto Tune w zwyklym overlayu OBS.
- Autotuning nie stosuje rekomendacji bez `autotune_apply`.
- Rekomendacja zawiera score, confidence i konkretne parametry.
- Pusta mata karze false positives.
- Scenariusz 3 kart uwzglednia roznice kandydaci vs zaakceptowane.
- Operator ma rollback.
- Profil po save jest zapisany w `logs/calibration_profiles/`.
- `CV Explain` tlumaczy, co zrobic, gdy rekomendacja ma `LOW` confidence.

---

## Ryzyka i zabezpieczenia

| Ryzyko | Zabezpieczenie |
| --- | --- |
| Autotuning wybierze profil dobry dla jednej karty, zly dla trzech | Scenariusze `empty`, `one_card`, `three_cards`; scoring multi-snapshot |
| Geometryczny profil zwiekszy false positives | Kara za false positives na pustej macie |
| Rozpoznanie pogorszy sie mimo ladnych konturow | Recognition-aware score i accepted cards score |
| Operator przypadkiem popsuje sesje | Apply dopiero po kliknieciu, rollback przez `RuntimeConfigSession` |
| UI stanie sie zbyt skomplikowane | MVP pokazuje tylko status, confidence, score, Apply/Cancel/Save |
| Kamera readback klamie | Ustawienia kamery poza zakresem MVP, chyba ze `camera_controls` potwierdzi support |

---

## Kolejne kroki dla Gemini

1. Zacznij od `Task 0`, bo dwa stare taski autotuningu nadal maja status `DONE / Oczekuje na review`.
2. Nie implementuj live autotuningu przed `Task 1`, bo live smoke pokazal realna luke diagnostyczna kandydaci vs zaakceptowane.
3. Nie zmieniaj progow ORB w pierwszej iteracji. MVP ma stroic tylko bezpieczne parametry detekcji i workspace.
4. Kazdy task commituj osobno.
5. Po kazdym tasku aktualizuj `STATE.md`, `CHANGELOG.md` i `TEST_REPORT.md` dla `TASK-CV-AUTOTUNE-LIVE-001`.

## Plan integracji

Najpierw domykamy diagnostyke, bo bez niej autotuning bedzie czarna skrzynka. Potem dodajemy czysty scoring, potem stan sesji, potem protokol, potem backend, potem UI. Dopiero na koncu zapis profilu i live smoke. Taka kolejnosc minimalizuje ryzyko, ze Studio dostanie przyciski, ktore uruchamiaja niediagnostyczny albo nieodwracalny mechanizm.

## Pewnosc planu

Pewnosc: 8/10.

Niepewnosc dotyczy glownie tego, jakie dokladnie metryki recognition sa obecnie dostepne w runtime payloadzie po kazdym snapshotcie. Jezeli `recognition_score`, `best_candidate_score` albo rozbicie rejected/accepted nie sa jeszcze publikowane, Gemini powinien w pierwszej kolejnosci dodac je do diagnostyki snapshotu, zamiast zgadywac wartosci w `main.py`.
