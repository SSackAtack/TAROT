# STATE: TASK-CV-SNAPSHOT-005

## Status

DONE

## Branch

`codex/snapshot-first-recognition-hardening`

## Stan aktualny

Dodano `card_detection_profiles.py` z profilami Canny/adaptive threshold oraz deduplikacja po IoU bounding boxow. `SnapshotAnalyzer` korzysta z `find_card_quads_multi_profile()` jako domyslnego detektora.

## Kolejne kroki

1. Commit i push na branch wykonawczy.
2. Kontynuowac `TASK-CV-SNAPSHOT-006`: opcjonalny model pustej maty.
