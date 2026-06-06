# Handoff: State-first diff live smoke

Data: 2026-06-06 11:21 CEST
Branch: `codex/project-mvp-recovery-audit-2026-06-05`

## Stan aktualny

Sesja robocza testowała launcher i runtime pipeline `state_first_diff` dla podejścia:

- pusta mata jako zablokowana referencja sesji,
- `previous_snapshot` jako ostatni zaakceptowany stan stołu,
- `current_snapshot` jako nowa ustabilizowana klatka,
- detekcja zmian między `previous_snapshot` i `current_snapshot`,
- ROI z różnicy jako wejście do analizy/rozpoznania karty.

Użytkownik uruchomił `start_tarotvision_studio_state_first_diff.bat`, wykonał `START` i `CAPTURE EMPTY`. Pusta mata została poprawnie zablokowana.

Lokalna konfiguracja operatora:

- `app_ar/public/active_decks.json` ma lokalnie zmianę `rider-waite-smith -> gilded`.
- Ten plik jest poza zakresem i nie był commitowany.
- Nie robić `git restore app_ar/public/active_decks.json` bez zgody Michała.

## Co zostało zrobione w tej sesji

Dodano i wypchnięto launcher:

- `start_tarotvision_studio_state_first_diff.bat`
- commit `b125eeb chore: dodaj launcher state-first diff`

Naprawiono kolejne błędy integracyjne eksperymentalnego pipeline `state_first_diff`:

- `27ecff4 fix: napraw gate state-first diff`
  - `SnapshotGate.update()` dostaje teraz `now_ms`, `motion_detected`, `changed_ratio`.
- `31d24d6 fix: dostosuj publikacje state-first statusu`
  - `_publish()` używa aktualnego kontraktu `StatusStore.update_cv_state(cards, metrics, runtime, operator, layout, warnings)`.
- `9c0c63f fix: pokaz liczbe markerow aruco w state-first`
  - runtime state-first raportuje `aruco_calibrated`, `aruco_markers`, `table.marker_ids`.
  - `CV EXPLAIN` liczy markery również z `table.marker_ids`.
- `c1396fd fix: przekaz runtime do state-first explainability`
  - `build_operator_snapshot_fn` w state-first dostaje `cards`, `metrics`, `runtime`, `layout`, `warnings`.

Weryfikacje wykonane:

- `python -m unittest app_cv.tests.test_state_first_diff_pipeline -v` => PASS, 9/9
- `python -m unittest app_cv.tests.test_operator_explainability -v` => PASS, 5/5
- `python -m py_compile app_cv\tarotvision\pipelines\state_first_diff.py`
- `python -m py_compile app_cv\tarotvision\operator_explainability.py app_cv\tarotvision\pipelines\state_first_diff.py`

Testy wymagały lokalnych zależności instalowanych tymczasowo do `.tmp_pydeps_statefirst`; katalog został usunięty po testach.

## Live payload z WebSocket

Codex pasywnie odczytał payloady z:

`ws://localhost:8765`

Komenda używana do diagnostyki była oparta o PowerShell `.NET ClientWebSocket`, bez wysyłania komend sterujących.

Ostatni odczyt po `CAPTURE EMPTY`:

- `cards=0`
- `detected=False`
- `layout_state=waiting_for_stable_frame`
- `gate_state=settling`
- `stable_for_ms` około `45-46 ms`
- `aruco_calibrated=True`
- `aruco_markers=4`
- `marker_ids=10,11,12,13`
- `empty_locked=True`
- `previous_snapshot=True`
- `current_snapshot=False`
- `ready_for_diff=False`
- `change_region_count` brak
- `roi_count` brak
- `accepted_card_count` brak

Wniosek: ArUco działa, talia Gilded jest aktywna, empty reference jest zablokowana. Pipeline nie dochodzi do wykonania różnicy, bo gate stale pozostaje w `settling` i nie tworzy `current_snapshot`.

## Najważniejszy wniosek techniczny

Obecny blocker nie jest ArUco, deck ani recognition.

Najbardziej prawdopodobny problem jest w czasie przekazywanym do `SnapshotGate.update()` w `state_first_diff`.

W `snapshot_first.py` gate dostaje:

```python
now_ms = int(time.time() * 1000)
snapshot_gate.update(now_ms=now_ms, ...)
```

W `state_first_diff.py` po ostatniej poprawce gate dostaje:

```python
now_ms=frame_loop_start
```

`frame_loop_start` w `main.py` wygląda na wartość z `time.perf_counter()` w sekundach, nie timestamp w milisekundach. To tłumaczy, dlaczego `stable_for_ms` jest bardzo małe i gate pozostaje w `settling`.

## Następny krok dla kolejnego agenta

1. Przeczytać obowiązkowo:
   - `.ai/PROJECT_STATE.md`
   - `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`
   - `.ai/TASKS_INDEX.md`
   - ten plik handoff.

2. Sprawdzić status:

```bash
git status
git diff -- app_ar/public/active_decks.json
```

Nie commitować `app_ar/public/active_decks.json`.

3. Zweryfikować root cause czasu gate:

- sprawdzić, gdzie w `main.py` ustawiany jest `frame_loop_start`;
- sprawdzić `app_cv/tarotvision/snapshot_gate.py`;
- porównać z `app_cv/tarotvision/pipelines/snapshot_first.py`;
- dodać test regresyjny w `app_cv/tests/test_state_first_diff_pipeline.py`, że `StateFirstDiffPipeline` przekazuje do gate timestamp w milisekundach, a nie surowe sekundy `perf_counter`.

4. Proponowana poprawka:

W `state_first_diff.py` nie używać `frame_loop_start` jako `now_ms`. Zbudować `now_ms = int(time.time() * 1000)` analogicznie do `snapshot_first.py`, albo przekazać z `main.py` jawny timestamp ms. Najmniej inwazyjna poprawka to lokalnie w `process_frame`:

```python
now_ms = int(time.time() * 1000)
gate_decision = self.snapshot_gate.update(
    now_ms=now_ms,
    motion_detected=motion_result.motion_detected,
    changed_ratio=motion_result.changed_ratio,
)
```

Wtedy `frame_loop_start` można nadal używać do metryk czasu pętli, ale nie jako timestamp gate.

5. Po poprawce uruchomić:

```bash
python -m unittest app_cv.tests.test_state_first_diff_pipeline -v
python -m py_compile app_cv\tarotvision\pipelines\state_first_diff.py
```

Jeśli środowisko nie ma `numpy`, można tymczasowo zainstalować zależności do `.tmp_pydeps_statefirst`, ale nie commitować tego katalogu.

6. Po restarcie `.bat` poprosić Michała:

- `START`
- `CAPTURE EMPTY`
- położyć jedną kartę Gilded
- odczekać 2-3 sekundy
- poprosić agenta o „sprawdź payload”

Oczekiwany payload po poprawce:

- `stable_for_ms` rośnie do progu gate,
- `current_snapshot` pojawia się chwilowo,
- `ready_for_diff=True` w momencie pary snapshotów,
- `change_region_count >= 1`,
- `roi_count >= 1`,
- potem `accepted_card_count` i `cards` pokażą, czy recognition zadziałało.

## Komenda do pasywnego podglądu payloadu

PowerShell:

```powershell
$ws = [System.Net.WebSockets.ClientWebSocket]::new()
$uri = [Uri]'ws://localhost:8765'
$connected = $ws.ConnectAsync($uri, [Threading.CancellationToken]::None).Wait(3000)
if (-not $connected -or $ws.State -ne 'Open') { throw 'Nie udalo sie polaczyc z ws://localhost:8765' }
$buffer = New-Object byte[] 1048576
for ($i=0; $i -lt 8; $i++) {
    $result = $ws.ReceiveAsync([ArraySegment[byte]]::new($buffer), [Threading.CancellationToken]::None).Result
    $text = [Text.Encoding]::UTF8.GetString($buffer, 0, $result.Count)
    $obj = $text | ConvertFrom-Json
    [pscustomobject]@{
        sample=$i
        cards=($obj.cards | Measure-Object).Count
        detected=$obj.detected
        layout_state=$obj.layout.state
        gate_state=$obj.layout.gate_state
        stable_for_ms=$obj.layout.stable_for_ms
        aruco_calibrated=$obj.runtime.aruco_calibrated
        aruco_markers=$obj.runtime.aruco_markers
        marker_ids=($obj.runtime.table.marker_ids -join ',')
        empty_locked=$obj.layout.session.empty_reference_locked
        previous_snapshot=$obj.layout.session.previous_snapshot
        current_snapshot=$obj.layout.session.current_snapshot
        ready_for_diff=$obj.layout.session.ready_for_diff
        change_region_count=$obj.layout.change_region_count
        roi_count=$obj.layout.roi_count
        accepted_card_count=$obj.layout.accepted_card_count
        mask_nonzero_ratio=$obj.layout.mask_nonzero_ratio
        explain_severity=$obj.operator.explainability.severity
        next_action=$obj.operator.explainability.next_action
    } | Format-List
    Start-Sleep -Milliseconds 700
}
$ws.Dispose()
```

## Czego nie robić

- Nie wracać teraz do autotuningu.
- Nie luzować geometrii kart.
- Nie zmieniać decków ani `active_decks.json` bez zgody Michała.
- Nie interpretować `ArUco 0/4` ze starego UI bez potwierdzenia payloadem; live payload potwierdził `4/4`.
- Nie otwierać PR jako gotowy do merge, dopóki smoke `one_card` state-first nie przejdzie przez diff i nie pokaże, gdzie zatrzymuje się recognition.

## Status na zamknięcie sesji

Status: `STATE_FIRST_DIFF_GATE_TIME_FIX_REQUIRED`

Najbliższy blocker: `SnapshotGate` w state-first prawdopodobnie dostaje czas w złej jednostce.

