# TEST REPORT: TASK-CV-STAGE-6-CALIBRATION-WIZARD-ONE-CARD-GEOMETRY-STABILIZATION-001

## Rezultaty testów jednostkowych

`python -m unittest discover -s app_cv/tests -p "test_*.py"` => PASS, 423/423 testów zielonych.

Uwaga: pełny backend suite nie był ponownie uruchamiany w samym kroku smoke testu po decyzji Supervisora. Wynik 423/423 PASS pochodzi z fazy wdrożenia poprawki profili.

## Rezultaty testów fizycznych (Smoke Test)

PHYSICAL_SMOKE — ONE_CARD_GEOMETRY_STABILIZATION

Branch: `task/cv-stage-6-calibration-wizard-one-card-geometry-stabilization-001`
HEAD: `9da3000`
Data: 2026-06-05

### EMPTY

- 3/3: PASS
- false positives: NIE
- warningi HUD: NIE w próbkach empty
- Dowód: `logs/autotune_sessions/autotune_20260605_185950_1780678790932493400_empty_recommendation_ready.json`
- Uwagi: `candidate_count=0`, `accepted_count=0`, `false_positive_total=0`.

### ONE_CARD

- 3/3 jako pełny krok kalibracji: FAIL
- ONE_CARD_GEOMETRY: PASS — `detected_count=1` dla wszystkich 3 próbek
- ONE_CARD_ACCEPTANCE: FAIL — `accepted_total=1/3`
- Najczęstszy `detected_count` przy odrzuceniu: `1`
- Czy `min_area_rect` fallback pomógł: TAK dla geometrii
- Czy HUD / next_action pokazał powód: TAK
- Dowód: `logs/autotune_sessions/autotune_20260605_192956_1780680596924628900_one_card_recommendation_ready.json`
- Uwagi: problem przesunął się poza geometrię. Dalsza diagnostyka powinna dotyczyć zgodności talii i recognition acceptance.

### THREE_CARDS

- NOT_RUN
- Uwagi: nie uruchamiano, ponieważ `one_card` nie przeszedł jako pełny krok kalibracji.

### Konfiguracja talii podczas testu

- `app_ar/public/active_decks.json`: lokalnie ustawione `gilded` (plik poza zakresem taska, nie commitować).
- Runtime backendu: `Zaladowano talie aktywne: ['gilded']`.
- Studio payload/operator: aktywna talia `gilded`.
- Active tuning profile: brak profilu zapisanego w zdarzeniu recommendation (`profile_name=null`).
- Physical deck used in smoke: Gilded (potwierdzone przez Michała po smoke teście).
- Czy fizyczna karta była z tej samej talii, którą system próbował rozpoznawać: TAK.
- Dodatkowy sygnał: jedna próbka została rozpoznana jako `Gilded_08`, confidence/inliers `0.571`.

### Zakres

- `app_ar/public/active_decks.json` został pominięty w commicie: TAK, brak staged files.
- Nie wykonano `git restore app_ar/public/active_decks.json`, żeby nie skasować lokalnej zmiany spoza zakresu.

### Status po smoke teście

`GEOMETRY_VERIFIED_RECOGNITION_FOLLOWUP_REQUIRED`

Nie otwierać PR jako gotowego do merge. Nie kontynuować strojenia geometrii bez nowych dowodów.
