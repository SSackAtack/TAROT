Review Task STUDIO-006: Diagnostyka CV Health Minimal i Dedykowany Launcher Studio
Base: master (3e40b13809480572d5c4b8ba2e482e1f4ba55831)
Head: task/studio-006-warning-hud-launcher (current branch)

Zakres:
- Implementacja dynamicznego wyświetlania ostrzeżeń CV w czasie rzeczywistym w Konsoli Studio (?studio=1) na podstawie WebSocket payloadu z tablicą `warnings`.
- Zaprojektowanie i wdrożenie premium stylizacji ostrzeżeń z soft, miedziano-czerwonym pulsowaniem borderów (spójnym z brandingiem zgaszonej miedzi `#d67d3e`).
- Utworzenie dedykowanego launchera Windows `start_tarotvision_studio.bat` w głównym katalogu projektu do błyskawicznego podnoszenia sesji reżyserskiej.

Weryfikacja wykonana przez Gemini:
- cd app_cv && python -m unittest discover tests => PASS (176 tests OK)
- cd app_ar && npm run build => PASS (Bundling completed successfully without errors)

Pliki zmienione:
- `app_ar/src/studio/studioConsole.js`
- `app_ar/studio.css`
- `start_tarotvision_studio.bat`
- `.ai/TASKS_INDEX.md`

Znane ryzyka / decyzje do review:
- **Residual Risk: LOW**
  - *Kolizja portów*: Launcher w ciemno zakłada start Vite na porcie 5173. Jeśli port jest zajęty przez inną wiszącą sesję, Vite przełączy się na 5174, a launcher i tak otworzy 5173. Środek zaradczy: standardowe zwolnienie portów/zamknięcie procesów w tle.
  - *Zachowanie komendy start*: Launcher używa systemowego `start` do otwarcia przeglądarki. W przypadku nietypowej domyślnej przeglądarki bez wsparcia dla nowoczesnych standardów HTML5/WebSockets, Studio Console może napotkać błędy. Środek zaradczy: używanie nowoczesnej przeglądarki (np. Chrome/Edge/Firefox).
  - *Założenie o typie danych warnings*: Logika frontendu zakłada, że `data.warnings` to tablica surowych napisów (stringów). Gdyby w przyszłości backend zmienił strukturę warnings na obiekty, w HUD wyświetli się surowy `[object Object]`. Zmiana ta jest jednak poza zakresem i backend CV pozostaje niezmieniony.

