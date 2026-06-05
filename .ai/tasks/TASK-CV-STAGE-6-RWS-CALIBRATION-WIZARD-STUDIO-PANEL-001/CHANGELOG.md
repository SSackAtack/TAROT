# Changelog dla TASK-CV-STAGE-6-RWS-CALIBRATION-WIZARD-STUDIO-PANEL-001

Wszystkie istotne zmiany wprowadzone w ramach tego zadania.

## [Niezapisane / W toku]

### Dodano
- Dedykowaną obsługę i renderowanie statusu asystenta kalibracji w sidebarze Studio UI (`app_ar/src/studio/studioConsole.js`).
- Wyświetlanie stanu (z mapowaniem na język polski), scenariusza, próbek, gotowości do oceny, wyniku jakości, flag kroków, a także list komunikatów błędów blokujących, ostrzeżeń i komunikatów dla operatora.
- Premium style dla asystenta kalibracji w pliku `app_ar/studio.css` (kolorystyka zgaszonej miedzi `#d67d3e` oraz kolory statusowe).
- Obiekt fallback `DEFAULT_CALIBRATION_WIZARD_STATUS` zabezpieczający interfejs przed pustym payloadem WebSocket z backendu.

### Zmieniono
- Zaktualizowano interfejs w sekcji "autotune" sidebaru Studio UI, zastępując surowy debugowy panel nowym, ustrukturyzowanym asystentem kalibracji stanowiska.
- Zintegrowano deweloperskie włączanie/wyłączanie przycisków akcji kalibracji w zależności od aktualnego stanu asystenta.
