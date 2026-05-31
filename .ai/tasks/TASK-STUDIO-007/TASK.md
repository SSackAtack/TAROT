# TASK-STUDIO-007 — Port-aware Studio Launcher Hardening

## 1. Cel i Tło Techniczne

Dedykowany launcher Konsoli Studio (`start_tarotvision_studio.bat`) uruchamia serwer deweloperski Vite, który domyślnie nasłuchuje na porcie `5173`. Przeglądarka jest automatycznie otwierana pod adresem `http://localhost:5173/?studio=1`. 
Jeśli port `5173` jest zajęty przez inną wiszącą w tle sesję deweloperską (np. proces Node/Vite, który nie został prawidłowo zamknięty), Vite automatycznie przełącza się na kolejny wolny port (np. `5174`). W efekcie przeglądarka otwiera pusty adres `localhost:5173` lub starą nieaktualną instancję, co uniemożliwia operatorowi połączenie z nowo uruchomioną sesją i powoduje błędy WebSockets.

Celem tego zadania jest utwardzenie pliku launchera (`start_tarotvision_studio.bat`) poprzez dodanie mechanizmu detekcji zajętości portu `5173` przez PowerShell przed startem procesów. Launcher da operatorowi pełną kontrolę i wybór dalszego postępowania (automatyczne ubicie starego procesu, kontynuacja na własne ryzyko lub bezpieczne przerwanie działania).

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

### Pliki Dopuszczone do Modyfikacji
* `[MODIFY]` `start_tarotvision_studio.bat` (E:\Antigravity\Projekty\TAROT\start_tarotvision_studio.bat)
* `[MODIFY]` `.ai/TASKS_INDEX.md` (E:\Antigravity\Projekty\TAROT\.ai\TASKS_INDEX.md)
* `[NEW]` Pliki w `.ai/tasks/TASK-STUDIO-007/`

---

## 3. Poza Zakresem (Out of Scope)

* Brak jakichkolwiek modyfikacji kodu frontendowego JavaScript/TypeScript (`app_ar/src/`).
* Brak modyfikacji stylów CSS (`app_ar/studio.css`).
* Brak modyfikacji backendu CV (`app_cv/`).
* Brak modyfikacji protokołu WebSocket lub formatu payloadu.
* Brak modyfikacji głównego launchera operatorskiego `start_tarotvision.bat` (skupiamy się wyłącznie na Studio Console).

---

## 4. Kryteria Akceptacji (Acceptation Criteria)

Zadanie uznaje się za ukończone, gdy:
- [ ] Launcher `start_tarotvision_studio.bat` przed uruchomieniem serwerów deweloperskich sprawdza status portu `5173` za pomocą zintegrowanego skryptu PowerShell.
- [ ] W przypadku wykrycia zajętości portu, wyświetlany jest czytelny, jasnoczerwony baner ostrzegawczy z opisem konsekwencji (otwarcie błędnego portu w przeglądarce).
- [ ] Launcher prezentuje operatorowi menu wyboru z 3 opcjami:
  1. Automatyczne zamknięcie (ubicie) wiszącego procesu Node/Vite na porcie 5173 i kontynuacja.
  2. Ignorowanie i kontynuacja (na własne ryzyko).
  3. Bezpieczne wyjście i anulowanie startu (domyślnie).
- [ ] Jeśli port `5173` jest całkowicie wolny, system przechodzi do standardowej procedury startowej bez pokazywania ostrzeżeń i dodatkowych pytań.
- [ ] Zarejestrowano zadanie w `.ai/TASKS_INDEX.md` i zaktualizowano status po wdrożeniu.
