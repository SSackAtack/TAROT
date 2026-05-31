# TASK-CV-RECT-001 — Parameterize card rectangle detection for autotuning

## 1. Cel i Tło Techniczne

Przygotowanie detekcji prostokątów kart do późniejszego autotuningu przez wyprowadzenie parametrów detekcji z twardych stałych i umożliwienie testowania różnych konfiguracji Canny / area ratio / contour mode bez zmiany algorytmu ORB.

Aktualny problem:
* Snapshot-first pipeline ma `card_count = 0`, mimo że obraz kamery jest ostry.
* Karta Boski na ciemnej macie ma słabo widoczną ciemną ramkę.
* Obecny `card_detection.py` używa stałych `CANNY_LOW = 50`, `CANNY_HIGH = 150` oraz `cv2.RETR_EXTERNAL`.
* To utrudnia wykrycie karty na ciemnym tle oraz przy zagnieżdżonych konturach (np. karta na papierze A4).

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

> [!IMPORTANT]
> Obowiązuje ścisła zasada modyfikacji maksymalnie 1–3 plików produkcyjnych na zadanie.

### Pliki Dopuszczone do Modyfikacji
* `[MODIFY]` `card_detection.py` (app_cv/tarotvision/card_detection.py)
* `[MODIFY]` `test_card_detection.py` (app_cv/tests/test_card_detection.py)

---

## 3. Poza Zakresem (Out of Scope)

* Żadnych zmian w `main.py`, `card_recognition.py`, `camera_session.py`, `studioConsole.js`, `studio.css`, skryptach startowych, jsonach manifestu.
* Brak zmian progów ORB, FLANN, RANSAC, payloadów WebSocket, interfejsu Studio.

---

## 4. Kryteria Akceptacji (Acceptance Criteria)

Zadanie uznaje się za ukończone, gdy:
- [x] Zaimplementowano parametryzację `find_card_quads(...)` z pełną kompatybilnością wsteczną.
- [x] Obsłużono mapowanie `contour_mode` ("external", "list", "tree") oraz rzucanie kontrolowanego `ValueError` przy nieznanej wartości.
- [x] Wdrożono sortowanie kandydatów po powierzchni malejąco oraz ograniczanie za pomocą `max_candidates`.
- [x] Dodano funkcję `find_card_quads_with_debug` oraz parametr `return_debug`.
- [x] Testy jednostkowe Pythona (182 testy) przechodzą bezbłędnie.
- [x] Dodano test syntetyczny `test_nested_contour_a4_trap` potwierdzający rozwiązanie problemu zagnieżdżonych konturów.
- [x] Frontend buduje się poprawnie (`npm run build`).
