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
- Brak. Zakres jest w 100% bezpieczny i odizolowany od mechanizmów CV OpenCV/ORB oraz widoku operatorskiego.
