# Stan Prac — TASK-CV-RECT-001

## 1. Status Ogólny
* **Status:** `DONE`
* **Realizator (Owner):** Gemini
* **Gałąź Git:** `task/cv-rect-001-parameterize-card-detection`

---

## 2. Co Zostało Zrobione (Completed)
- [x] Przywrócono czysty stan master w lokalnym repozytorium (usunięto niekontrolowane eksperymenty w `main.py` itp.).
- [x] Utworzono dedykowaną gałąź roboczą `task/cv-rect-001-parameterize-card-detection`.
- [x] Zaimplementowano parametryzację `find_card_quads(...)` w `app_cv/tarotvision/card_detection.py`.
- [x] Dodano walidację trybu konturu (`contour_mode`) rzucającą kontrolowany `ValueError`.
- [x] Zaimplementowano sortowanie po powierzchni malejąco i limitowanie kandydatów `max_candidates`.
- [x] Wdrożono diagnostyczny format debugujący za pomocą `return_debug` i funkcji pomocniczej `find_card_quads_with_debug`.
- [x] Rozbudowano `app_cv/tests/test_card_detection.py` o testy kompatybilności wstecznej, walidacji parametrów, sortowania/limitowania, formatu debugowania oraz test syntetyczny zagnieżdżonego konturu `test_nested_contour_a4_trap`.
- [x] Pomyślnie uruchomiono i zweryfikowano wszystkie 182 testy backendu CV (wszystkie zielone).
- [x] Pomyślnie zweryfikowano kompilację produkcyjną frontendu AR w Vite.

---

## 3. Co Pozostało do Zrobienia (Remaining)
- [ ] Merge do gałęzi głównej po akceptacji (Code Review / ChatGPT Supervisor).
