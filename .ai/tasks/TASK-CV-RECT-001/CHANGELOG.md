# Wykaz Zmian (Changelog) — TASK-CV-RECT-001

## 1. Modyfikowane Pliki Produkcyjne

### `app_cv/tarotvision/card_detection.py`
* Zmodyfikowano sygnaturę `find_card_quads(...)` dodając parametry `canny_low`, `canny_high`, `contour_mode`, `max_candidates` i `return_debug`.
* Zaimplementowano dynamiczne mapowanie `"external"` -> `cv2.RETR_EXTERNAL`, `"list"` -> `cv2.RETR_LIST` i `"tree"` -> `cv2.RETR_TREE`.
* Dodano walidację wejściowego `contour_mode` z rzucaniem kontrolowanego błędu `ValueError`.
* Wprowadzono zbieranie metryk diagnostycznych: `contours_total`, `candidates_after_area`, `candidates_after_quad`.
* Dodano stabilne sortowanie wykrytych quadów po powierzchni w porządku malejącym oraz bezpieczne limitowanie do `max_candidates`.
* Wdrożono funkcję pomocniczą `find_card_quads_with_debug(...)` ułatwiającą offline'ową diagnostykę.

---

## 2. Pliki Testowe i Konfiguracyjne

### `app_cv/tests/test_card_detection.py`
* `test_default_backwards_compatibility`: potwierdza, że domyślne wywołanie `find_card_quads(frame)` bez argumentów działa tak jak dawniej.
* `test_invalid_contour_mode_raises_value_error`: sprawdza, czy przekazanie nieznanej wartości `contour_mode` rzuca właściwy `ValueError`.
* `test_max_candidates_sorting_and_limiting`: weryfikuje sortowanie po powierzchni malejąco i poprawne odrzucanie nadmiarowych kandydatów.
* `test_return_debug_format` i `test_find_card_quads_with_debug_helper`: sprawdzają strukturę słownika diagnostycznego.
* `test_nested_contour_a4_trap`: test syntetyczny zagnieżdżonego konturu karty na ciemnej macie i białej kartce A4. Potwierdza, że tryby `list`/`tree` poprawnie ekstrahują zagnieżdżoną kartę, podczas gdy tryb `external` pobiera wyłącznie zewnętrzny kontur papieru.
