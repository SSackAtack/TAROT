# STATE

## Status

```text
APPROVED_RWS_EXPANSION_FIXTURE_OFFLINE_ONLY
```

## Completed

- Przygotowano zakres operator-assisted fixture expansion.
- Potwierdzono ponowne użycie istniejących narzędzi capture, preflight i review.
- Utrwalono zakaz uruchamiania benchmarku przed zatwierdzeniem review pack.
- Dodano osobny minimalny wizard dla 8 zdjęć RWS na jasnej macie.
- Dodano osobny preflight, który wymaga kompletnej paczki ośmiu nowych sesji.
- Oddzielono manifest, ground truth i output ekspansji od wcześniejszych 28 próbek.
- Rozdzielono Stage 6 i `Komercja` do osobnych worktree.
- Naprawiono główny launcher: domyślnie uruchamia RWS 8 próbek, a legacy 28 wymaga jawnego wyboru.
- Kroki ekspansji pokazują `1/8`, a nie `1/28`.
- RWS zapisuje rzeczywiste `expected_card_id` i `expected_behavior: identify`.
- Preflight blokuje błędną etykietę i brakujące pliki capture.
- Zdiagnozowano błąd MSMF `-1072875772`: backend `python main.py` zajmował kamerę.
- Stabilny starter wykrywa aktywny backend przed capture i blokuje start z PID.
- Wizard wyjaśnia zajęcie kamery przy błędzie odczytu strumienia.
- Przeprowadzono fizyczną procedurę capture 8 próbek RWS na jasnej macie.
- Zweryfikowano pomyślny przebieg preflightu (preflight_report.json status: PASS).
- Spakowano manual_review_pack do pliku ZIP i wyznaczono sumę kontrolną SHA-256.
- Paczka została manualnie sprawdzona i zatwierdzona decyzją `APPROVED_RWS_EXPANSION_FIXTURE_OFFLINE_ONLY_BY_CHATGPT_SUPERVISOR`.

## Manual Review Pack Information

- **ZIP Path:** `logs/offline_replay/stage6_real_camera_fixture_expansion_rws_minimal_manual_review_pack.zip` (Local artifact only, not committed.)
- **SHA-256:** `1DE6E7FE4750ECBFE1DCFD092B05149B7D6503D40E7BB746B3B3D52C965B1DA8`
- **Sample Count:** `8`
- **Preflight Status:** `PASS`
- **Benchmark:** `NOT_RUN` — zablokowany podczas weryfikacji paczki; do uruchomienia w kolejnym tasku offline.
- **Runtime:** `NOT_CHANGED`

## Required Next Action

Uruchomienie zadania offline benchmarku: `TASK-CV-STAGE-6-RWS-EXPANSION-BENCHMARK-001` (bez integracji runtime).

## Runtime Safety

```text
NO_RUNTIME_INTEGRATION
NO_RUNTIME_THRESHOLD_APPROVAL
```
