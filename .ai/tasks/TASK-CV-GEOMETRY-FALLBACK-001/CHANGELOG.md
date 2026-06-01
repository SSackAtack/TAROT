# CHANGELOG: TASK-CV-GEOMETRY-FALLBACK-001

## 2026-06-01

- Przywrócono testowalność `SnapshotAnalyzer` po zmianach diagnostycznych z live testu.
- Dodano stabilną diagnostykę detekcji i metryki runtime dla profili geometrycznych.
- Dodano `minAreaRect` fallback jako bezpieczny generator kandydatów 4-punktowych.
- Dodano filtr markerów ArUco stołu, aby ignorować ID spoza `10-13`.
- Zweryfikowano 35 testów celowanych oraz kompilację składniową zmienionych modułów.
