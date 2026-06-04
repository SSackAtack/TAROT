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

## Required Next Action

Michał/operator uruchamia `stage6_capture_expansion_rws.bat` i wykonuje osiem
zdjęć zgodnie z instrukcjami wizarda.

## Runtime Safety

```text
NO_RUNTIME_INTEGRATION
NO_RUNTIME_THRESHOLD_APPROVAL
NO_NEW_BENCHMARK_BEFORE_REVIEW_PACK_APPROVAL
```
