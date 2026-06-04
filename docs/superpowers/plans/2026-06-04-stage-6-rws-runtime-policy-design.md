# Stage 6 RWS Runtime Policy Design

## Current Offline Evidence
W toku offline benchmarków (paczki 8 próbek RWS) wyciągnięto następujące wnioski techniczne:
- Surowa detekcja / rozpoznawanie ORB jest podatne na błędy w warunkach silnych odblasków (glare) na kartach (dokładność Top-1 na całym zestawie to 50%).
- Bramka jakościowa (Quality Gate) w 100% chroni system przed błędnym rozpoznaniem kart z odblaskami, blokując je i kierując do ponownego przechwycenia (`RETRY_CAPTURE`) lub decyzji reżyserskiej (`MANUAL_REVIEW`).
- Dokładność podzbioru zaakceptowanego automatycznie (`ACCEPT_FOR_IDENTIFICATION`) wynosi 100% (4 na 4 próbki bezodblaskowe).

---

## Design Goal
Zaprojektowanie bezpiecznej dla widza i spójnej dla operatora polityki zachowania systemu (Runtime Policy) w pętli produkcyjnej dla różnych decyzji bramki jakościowej: `ACCEPT_FOR_IDENTIFICATION`, `RETRY_CAPTURE`, `MANUAL_REVIEW` oraz `EXTRACTION_FAILED`.

---

## Non-Goals
- Implementacja kodu runtime backendu lub frontendu.
- Zmiana struktury payloadów WebSocket w bieżącej sesji.
- Modyfikacja progów detekcji i jakość (thresholds) w kodzie produkcyjnym.

---

## Decision Matrix

| Decyzja Bramki Jakościowej | Działanie Systemu | Wpływ na AR/OBS | Wpływ na Panel Reżysera |
|---|---|---|---|
| **ACCEPT_FOR_IDENTIFICATION** | Wywołaj ORB i zweryfikuj zaufanie (confidence). | Aktualizuj nakładkę AR po histerezie stabilności. | Pokazuje zielony status i zidentyfikowaną kartę. |
| **RETRY_CAPTURE** | Wyślij żądanie nowego snapshotu (max 2 próby). | Zachowaj poprzedni stabilny stan nakładki AR (brak migotania). | Pokazuje ostrzeżenie o odblaskach/jakości i licznik prób. |
| **MANUAL_REVIEW** | Zatrzymaj autodetekcję, czekaj na decyzję. | Zachowaj poprzedni stabilny stan nakładki AR (brak zmian). | Prezentuje podgląd cropa, powody odrzucenia i Top-3 kandydatów. |
| **EXTRACTION_FAILED** | Pomiń ORB, zgłoś błąd i powtórz snapshot lub eskaluj. | Zachowaj poprzedni stabilny stan nakładki AR. | Komunikat: brak detekcji konturu karty na macie. |

---

## Pipeline Policy
Rekomendowana kolejność przetwarzania nowej klatki w pętli CV (ruchomy snapshot):
1. **Pobranie Snapshotu** (kadr z kamery fizycznej).
2. **Detekcja i ekstrakcja prostokąta karty (Crop/Deskew/Normalize)**.
   - *JEŚLI ekstrakcja nie powiedzie się:* Skieruj natychmiast na ścieżkę **EXTRACTION_FAILED** (pomiń ORB).
3. **Bramka Jakościowa (Quality Gate)**.
   - Ocena odblasków, flar, kontrastu i poziomu szczegółów.
   - *JEŚLI wynik to RETRY_CAPTURE:* Skieruj na ścieżkę automatycznej retencji snapshotu.
   - *JEŚLI wynik to MANUAL_REVIEW:* Skieruj do kolejki decyzji operatora.
4. **Rozpoznanie ORB** (wywoływane wyłącznie dla próbek ze statusem `ACCEPT_FOR_IDENTIFICATION`).
5. **Polityka Zaufania (Confidence Policy)**.
   - Sprawdzenie minimalnego zaufania (confidence score/gap).
6. **Aktualizacja Stanu AR/OBS** po potwierdzeniu stabilności (histereza czasowa).

---

## State Model
Projektowany model stanu sesji w `tarotvision/status/status_store.py`:
- `last_confirmed_state` (dict): Ostatni w pełni zweryfikowany i wyświetlany na nakładce AR stan kart (bezpieczny dla widza).
- `candidate_state` (dict): Tymczasowy stan karty z aktualnej klatki, oczekujący na histerezę stabilności.
- `pending_review_state` (dict): Stan wstrzymanej próbki czekającej na reakcję operatora (zawiera crop, Top-3 kandydatów, powody bramki).
- `retry_count` (int): Licznik automatycznych snapshotów w ramach jednej detekcji (zapobiega nieskończonym pętlom).
- `quality_reasons` (list): Przyczyny odrzucenia próbki przez bramkę jakościową.

---

## Operator Policy (Decyzje Operatora w MANUAL_REVIEW)
W przypadku eskalacji do `MANUAL_REVIEW`, operator ma do wyboru akcje:
1. **CONFIRM_TOP1**: Ręczne zatwierdzenie kandydata Top-1 zwróconego przez ORB.
2. **SELECT_FROM_TOP3**: Wybór innej karty z listy Top-3 kandydatów.
3. **RETRY_CAPTURE**: Ręczne wymuszenie wykonania nowej klatki (np. po poprawieniu karty na macie).
4. **MARK_UNKNOWN**: Oznaczenie karty jako nieznana (brak renderu AR).
5. **REJECT_SAMPLE**: Odrzucenie próbki i wyczyszczenie slotu karty.

---

## AR / OBS Policy (Zachowanie Nakładek Wizualnych)
Nadrzędnym celem jest **brak migotania (flickering) i brak błędnych wskazań** dla widzów na streamie OBS:
- **Podczas ACCEPT**: Aktualizacja renderu AR następuje dopiero po potwierdzeniu stabilności (np. ta sama karta zidentyfikowana w 2 kolejnych snapshotach w określonym oknie czasowym).
- **Podczas RETRY_CAPTURE**: Nakładka AR nie jest usuwana ani modyfikowana. Widz widzi poprzedni stabilny stan, a w tle system cicho próbuje poprawić klatkę.
- **Podczas MANUAL_REVIEW**: Nakładka AR pozostaje stabilna na poprzednim potwierdzonym wyniku. Panel operatora pulsuje na czerwono/miedziano, informując o konieczności podjęcia decyzji.
- **Podczas EXTRACTION_FAILED**: Publiczny AR nie ulega zmianie. Zapobiega to usuwaniu nakładek przy chwilowym zasłonięciu karty dłonią przez operatora.

---

## Failure Handling (Obsługa EXTRACTION_FAILED)
Jeśli system nie wykryje konturu karty na macie:
- ORB nie jest uruchamiany.
- Licznik `retry_count` rośnie o 1.
- Jeśli `retry_count <= 2`: Wykonywany jest kolejny snapshot z kamery.
- Jeśli `retry_count > 2`: Następuje eskalacja do statusu `MANUAL_REVIEW` z powodem `EXTRACTION_FAILED`. Operator widzi komunikat: *"Karta niewykryta. Skoryguj położenie karty na macie i kliknij Ponów Snapshot"*.

---

## Runtime Safety Rules
1. **Zasada Stabilności**: Nigdy nie wysyłaj niepewnego ID karty na nakładkę AR.
2. **Zasada Trwałości**: Nie usuwaj aktualnego renderu AR z powodu tymczasowego odrzucenia klatki przez bramkę jakości (np. podczas ruchu ręką nad matą).
3. **Zasada Kontroli Reżyserskiej**: Każde automatycznie odrzucone rozpoznanie po wyczerpaniu retries musi trafić do operatora (nie może cicho zniknąć ani pokazać losowej karty).
4. **Zasada Wydajności**: Nigdy nie uruchamiaj algorytmu deskew / ORB na pustych lub czarnych obrazach (po nieudanej ekstrakcji).
5. **Zasada Priorytetu Bezpieczeństwa**: Lepsze jest wstrzymanie aktualizacji (manual review) niż wyświetlenie błędnej karty tarotowej widzom.

---

## Future Implementation Tasks (Kolejne Kroki Techniczne)
1. Rozbudowa statusu WebSocket o metadane bramki jakościowej (`quality_gate_decision`, `reasons`).
2. Implementacja logiki ponawiania snapshotów w `snapshot_first.py` z uwzględnieniem `retry_count`.
3. Dodanie widoku podglądu cropa i Top-3 kandydatów w konsoli Studio Console (`app_ar/src/studio/`).
4. Wdrożenie obsługi komend operatora (`confirm_card`, `select_card_candidate`).

---

## Open Questions
- Czy histereza stabilności AR powinna być konfigurowalna z poziomu konsoli operatorskiej, czy na stałe zaszyta w kodzie backendu (np. 1.5s)?
- Czy w przypadku `RETRY_CAPTURE` operator powinien widzieć dynamicznie odświeżany licznik klatek w tle, czy tylko finalny status po zakończeniu retries?
