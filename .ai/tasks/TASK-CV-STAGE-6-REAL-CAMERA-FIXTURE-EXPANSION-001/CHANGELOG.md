# CHANGELOG

## 2026-06-04

- Utworzono organizacyjno-operatorski task rozszerzenia fixture.
- Zapisano status `BLOCKED_BY_OPERATOR_CAPTURE`.
- Zapisano wymaganą różnorodność nowych fizycznych próbek.
- Zablokowano kolejny benchmark do czasu zatwierdzenia manual review pack.
- Dodano osobny minimalny wizard i launcher dla 8 zdjęć RWS.
- Dodano preflight ekspansji i testy jednostkowe.
- Po zgłoszeniu operatora zidentyfikowano konflikt wspólnego katalogu roboczego: gałąź `Komercja` nie zawierała nowego launchera i uruchamiała legacy 28.
- Utworzono izolowany worktree Stage 6.
- Główny launcher Stage 6 domyślnie uruchamia RWS 8 próbek; legacy wymaga jawnego potwierdzenia.
- Poprawiono licznik kroków, ground truth RWS i rygor preflightu.
- Dodano czytelną diagnostykę zajętej kamery po błędzie Windows MSMF.
- Stabilny starter blokuje start, gdy działa backend `python main.py`.
- Nie zmieniono benchmarków ani runtime.
- Zakończono fizyczne przechwytywanie 8 próbek RWS na jasnej macie.
- Spakowano manual review pack do formatu ZIP i obliczono sumę kontrolną SHA-256.
- Zaktualizowano status zadania na `PROVISIONAL_ACCEPTED_FOR_MANUAL_REVIEW`.
