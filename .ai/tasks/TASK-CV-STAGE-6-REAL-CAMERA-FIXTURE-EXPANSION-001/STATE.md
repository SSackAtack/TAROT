# STATE

## Status

`PROVISIONAL_BLOCKED`

## Blocking Condition

```text
BLOCKED_BY_OPERATOR_CAPTURE
WAITING_FOR_NEW_REAL_CAMERA_CAPTURE
```

Brakuje nowych fizycznych próbek real-camera. Istniejący fixture został już
wykorzystany do aktualnych benchmarków i nie powinien być ponownie używany do
deklarowania dalszego postępu walidacji.

## Completed

- Przygotowano zakres operator-assisted fixture expansion.
- Potwierdzono ponowne użycie istniejących narzędzi capture, preflight i review.
- Utrwalono zakaz uruchamiania benchmarku przed zatwierdzeniem review pack.
- Dodano osobny minimalny wizard dla 8 zdjęć RWS na jasnej macie.
- Dodano osobny preflight, który wymaga kompletnej paczki ośmiu nowych sesji.
- Oddzielono manifest, ground truth i output ekspansji od wcześniejszych 28 próbek.
- Rozdzielono Stage 6 i `Komercja` do osobnych worktree.
- Naprawiono główny launcher: domyślnie uruchamia RWS 8 próbek, a legacy 28
  wymaga jawnego wyboru.
- Kroki ekspansji pokazują `1/8`, a nie `1/28`.
- RWS zapisuje rzeczywiste `expected_card_id` i `expected_behavior: identify`.
- Preflight blokuje błędną etykietę i brakujące pliki capture.

## Required Next Action

Michał/operator uruchamia
`E:\Antigravity\Projekty\START_TAROT_STAGE6_RWS_8_PROBEK.bat` i wykonuje osiem
zdjęć zgodnie z instrukcjami wizarda.

## Runtime Safety

```text
NO_RUNTIME_INTEGRATION
NO_RUNTIME_THRESHOLD_APPROVAL
NO_NEW_BENCHMARK_BEFORE_REVIEW_PACK_APPROVAL
```
