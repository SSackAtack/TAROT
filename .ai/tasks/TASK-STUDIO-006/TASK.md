# TASK-STUDIO-006 — Diagnostyka CV Health Minimal & Dedykowany Launcher Studio

## 1. Cel i Tło Techniczne

Konsola reżyserska Studio (`?studio=1`) ma służyć jako zaawansowane, lecz przejrzyste i stabilne środowisko pracy dla operatora. W tym celu w sekcji "Diagnostyka CV Health" chcemy wdrożyć minimalistyczny podgląd (CV Health minimal), który:
- Pokazuje najważniejsze wskaźniki (FPS, Cards, Stable Ms, Snapshot).
- Dynamicznie wyświetla ostatnie wykryte ostrzeżenie (np. słabe oświetlenie, brak kamery, itp.) przesyłane w locie przez WebSocket z backendu w tablicy `warnings`.
- Pozostaje wolny od surowych, długich logów deweloperskich, aby nie przytłaczać operatora.

Dodatkowo w celu optymalizacji uruchamiania systemu wdrożymy dedykowany launcher `start_tarotvision_studio.bat`, który uruchamia serwery backendu i frontendu oraz automatycznie otwiera przeglądarkę bezpośrednio w trybie reżyserskim Studio (`http://localhost:5173/?studio=1`).

---

## 2. Rygorystyczny Zakres Modyfikacji (Scope)

> [!IMPORTANT]
> Obowiązuje ścisła zasada modyfikacji maksymalnie 1–3 plików produkcyjnych na zadanie (chyba że zatwierdzono Human Override).

### Pliki Dopuszczone do Modyfikacji
* `[MODIFY]` `app_ar/src/studio/studioConsole.js` (E:\Antigravity\Projekty\TAROT\app_ar\src\studio\studioConsole.js)
* `[MODIFY]` `app_ar/studio.css` (E:\Antigravity\Projekty\TAROT\app_ar\studio.css)
* `[NEW]` `start_tarotvision_studio.bat` (E:\Antigravity\Projekty\TAROT\start_tarotvision_studio.bat)
* `[MODIFY]` `.ai/TASKS_INDEX.md` (E:\Antigravity\Projekty\TAROT\.ai\TASKS_INDEX.md)

---

## 3. Poza Zakresem (Out of Scope)

* Brak zmian w algorytmach OpenCV i logice detekcji w backendzie CV (`app_cv`).
* Brak zmian w protokole WebSocket lub strukturze status payloadu.
* Brak modyfikacji widoku operatorskiego `?operator=1` ani głównego AR overlay.
* Brak modyfikacji TASK-DECK-010 ani zmian w pliku `active_decks.json`.

---

## 4. Kryteria Akceptacji (Acceptation Criteria)

Zadanie uznaje się za ukończone, gdy:
- [ ] Sekcja "Diagnostyka CV Health" w Studio zawiera premium kontener ostrzeżeń (`studio-cv-warning-box`).
- [ ] Ostrzeżenie jest widoczne tylko wtedy, gdy w payloadzie WebSocket w tablicy `warnings` znajduje się przynajmniej jedno aktywne ostrzeżenie z backendu (wtedy wyświetlamy ostatnie z nich).
- [ ] Kontener ostrzeżeń ma premium ciemnomiedzianą i czerwoną kolorystykę z łagodnym pulsowaniem i nienagannym kontrastem.
- [ ] Stworzono skrót startowy `start_tarotvision_studio.bat` w głównym katalogu, który pomyślnie otwiera URL `?studio=1`.
- [ ] Frontend buduje się poprawnie (npm run build).
- [ ] Testy jednostkowe backendu Pythona przechodzą bezbłędnie.
- [ ] Raport z testów został dołączony do pliku `TEST_REPORT.md` w katalogu zadania.
