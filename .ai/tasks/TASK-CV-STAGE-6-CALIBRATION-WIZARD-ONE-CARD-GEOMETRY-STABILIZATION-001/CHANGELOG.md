# CHANGELOG: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-GEOMETRY-STABILIZATION-001

## Wersja 1.0.0 (W toku)

- Przygotowano strukturę zadania i zdefiniowano plan wdrożenia.
- Zaimplementowano rotacyjny zapis klatek debug (max 10 zestawów JPG + JSON) w `app_cv/tarotvision/calibration_debug.py` zintegrowany z `main.py`.
- Przeprowadzono analizę diagnostyczną zebranych logów przy użyciu skryptu `analyze_debug_snapshot.py`.
- Zidentyfikowano przyczynę odrzuceń geometrycznych (przerwane kontury na Canny, brak 4-punktowej wypukłości na profilu adaptacyjnym).
- Zaktualizowano plan wdrożenia o propozycję poprawki parametrycznej.
- **Wdrożono zmianę**: Włączono fallback `use_min_area_rect_fallback=True` dla profilu `adaptive_light` oraz `adaptive_dark` w `card_detection_profiles.py`.
- **Weryfikacja**: Uruchomiono pełną bazę testów jednostkowych (423/423 PASS, brak regresji).
- **Smoke test**: `empty` pozostało czyste, a `one_card` uzyskało `detected_count=1` dla 3/3 próbek, co potwierdza poprawę geometrii.
- **Supervisor decision**: Nie otwierać PR jako gotowego do merge, ponieważ pełny krok `one_card` nadal kończy się `FAIL` przez acceptance/recognition (`accepted_total=1/3`).
- **Zakres dalszych prac**: Zatrzymano dalszy tuning geometrii. Michał potwierdził, że fizyczna talia w smoke teście to Gilded, więc aktywna talia runtime była zgodna. Następny krok to osobny task recognition acceptance.
