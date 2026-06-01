# STATE: TASK-CV-SNAPSHOT-002

## Status

DONE

## Branch

`codex/snapshot-first-recognition-hardening`

## Stan aktualny

Dodano `tarotvision.image_io` i `tarotvision.reference_loader`. `main.py` deleguje ladowanie aktywnych talii do `load_active_reference_cards()`, a `card_recognition.load_reference_cards()` czyta pliki przez Unicode-safe wrapper.

## Kolejne kroki

1. Commit i push na branch wykonawczy.
2. Kontynuowac `TASK-CV-SNAPSHOT-003`: analiza snapshotu po warp ArUco.
