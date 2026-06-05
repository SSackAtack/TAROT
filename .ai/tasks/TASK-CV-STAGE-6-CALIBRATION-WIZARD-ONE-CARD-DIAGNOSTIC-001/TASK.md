# TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-DIAGNOSTIC-001 — Calibration Wizard One Card & Three Cards Diagnostics Fix

## Cel

Zdiagnozować i naprawić problem realnej kalibracji scenariusza `one_card`, przy którym `empty` przechodzi poprawnie, ale etap „1 karta” nie przechodzi lub nie zbiera próbek. Przy okazji sprawdzić poprawność logiki dla `three_cards`.

## Kontekst

Michał zgłosił realny problem na fizycznym stanowisku:
- `empty` / pusta mata przechodzi OK,
- `one_card` / 1 karta sprawia problem (brak zbierania próbek / blokada na etapie 0/3),
- trzeba od razu sprawdzić, czy `three_cards` / 3 karty nie ma tej samej klasy błędu.

Główną przyczyną jest fakt, że funkcja `record_autotune_sample_from_snapshot(...)` w `app_cv/main.py` odrzuca próbki, jeśli `accepted_count != expected_count`. Gdy system nie jest jeszcze skalibrowany, karta leżąca na stole może zostać wykryta geometrycznie (`detected_count == 1`), ale nie rozpozna się poprawnie (`accepted_count == 0`). Warunek ten uniemożliwia zebranie próbek koniecznych do uruchomienia autotunera, co prowadzi do zakleszczenia (deadlocka).

Dodatkowo wykryto niezgodność nazewnictwa kluczy w próbce:
- `main.py` zapisuje klucz `"detected_count"`,
- `autotune_session.py` i `autotune_scoring.py` odczytują klucz `"candidate_count"`.
Uniemożliwiało to poprawne przejście etapu nawet przy prawidłowym rozpoznaniu karty.

## Zakres

- Modyfikacja `app_cv/main.py`:
  - Zmiana warunku zbierania próbek w `record_autotune_sample_from_snapshot(...)` tak, aby dla scenariuszy z kartami decydowało wykrycie geometryczne (`detected_count == expected_count`), a nie rozpoznanie (`accepted_count == expected_count`).
  - Dodanie brakujących pól do słownika próbki (np. `"candidate_count"`, `"false_positive_count"`, `"geometry_score"`, `"recognition_score"`, `"matching_ms"`) w celu spójności z modułami `autotune_session` i `autotune_scoring`.
- Dodanie / uaktualnienie testów jednostkowych w `app_cv/tests/test_autotune_pipeline_sample_capture.py` w celu pokrycia nowych warunków zbierania próbek.

## Kryteria akceptacji

- Scenariusze `one_card` i `three_cards` prawidłowo zbierają próbki na podstawie wykrycia geometrycznego (odpowiednio 1 i 3 wykryte prostokąty), nawet jeśli karty nie zostały jeszcze rozpoznane.
- Wskaźniki `candidate_count` oraz `false_positive_count` są prawidłowo przekazywane i obliczane.
- Wszystkie testy jednostkowe w projekcie przechodzą pomyślnie.
