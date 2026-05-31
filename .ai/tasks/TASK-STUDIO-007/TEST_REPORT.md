# TASK-STUDIO-007 — Raport z Testów

## 1. Testy Automatyczne
*Zgodnie ze specyfikacją zadania, nie modyfikowano kodu źródłowego frontendu deweloperskiego (JS/CSS) ani backendu CV (Python). W związku z tym testy automatyczne nie były wymagane dla tego zadania. Pomimo tego potwierdzono, że istniejące testy jednostkowe CV przechodzą bezbłędnie.*

---

## 2. Raport z Wykonania Testów Manualnych

Przeprowadzono rygorystyczne testy manualne weryfikujące poprawność obsługi portu w systemie Windows.

### Krok 1: Weryfikacja przy WOLNYM porcie 5173
- **Scenariusz**: Uruchomienie `start_tarotvision_studio.bat` w czystym środowisku (brak działających procesów Node/Vite).
- **Status**: `PASS`
- **Wynik**: Launcher wypisuje `[OK] Port 5173 jest wolny. Kontynuuję...` i natychmiastowo przechodzi do standardowego podnoszenia serwerów AR/CV bez żadnych przerw ani pytań do operatora.

### Krok 2: Weryfikacja przy ZAJĘTYM porcie 5173
- **Scenariusz**: Symulacja zajętości portu (uruchomienie innego procesu nasłuchującego na porcie 5173) i wywołanie `start_tarotvision_studio.bat`.
- **Status**: `PASS`
- **Wynik**: Launcher wykrywa kolizję portów, zmienia kolor konsoli na jasnoczerwony (`color 0C`), prezentuje baner ostrzegawczy o konsekwencjach uruchomienia i daje operatorowi 3 opcje wyboru.

### Krok 3: Automatyczne ubicie wiszącego procesu (Wybór "1")
- **Scenariusz**: Po wykryciu zajętości portu, operator wybiera opcję `1`.
- **Status**: `PASS`
- **Wynik**: Skrypt PowerShell z sukcesem identyfikuje identyfikator procesu (`OwningProcess`) nasłuchującego na porcie 5173, wymusza jego zatrzymanie (`Stop-Process -Force`), odczekuje 2 sekundy i pomyślnie kontynuuje normalne uruchamianie TarotVision Studio na nowo uwolnionym porcie.

### Krok 4: Kontynuacja na własną odpowiedzialność (Wybór "2")
- **Scenariusz**: Po wykryciu zajętości, operator wybiera opcję `2`.
- **Status**: `PASS`
- **Wynik**: Launcher ignoruje ostrzeżenie, przywraca standardowy kolor deweloperski i kontynuuje start serwerów. Przeglądarka otwiera `5173` (który wyświetli starą sesję), a nowy Vite startuje na `5174` zgodnie z oczekiwaniem.

### Krok 5: Bezpieczne wyjście i anulowanie (Wybór "3" / Domyślny)
- **Scenariusz**: Operator wybiera opcję `3` lub po prostu naciska Enter bez podawania wartości.
- **Status**: `PASS`
- **Wynik**: Launcher bezpiecznie zatrzymuje działanie, wypisuje `Uruchamianie przerwane przez operatora` i po naciśnięciu dowolnego klawisza czysto zamyka konsolę bez otwierania jakichkolwiek serwerów czy przeglądarki.
