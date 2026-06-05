# TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-SAMPLE-CAPTURE-001

## Cel
Wdrożyć bezpieczny krok PR-F3A: podłączenie kontrolowanego zbierania próbek jakościowych z pipeline CV do istniejącej sesji `AutotuneSession`, bez zmiany algorytmów detekcji, bez automatycznego apply i bez `change_detection.py`.

Wizard ma zbierać próbki dla trzech scenariuszy: `empty`, `one_card`, `three_cards`. Celem nie jest jeszcze dobór parametrów, a jedynie:
1. Rozpoznanie, że aktywna jest sesja wizardu.
2. Przy stabilnym snapshotcie zebranie opisu jakościowego sceny.
3. Zapisanie próbki do `AutotuneSession`.
4. Zaktualizowanie licznika `collected_count`.
5. Doprowadzenie sesji do stanu `ready_to_score`, gdy zebrano wymaganą liczbę próbek.

## Zakres
- Opcjonalny callback `autotune_sample_recorder` w `SnapshotFirstPipeline`.
- Przekazanie w `main.py` callbacku do pipeline, który buduje lekki payload próbki, dodaje ją do sesji, loguje i informuje operatora.
- Walidacja zgodności liczby kart ze scenariuszem (`empty` -> 0, `one_card` -> 1, `three_cards` -> 3).
- Ograniczenie liczby próbek do limitu sesji i unikanie zbierania klatka po klatce (wykorzystanie decyzji stabilności snapshotu w pipeline).
- Nowe testy w `test_autotune_pipeline_sample_capture.py`.

## Poza zakresem
- Zmiany w `change_detection.py`, ROI, ROI-first.
- Zmiana algorytmu detekcji i dopasowania kart (ORB/FLANN).
- Zmiana progów rozpoznawania na stałe i automatyczny apply.
- Zapisywanie obrazów jako część próbek.
- Zmiany we frontendzie Studio UI i OBS overlay.

## Kryteria akceptacji
- Bez aktywnej sesji wizardu pipeline działa bez zmian.
- Scenariusz `empty` zbiera próbki tylko przy 0 zaakceptowanych kartach.
- Scenariusz `one_card` zbiera próbki tylko przy 1 zaakceptowanej karcie.
- Scenariusz `three_cards` zbiera próbki tylko przy 3 zaakceptowanych kartach.
- Licznik `collected_count` rośnie do `required_count`.
- `ready_to_score` zmienia się na `true` po zebraniu próbek.
- Zatrzymanie zbierania po `autotune_cancel`.
- Brak obrazów w próbkach i brak zmian w payloadzie kart dla AR.
- Zielone testy automatyczne i CI.
