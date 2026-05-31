# TASK-CV-DIAG-001 — Diagnostyka błędu rozpoznawania kart po wdrożeniu launchera

## 1. Cel i Tło Techniczne

Celem zadania jest ustalenie, dlaczego po uruchomieniu systemu z gałęzi `master` przy użyciu skryptu `start_tarotvision_studio.bat`, system nie rozpoznaje fizycznych kart układanych na stole (konkretnie na przykładzie zgłoszenia operatora o braku detekcji przy wybranej talii "Gilded").

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

> [!IMPORTANT]
> To zadanie ma charakter wyłącznie diagnostyczny (read-only dla kodu). Zabrania się wprowadzania jakichkolwiek modyfikacji w kodzie produkcyjnym CV, frontendu, WebSocketów czy skryptów uruchomieniowych.

### Pliki Dopuszczone do Modyfikacji (Dokumentacja)
* `[MODIFY]` `.ai/TASKS_INDEX.md` (rejestr zadań)
* `[MODIFY]` `.ai/PROJECT_STATE.md` (aktualizacja stanu projektu)
* `[NEW]` `.ai/tasks/TASK-CV-DIAG-001/TASK.md` (niniejszy plik)

---

## 3. Poza Zakresem (Out of Scope)

* Żadnych zmian w kodzie backendu Pythona (`app_cv/`).
* Żadnych zmian w kodzie frontendu Vite (`app_ar/`).
* Żadnych poprawek w pliku `start_tarotvision_studio.bat`.

---

## 4. Kryteria Akceptacji (Acceptation Criteria)

Zadanie uznaje się za ukończone, gdy:
- [x] Przeprowadzono pełną analizę kodu CV pod kątem mechanizmu Snapshot-First oraz kalibracji stołu ArUco.
- [x] Przeanalizowano zrzuty ekranu dostarczone przez operatora pod kątem obecności markerów ArUco oraz wyglądu fizycznej karty.
- [x] Zidentyfikowano podwójną główną przyczynę problemu (Double Root Cause): niedopasowanie bazy talii (Boski vs Gilded) oraz brak pełnej widoczności markerów ArUco (wykrywane 2 z 4).
- [x] Opracowano szczegółowy, 12-punktowy raport diagnostyczny w języku polskim.
- [x] Zaktualizowano indeks zadań `.ai/TASKS_INDEX.md` oraz stan projektu `.ai/PROJECT_STATE.md`.
