# STATE: TASK-CV-SNAPSHOT-003

## Status

DONE

## Branch

`codex/snapshot-first-recognition-hardening`

## Stan aktualny

`SnapshotFirstPipeline` wybiera `analysis_frame` przed analiza: jesli `TableCalibration` jest skalibrowany i `warp_frame()` zwraca obraz, analyzer dostaje klatke sprostowana. W przeciwnym razie zostaje fallback do oryginalnego snapshotu.

## Kolejne kroki

1. Commit i push na branch wykonawczy.
2. Kontynuowac `TASK-CV-SNAPSHOT-004`: diagnostyka porazek detekcji i rozpoznania.
