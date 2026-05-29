# TarotVision Konsola Kalibracji i Auto-Strojenie Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zbudowac praktyczna konsole operatorska i profilowanie parametrów, które skraca czas ustawienia sesji nagraniowej, poprawia powtarzalnosc testów i daje kontrolowany fundament pod pozniejsze auto-strojenie.

**Architecture:** Nie dopisujemy kolejnej warstwy logiki bezposrednio do monolitu `app_cv/main.py`. Najpierw wydzielamy konfiguracje runtime, walidacje parametrów, profile i protokól sterowania, a dopiero potem dodajemy UI oraz ograniczone auto-strojenie jako rekomendacje zatwierdzana przez operatora. Auto-tuning nie ma "magicznie" znalezc optimum w 5 sekund; ma mierzalnie pomagac wybrac bezpieczny profil dla aktualnego swiatla i kamery.

**Tech Stack:** Python stdlib `unittest`, OpenCV, NumPy, `websockets`, JSONL diagnostics, Vite, Three.js, DOM/CSS bez nowej biblioteki UI.

---

## Status ogolny

Plan koncepcyjny Gemini wskazal dobry kierunek: konsola parametrów, profile i auto-kalibracja. Po analizie aktualnego kodu i ryzyk plan zostaje zwezony i uporzadkowany.

Najwazniejsza decyzja: **najpierw budujemy narzedzie operatorskie i telemetryczne, potem automatyzacje**. Realna wartosc dodana to szybsze diagnozowanie problemów, powtarzalne profile, bezpieczny rollback i mierzalne porównania. Auto-strojenie jest wartosciowe dopiero wtedy, gdy opiera sie na danych z panelu i benchmarków.

## Stan aktualny

- Frontend AR w `app_ar/main.js` jest widokiem produkcyjnym dla OBS. Musi pozostac czysty, przezroczysty i lekki.
- Backend CV w `app_cv/main.py` wysyla status przez WebSocket, ale ignoruje wiadomosci przychodzace od klienta.
- Parametry krytyczne sa stalymi w `main.py`: `MIN_MATCH_COUNT`, `RATIO_THRESH`, `MIN_INLIER_RATIO`, `EMA_ALPHA`, `TRACKING_IOU_THRESHOLD`, `LOCK_DEAD_ZONE_POS`, `LOCK_DEAD_ZONE_ANGLE`, `REVERIFY_INTERVAL_FRAMES`, `BOOST_AFTER_LAYOUT_CHANGE_FRAMES`.
- CLAHE jest tworzone raz i stosowane zarówno do wzorców CV, jak i klatek kamery. Dynamiczna zmiana `clahe_clip_limit` wymaga kontrolowanego przebudowania preprocessingu, bo inaczej wzorce i klatki moga byc niespójne.
- Contour tracking uzywa obecnie Otsu threshold + konturów, nie Canny. Parametry Canny nie sa teraz krytyczna dzwignia systemu.
- Kamera jest konfigurowana tylko przez rozdzielczosc. Sterowanie focusem/ekspozycja/kontrastem przez OpenCV nie zostalo jeszcze zweryfikowane na AnkerWork C310.

## Co zostalo zrobione

- Ustalono, ze poprzednia wersja planu byla zbyt szeroka: kamera, preprocessing, FSM, frontend i auto-tuning byly traktowane jako jeden mechanizm.
- Ustalono, ze parametr `EMA_ALPHA` nie powinien byc opisywany jako frontendowy, bo aktualny frontend ustawia pozycje kart bezposrednio; EMA dziala po stronie CV.
- Ustalono, ze "auto-kalibracja w 5 sekund" jest celem marketingowo atrakcyjnym, ale technicznie ryzykownym jako obietnica. W tej wersji planu auto-strojenie ma dawac rekomendacje profilu z widocznymi metrykami przed/po.

## Kolejne kroki

1. Wdrozyc read-only konsole operatorska, zeby widziec metryki bez dotykania runtime.
2. Wydzielic walidowana konfiguracje runtime i profile JSON.
3. Dodac reczne strojenie bezpiecznych parametrów software'owych z rollbackiem.
4. Zweryfikowac realna obsluge `CAP_PROP_*` na kamerze i dopiero wtedy wystawic suwaki sprzetowe.
5. Dodac auto-strojenie jako rekomendacje, nie jako automatyczne nadpisanie dzialajacego profilu.

---

## Zasady projektowe

### 1. Konsola nie moze psuc overlayu OBS

Domyslny widok `http://localhost:5173/` pozostaje czystym overlayem AR. Konsola operatorska ma byc aktywna tylko w trybie operatorskim, np. `http://localhost:5173/?operator=1`, albo po skrócie klawiszowym podczas pracy developerskiej. Nie wolno domyslnie pokazywac panelu w obrazie przechwytywanym przez OBS.

### 2. Parametry dzielimy wedlug ryzyka

**Bezpieczne live tuning:**

- `LOCK_DEAD_ZONE_POS`
- `LOCK_DEAD_ZONE_ANGLE`
- `TRACKING_IOU_THRESHOLD`
- `REVERIFY_INTERVAL_FRAMES`
- `BOOST_AFTER_LAYOUT_CHANGE_FRAMES`

Te parametry moga byc zmieniane podczas testu, bo nie zmieniaja surowego obrazu ani cache'u wzorców.

**Ostrozne live tuning / tryb kalibracji:**

- `EMA_ALPHA` po stronie CV
- `MIN_MATCH_COUNT`
- `RATIO_THRESH`
- `MIN_INLIER_RATIO`

Zmiany tych parametrów moga poprawic stabilnosc albo zwiekszyc false positives. Panel musi pokazywac zakresy i umozliwiac rollback.

**Tylko kalibracja / restart preprocessingu:**

- `clahe_clip_limit`
- `clahe_tile_grid_size`
- przyszle progi detekcji prostokatów

Zmiana CLAHE wymaga spójnego potraktowania klatek i wzorców. Nie wolno traktowac tego jak zwyklego suwaka kosmetycznego.

**Sprzet kamery po weryfikacji:**

- `CAP_PROP_FOCUS`
- `CAP_PROP_EXPOSURE`
- `CAP_PROP_CONTRAST`
- `CAP_PROP_AUTOFOCUS`

Panel musi pokazac wartosc zadana i wartosc odczytana z kamery. Jesli backend ignoruje parametr, UI ma oznaczyc go jako `unsupported`, a nie udawac sukcesu.

### 3. Auto-strojenie ma minimalizowac ryzyko, nie maksymalizowac pokazowosc

Auto-tuning nie powinien sam trwale nadpisywac konfiguracji. Prawidlowy flow:

```text
Start calibration -> collect samples -> score candidate profiles -> show recommendation -> operator applies -> profile is saved
```

### 4. Sukces musi byc mierzony

Konsola i auto-strojenie maja byc oceniane przez:

- czas ustawienia sesji przed nagraniem,
- liczbe restartów CV potrzebnych do znalezienia stabilnych parametrów,
- spadek false unlock / false reverify,
- stabilnosc `locked_tracked_count`,
- koszt `matching_ms`,
- liczbe zgubionych kart po ruchu i usunieciu,
- powtarzalnosc profilu po restarcie aplikacji.

---

## Realne zyski

1. **Szybszy debug live.** Operator widzi, czy problemem jest matching, tracking, motion trigger, zbyt agresywny boost czy brak wsparcia kamery.
2. **Powtarzalne sesje.** Profile JSON pozwalaja wrócic do dzialajacych ustawien zamiast odtwarzac je z pamieci.
3. **Mniej restartów.** Bezpieczne parametry FSM i tracking mozna zmieniac w locie.
4. **Lepsza wspólpraca agentów.** Kolejny model moze analizowac zapisany profil i logi zamiast zgadywac, jakie suwaki byly ustawione.
5. **Fundament pod auto-tuning.** Najpierw zbieramy metryki i profile, potem automatyzujemy wybór.

## Ryzyka i ograniczenia

| Ryzyko | Skutek | Ograniczenie ryzyka |
| --- | --- | --- |
| Kamera ignoruje `CAP_PROP_*` | Suwaki sprzetowe nie maja realnego efektu | Najpierw `camera_controls.probe`, potem UI z `supported/readback` |
| Zbyt szeroki panel | Operator moze popsuc stabilna sesje | Podzial na tryb basic/advanced i przycisk rollback |
| Zmiana CLAHE rozjezdza wzorce i klatki | Spadek rozpoznawania lub false positives | CLAHE tylko przez kontrolowany reload reference cache |
| Auto-tuning optymalizuje jedna karte, psuje rozklady 3-6 kart | Niestabilnosc produkcyjna | Scenariusze testowe: pusta mata, 1 karta, 3 karty, ruch reki |
| Konsola pojawia sie w OBS | Zepsuty obraz produkcyjny | Tryb operatorski tylko przez query param / osobny widok |
| `main.py` rosnie bez granic | Trudniejszy debug | Nowe moduly w `app_cv/tarotvision/`, `main.py` tylko orkiestruje |

---

## Architektura docelowa

```text
app_ar operator UI (?operator=1)
  -> WebSocket control messages
  -> app_cv/tarotvision/tuning_protocol.py
  -> app_cv/tarotvision/runtime_config.py
  -> app_cv/main.py applies safe runtime changes
  -> app_cv/tarotvision/profile_store.py saves/loads JSON profiles
  -> app_cv/tarotvision/camera_controls.py probes optional camera support
  -> app_cv/tarotvision/calibration_session.py scores candidate profiles
  -> WebSocket status payload exposes metrics/operator state
  -> operator accepts/rejects recommendation
```

Status wysylany z backendu powinien zachowac kompatybilnosc:

```json
{
  "detected": true,
  "cards": [],
  "metrics": {},
  "runtime": {},
  "operator": {
    "enabled": true,
    "active_profile": "default",
    "pending_changes": {},
    "supported_camera_controls": {},
    "calibration": {
      "state": "idle",
      "last_score": null
    }
  }
}
```

Frontend nadal ma uzywac `data.cards || []`, ignorujac `operator` w widoku OBS.

---

## File Structure

- Create: `app_cv/tarotvision/runtime_config.py`
  Walidowana konfiguracja runtime, zakresy parametrów, apply/rollback snapshot.
- Create: `app_cv/tests/test_runtime_config.py`
  Testy walidacji zakresów, rollbacku i serializacji.
- Create: `app_cv/tarotvision/tuning_protocol.py`
  Parser i walidator wiadomosci WebSocket od operatora.
- Create: `app_cv/tests/test_tuning_protocol.py`
  Testy poprawnych i blednych wiadomosci JSON.
- Create: `app_cv/tarotvision/profile_store.py`
  Zapis i odczyt profili z `logs/calibration_profiles/`.
- Create: `app_cv/tests/test_profile_store.py`
  Testy round-trip profilu i obrony przed nieznanymi parametrami.
- Create: `app_cv/tarotvision/camera_controls.py`
  Probe/set/readback dla opcjonalnych parametrów kamery.
- Create: `app_cv/tests/test_camera_controls.py`
  Testy na fake capture bez prawdziwej kamery.
- Create: `app_cv/tarotvision/calibration_session.py`
  Zbieranie próbek metryk i scoring kandydatów profilu.
- Create: `app_cv/tests/test_calibration_session.py`
  Testy scoringu i wyboru rekomendowanego profilu.
- Modify: `app_cv/main.py`
  Odbiór control messages, publikacja sekcji `operator`, stosowanie bezpiecznych zmian.
- Modify: `app_ar/main.js`
  Tryb operatorski, wysylanie control messages, render panelu tylko poza OBS.
- Modify: `app_ar/style.css`
  Minimalny panel operatorski, czytelny na ciemnym tle, domyslnie ukryty.
- Modify: `README.md`
  Instrukcja uruchomienia konsoli operatorskiej i opis profili, gdy funkcja zostanie wdrozona.

---

### Task 1: Runtime Config i walidacja parametrów

**Files:**
- Create: `app_cv/tarotvision/runtime_config.py`
- Create: `app_cv/tests/test_runtime_config.py`

- [ ] **Step 1: Write failing tests**

```python
import unittest

from tarotvision.runtime_config import RuntimeConfig, ParameterValidationError


class RuntimeConfigTest(unittest.TestCase):
    def test_updates_safe_parameter_in_range(self):
        config = RuntimeConfig()

        config.update("LOCK_DEAD_ZONE_POS", 3.5)

        self.assertEqual(config.values["LOCK_DEAD_ZONE_POS"], 3.5)

    def test_rejects_value_outside_range(self):
        config = RuntimeConfig()

        with self.assertRaises(ParameterValidationError):
            config.update("TRACKING_IOU_THRESHOLD", 1.5)

    def test_snapshot_and_rollback(self):
        config = RuntimeConfig()
        snapshot = config.snapshot()
        config.update("LOCK_DEAD_ZONE_POS", 5.0)

        config.rollback(snapshot)

        self.assertEqual(config.values["LOCK_DEAD_ZONE_POS"], 3.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_runtime_config.py -v
```

Expected: import failure because `tarotvision.runtime_config` does not exist.

- [ ] **Step 3: Implement runtime config**

```python
from dataclasses import dataclass
from copy import deepcopy


class ParameterValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TunableParameter:
    name: str
    default: float
    minimum: float
    maximum: float
    live_safe: bool


PARAMETERS = {
    "LOCK_DEAD_ZONE_POS": TunableParameter("LOCK_DEAD_ZONE_POS", 3.0, 1.5, 6.0, True),
    "LOCK_DEAD_ZONE_ANGLE": TunableParameter("LOCK_DEAD_ZONE_ANGLE", 0.5, 0.1, 1.2, True),
    "TRACKING_IOU_THRESHOLD": TunableParameter("TRACKING_IOU_THRESHOLD", 0.35, 0.1, 0.8, True),
    "REVERIFY_INTERVAL_FRAMES": TunableParameter("REVERIFY_INTERVAL_FRAMES", 180.0, 30.0, 600.0, True),
    "BOOST_AFTER_LAYOUT_CHANGE_FRAMES": TunableParameter("BOOST_AFTER_LAYOUT_CHANGE_FRAMES", 12.0, 0.0, 60.0, True),
    "EMA_ALPHA": TunableParameter("EMA_ALPHA", 0.4, 0.05, 1.0, False),
    "MIN_MATCH_COUNT": TunableParameter("MIN_MATCH_COUNT", 18.0, 8.0, 60.0, False),
    "RATIO_THRESH": TunableParameter("RATIO_THRESH", 0.79, 0.6, 0.95, False),
    "MIN_INLIER_RATIO": TunableParameter("MIN_INLIER_RATIO", 0.3, 0.1, 0.8, False),
}


class RuntimeConfig:
    def __init__(self):
        self.values = {name: param.default for name, param in PARAMETERS.items()}

    def update(self, name, value):
        if name not in PARAMETERS:
            raise ParameterValidationError(f"Unknown parameter: {name}")
        param = PARAMETERS[name]
        numeric_value = float(value)
        if numeric_value < param.minimum or numeric_value > param.maximum:
            raise ParameterValidationError(
                f"{name} must be between {param.minimum} and {param.maximum}"
            )
        self.values[name] = numeric_value

    def snapshot(self):
        return deepcopy(self.values)

    def rollback(self, snapshot):
        for name, value in snapshot.items():
            self.update(name, value)
```

- [ ] **Step 4: Verify tests**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_runtime_config.py -v
```

Expected: `3 tests ... OK`.

---

### Task 2: WebSocket control protocol

**Files:**
- Create: `app_cv/tarotvision/tuning_protocol.py`
- Create: `app_cv/tests/test_tuning_protocol.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write parser tests**

```python
import unittest

from tarotvision.tuning_protocol import parse_control_message, ControlMessageError


class TuningProtocolTest(unittest.TestCase):
    def test_parses_tuning_update(self):
        message = parse_control_message(
            '{"type": "tuning_update", "param": "LOCK_DEAD_ZONE_POS", "value": 3.5}'
        )

        self.assertEqual(message.type, "tuning_update")
        self.assertEqual(message.param, "LOCK_DEAD_ZONE_POS")
        self.assertEqual(message.value, 3.5)

    def test_rejects_unknown_type(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "unknown"}')

    def test_parses_profile_apply(self):
        message = parse_control_message('{"type": "profile_apply", "name": "studio_day"}')

        self.assertEqual(message.type, "profile_apply")
        self.assertEqual(message.name, "studio_day")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement parser**

```python
from dataclasses import dataclass
import json


class ControlMessageError(ValueError):
    pass


@dataclass(frozen=True)
class ControlMessage:
    type: str
    param: str | None = None
    value: float | str | None = None
    name: str | None = None


ALLOWED_TYPES = {
    "tuning_update",
    "tuning_rollback",
    "profile_save",
    "profile_apply",
    "camera_probe",
    "calibration_start",
    "calibration_cancel",
}


def parse_control_message(raw_message):
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError as exc:
        raise ControlMessageError("Invalid JSON") from exc

    message_type = payload.get("type")
    if message_type not in ALLOWED_TYPES:
        raise ControlMessageError(f"Unsupported message type: {message_type}")

    if message_type == "tuning_update":
        if "param" not in payload or "value" not in payload:
            raise ControlMessageError("tuning_update requires param and value")
        return ControlMessage(
            type=message_type,
            param=str(payload["param"]),
            value=payload["value"],
        )

    if message_type in {"profile_save", "profile_apply"}:
        if "name" not in payload:
            raise ControlMessageError(f"{message_type} requires name")
        return ControlMessage(type=message_type, name=str(payload["name"]))

    return ControlMessage(type=message_type)
```

- [ ] **Step 3: Integrate receive path in `main.py`**

Replace the current ignored incoming message loop:

```python
async for message in websocket:
    pass
```

with a call that parses and queues control messages under `status_lock`. The CV loop should apply messages between frames, not inside the WebSocket coroutine.

- [ ] **Step 4: Verify**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_tuning_protocol.py -v
python -m py_compile E:\Antigravity\Projekty\TAROT\app_cv\main.py
```

Expected: tests OK and compile OK.

---

### Task 3: Read-only operator console

**Files:**
- Modify: `app_ar/main.js`
- Modify: `app_ar/style.css`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Add operator status payload**

Backend status should include:

```python
"operator": {
    "enabled": True,
    "active_profile": "default",
    "pending_changes": {},
    "supported_camera_controls": {},
    "calibration": {"state": "idle", "last_score": None},
}
```

- [ ] **Step 2: Add frontend operator mode guard**

In `app_ar/main.js`, compute:

```javascript
const operatorMode = new URLSearchParams(window.location.search).get('operator') === '1'
```

Only create the panel when `operatorMode` is true.

- [ ] **Step 3: Show read-only metrics**

Panel should display at minimum:

- `fps`
- `matching_ms`
- `cards_checked`
- `orb_skipped_locked`
- `locked_tracked_count`
- `available_card_count`
- `tracked_card_count`
- `schedule_mode`
- `boost_frames_remaining`

- [ ] **Step 4: Verify frontend build**

Run:

```powershell
npm --prefix E:\Antigravity\Projekty\TAROT\app_ar run build
```

Expected: build OK. Existing chunk-size warning is acceptable.

---

### Task 4: Manual tuning z Apply / Rollback

**Files:**
- Modify: `app_cv/main.py`
- Modify: `app_cv/tarotvision/runtime_config.py`
- Modify: `app_ar/main.js`
- Modify: `app_ar/style.css`

- [ ] **Step 1: Add pending/apply model**

UI sends `tuning_update`, backend validates it and applies immediately only for `live_safe=True`. For non-live-safe values backend stores them as `pending_changes` and returns warning:

```json
{
  "type": "tuning_update",
  "param": "MIN_MATCH_COUNT",
  "value": 22
}
```

Expected backend behavior:

```json
{
  "operator": {
    "pending_changes": {
      "MIN_MATCH_COUNT": 22
    }
  },
  "warnings": ["MIN_MATCH_COUNT requires calibration/apply step"]
}
```

- [ ] **Step 2: Apply live-safe values in the CV loop**

Replace direct reads of module constants in runtime-sensitive places with reads from `runtime_config.values`, starting with:

- `LOCK_DEAD_ZONE_POS`
- `LOCK_DEAD_ZONE_ANGLE`
- `TRACKING_IOU_THRESHOLD`
- `REVERIFY_INTERVAL_FRAMES`
- `BOOST_AFTER_LAYOUT_CHANGE_FRAMES`

- [ ] **Step 3: Add rollback**

Operator can send:

```json
{"type": "tuning_rollback"}
```

Backend restores the last stable snapshot and publishes the restored values in `operator`.

- [ ] **Step 4: Verify full Python checks**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest discover -s E:\Antigravity\Projekty\TAROT\app_cv\tests -v
python -m py_compile E:\Antigravity\Projekty\TAROT\app_cv\main.py
```

Expected: tests OK and compile OK.

---

### Task 5: Profile store

**Files:**
- Create: `app_cv/tarotvision/profile_store.py`
- Create: `app_cv/tests/test_profile_store.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write profile tests**

```python
import tempfile
import unittest

from tarotvision.profile_store import ProfileStore


class ProfileStoreTest(unittest.TestCase):
    def test_save_and_load_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)
            store.save("studio_day", {"LOCK_DEAD_ZONE_POS": 3.5})

            profile = store.load("studio_day")

        self.assertEqual(profile["LOCK_DEAD_ZONE_POS"], 3.5)

    def test_rejects_path_traversal_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save("../bad", {"LOCK_DEAD_ZONE_POS": 3.5})

    def test_rejects_unknown_parameter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save("studio_day", {"UNKNOWN_PARAM": 1.0})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement profile store**

```python
import json
import os
import re

from tarotvision.runtime_config import PARAMETERS


SAFE_PROFILE_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")


class ProfileStore:
    def __init__(self, directory):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path_for(self, name):
        if not SAFE_PROFILE_NAME.match(name):
            raise ValueError(f"Invalid profile name: {name}")
        return os.path.join(self.directory, f"{name}.json")

    def save(self, name, values):
        unknown = [param for param in values if param not in PARAMETERS]
        if unknown:
            raise ValueError(f"Unknown profile parameters: {unknown}")
        path = self._path_for(name)
        with open(path, "w", encoding="utf-8") as profile_file:
            json.dump(values, profile_file, indent=2, sort_keys=True)

    def load(self, name):
        path = self._path_for(name)
        with open(path, "r", encoding="utf-8") as profile_file:
            return json.load(profile_file)
```

- [ ] **Step 3: Integrate profile messages**

Support:

```json
{"type": "profile_save", "name": "studio_day"}
{"type": "profile_apply", "name": "studio_day"}
```

Profiles live in:

```text
logs/calibration_profiles/
```

- [ ] **Step 4: Verify**

Run:

```powershell
$env:PYTHONPATH="E:\Antigravity\Projekty\TAROT\app_cv"
python -m unittest E:\Antigravity\Projekty\TAROT\app_cv\tests\test_profile_store.py -v
```

Expected: `2 tests ... OK`.

---

### Task 6: Camera controls probe

**Files:**
- Create: `app_cv/tarotvision/camera_controls.py`
- Create: `app_cv/tests/test_camera_controls.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write fake-capture tests**

```python
import unittest

from tarotvision.camera_controls import probe_camera_control


class FakeCapture:
    def __init__(self, supported=True):
        self.supported = supported
        self.value = 0.0

    def get(self, prop):
        return self.value if self.supported else -1.0

    def set(self, prop, value):
        if not self.supported:
            return False
        self.value = value
        return True


class CameraControlsTest(unittest.TestCase):
    def test_probe_reports_supported_when_readback_changes(self):
        result = probe_camera_control(FakeCapture(True), prop_id=1, test_value=12.0)

        self.assertTrue(result.supported)
        self.assertEqual(result.readback_value, 12.0)

    def test_probe_reports_unsupported_when_set_fails(self):
        result = probe_camera_control(FakeCapture(False), prop_id=1, test_value=12.0)

        self.assertFalse(result.supported)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement camera probe**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraControlProbe:
    supported: bool
    requested_value: float
    readback_value: float


def probe_camera_control(capture, prop_id, test_value):
    before = float(capture.get(prop_id))
    set_ok = bool(capture.set(prop_id, float(test_value)))
    readback = float(capture.get(prop_id))
    supported = set_ok and readback != before
    return CameraControlProbe(
        supported=supported,
        requested_value=float(test_value),
        readback_value=readback,
    )
```

- [ ] **Step 3: Expose probe result**

On `camera_probe`, backend tests focus/exposure/contrast/autofocus and publishes:

```json
"supported_camera_controls": {
  "CAP_PROP_FOCUS": {"supported": true, "requested_value": 120.0, "readback_value": 120.0}
}
```

- [ ] **Step 4: Do not expose unsupported sliders as active**

Frontend may show unsupported camera parameters, but controls must be disabled and labeled `unsupported`.

---

### Task 7: Calibration scoring and recommendation

**Files:**
- Create: `app_cv/tarotvision/calibration_session.py`
- Create: `app_cv/tests/test_calibration_session.py`
- Modify: `app_cv/main.py`

- [ ] **Step 1: Write scoring tests**

```python
import unittest

from tarotvision.calibration_session import score_sample, choose_best_candidate


class CalibrationSessionTest(unittest.TestCase):
    def test_score_rewards_stable_detection_and_tracking(self):
        score = score_sample(
            identified=True,
            good_matches=35,
            false_contours=1,
            jitter=0.1,
            matching_ms=90.0,
        )

        self.assertGreater(score, 1000.0)

    def test_choose_best_candidate(self):
        candidates = [
            {"name": "noisy", "score": 900.0},
            {"name": "stable", "score": 1200.0},
        ]

        self.assertEqual(choose_best_candidate(candidates)["name"], "stable")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement scoring**

```python
def score_sample(identified, good_matches, false_contours, jitter, matching_ms):
    identification_bonus = 1000.0 if identified else 0.0
    feature_score = min(float(good_matches), 80.0) * 2.0
    false_contour_penalty = float(false_contours) * 20.0
    jitter_penalty = float(jitter) * 120.0
    matching_penalty = max(0.0, float(matching_ms) - 120.0) * 0.5
    return identification_bonus + feature_score - false_contour_penalty - jitter_penalty - matching_penalty


def choose_best_candidate(candidates):
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate["score"])
```

- [ ] **Step 3: Limit first auto-recommendation scope**

First calibration pass may recommend only:

- `LOCK_DEAD_ZONE_POS`
- `LOCK_DEAD_ZONE_ANGLE`
- `TRACKING_IOU_THRESHOLD`
- `BOOST_AFTER_LAYOUT_CHANGE_FRAMES`

It must not change camera parameters or CLAHE.

- [ ] **Step 4: Publish recommendation, do not auto-apply**

Backend publishes:

```json
"calibration": {
  "state": "recommendation_ready",
  "recommended_profile": "auto_2026_05_29_1530",
  "score_before": 920.0,
  "score_after": 1180.0
}
```

Operator must explicitly apply the profile.

---

### Task 8: Live verification protocol

**Files:**
- Modify: `docs/superpowers/plans/2026-05-29-tarotvision-auto-tuning-plan.md`
- Modify: `README.md` after implementation

- [ ] **Step 1: Run baseline without tuning**

Scenario:

```text
1. Empty table, 10 seconds.
2. One card, 20 seconds.
3. Three cards, 30 seconds.
4. Move one locked card slightly.
5. Remove one card.
```

Save metrics from `logs/cv_metrics.jsonl`.

- [ ] **Step 2: Run same scenario with manual tuned profile**

Compare:

- mean `fps`
- mean `matching_ms`
- `orb_skipped_locked`
- `locked_tracked_count`
- number of false unlock events in `cv_runtime.log`
- time until card removal is reflected in AR

- [ ] **Step 3: Run auto-recommendation**

Only accept it if it beats the baseline on at least two stability metrics without increasing `matching_ms` by more than 15%.

- [ ] **Step 4: Update README**

Document:

- how to open operator console,
- where profiles are saved,
- how to rollback,
- which camera controls are supported on the tested machine.

---

## Acceptance Criteria

- Domyslny overlay OBS nie pokazuje konsoli.
- Operator console otwiera sie tylko w trybie operatorskim.
- Backend przyjmuje i waliduje control messages przez WebSocket.
- Bezpieczne parametry mozna zmieniac live i rollback dziala bez restartu.
- Profile JSON mozna zapisac, wczytac i porównac w logach.
- UI nie pokazuje nieobslugiwanych `CAP_PROP_*` jako dzialajacych.
- Auto-tuning generuje rekomendacje profilu, ale jej nie stosuje bez akceptacji operatora.
- README zostaje zaktualizowany dopiero po realnym wdrozeniu funkcji.
- Wszystkie testy `app_cv/tests` przechodza przed commitem.

## Out of Scope dla pierwszego wdrozenia

- Pelny auto-tuning kamery bez weryfikacji `CAP_PROP_*`.
- YOLO/ONNX/OpenVINO jako czesc konsoli.
- Dynamiczne ROI jako element tego planu.
- Przepisywanie calego `main.py`.
- Obietnica stalej auto-kalibracji w 5 sekund.
- Canny jako glówna dzwignia strojenia, dopóki pipeline trackingowy go realnie nie uzywa.

## Session Status (2026-05-29, Codex)

Przeredagowano plan po analizie realnych zysków i ryzyk:

- rozdzielono konsole operatorska, manual tuning, profile, probe kamery i auto-rekomendacje,
- usunieto zalozenie, ze auto-tuning automatycznie i trwale nadpisuje parametry,
- dodano wymóg trybu operatorskiego poza domyslnym overlayem OBS,
- doprecyzowano podzial parametrów wedlug ryzyka,
- dodano modulowa architekture, testy i kryteria akceptacji.

## Immediate Next Action

Zaczac od Task 1 i Task 3: `runtime_config.py` oraz read-only operator console. To daje wartosc diagnostyczna natychmiast, bez ryzyka destabilizacji obecnego PoC.
