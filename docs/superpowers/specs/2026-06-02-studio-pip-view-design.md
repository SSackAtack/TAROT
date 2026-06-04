# Studio PiP View Design

## Stan aktualny

Studio ma centralny podglad kamery CV w `.studio-preview-overlay` oraz przyciski scen `Stol`, `WOW Mode`, nieaktywny `PiP (Portret)` i tryb automatycznego rezysera. Widok wirtualnego stolu jest nadal renderowany przez glowny canvas aplikacji, ale Studio zaslania go duzym podgladem kamery.

## Cel

Dodac w Studio trzy tryby podgladu:

- `Stol`: glowny widok to wirtualny stol, bez duzego podgladu kamery.
- `Kamera`: glowny widok to live camera preview.
- `PiP`: glowny widok to wirtualny stol, a kamera jest mala ramka PiP w prawym dolnym rogu obszaru preview.

## Architektura

Zmiana pozostaje frontend-only. `studioConsole.js` utrzyma lokalny stan trybu preview i bedzie przelaczal klasy CSS na `.studio-preview-overlay`. Nie zmieniamy backendowego `director_scene`, bo to nie jest scena rezysera ani stan OBS; to lokalny sposob kontroli widoku operatorskiego.

## Komponenty

- `studioConsole.js`: dodaje przyciski `Stol`, `Kamera`, `PiP`, funkcje `setStudioPreviewMode()` i event handlers.
- `studio.css`: definiuje layouty `table`, `camera`, `pip`.
- `test_camera_controls_static.py`: statyczny kontrakt obecnosci trybow i funkcji przelaczania.

## Testowanie

- Statyczny test UI musi potwierdzic teksty/atrybuty `data-preview-mode="table|camera|pip"` oraz `setStudioPreviewMode`.
- Build Vite musi przejsc bez bledow; istniejace ostrzezenia chunkow sa akceptowalne.
