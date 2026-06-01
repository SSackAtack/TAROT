# STATE: TASK-CV-SNAPSHOT-008

## Status

DONE

## Branch

`codex/snapshot-first-recognition-hardening`

## Stan aktualny

Dodano pierwszy kontrakt CLI/CSV dla lokalnego benchmarku snapshot recognition. Skrypt na tym etapie nie uruchamia jeszcze realnego `SnapshotAnalyzer`; zapisuje stabilny format wyników dla lokalnych próbek operatorskich.

## Session Status (2026-06-01)

Codex poprawił import testu benchmarku tak, aby działał także przy backendowym uruchomieniu CI z katalogu `app_cv`.

## Kolejne kroki

1. Review `TASK-CV-SNAPSHOT-008`.
2. Po zebraniu lokalnych zdjęć podpiąć benchmark do realnego `SnapshotAnalyzer`.
3. Nie commitować próbek z fizycznej kamery bez osobnej zgody Michała.
