# STATE

## Status

`DONE`

## Result

- ORB Top-1: `0.80`
- ORB Top-3: `0.85`
- ORB wrong-deck FAR: `0.00`
- ORB mean local runtime proxy: `389.784 ms`
- AKAZE Top-1 / Top-3: `0.70`
- AKAZE wrong-deck FAR: `0.75`
- AKAZE mean local runtime proxy: `892.476 ms`

## Decision Boundary

Wynik benchmarku jest offline-only. Nie zatwierdza thresholdów ani integracji runtime.

## Required Next Action

Supervisor ocenia wynik real-camera benchmarku i decyduje, czy ORB pozostaje
metodą do dalszych eksperymentów offline.
