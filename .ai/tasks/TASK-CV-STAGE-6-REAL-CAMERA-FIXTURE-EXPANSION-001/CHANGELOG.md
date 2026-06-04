# CHANGELOG

## 2026-06-04

- Utworzono organizacyjno-operatorski task rozszerzenia fixture.
- Zapisano status `BLOCKED_BY_OPERATOR_CAPTURE`.
- Zapisano wymaganą różnorodność nowych fizycznych próbek.
- Zablokowano kolejny benchmark do czasu zatwierdzenia manual review pack.
- Dodano osobny minimalny wizard i launcher dla 8 zdjęć RWS.
- Dodano preflight ekspansji i testy jednostkowe.
- Po zgłoszeniu operatora zidentyfikowano konflikt wspólnego katalogu roboczego:
  gałąź `Komercja` nie zawierała nowego launchera i uruchamiała legacy 28.
- Utworzono izolowany worktree Stage 6.
- Główny launcher Stage 6 domyślnie uruchamia RWS 8 próbek; legacy wymaga
  jawnego potwierdzenia.
- Poprawiono licznik kroków, ground truth RWS i rygor preflightu.
- Nie zmieniono benchmarków ani runtime.
