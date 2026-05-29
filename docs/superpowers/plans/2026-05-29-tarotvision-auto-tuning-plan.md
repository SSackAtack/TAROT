# Plan Wdrożenia: Konsola Kalibracji & Silnik Auto-Tuningu (Auto-Tuning Engine)

> **Zasada zespołu AI (AGENTS.md):** Każdy kolejny agent przejmujący ten projekt musi zapoznać się z tym planem przed rozpoczęciem prac nad Milestone 3. Plik stworzony i zatwierdzony koncepcyjnie przez Gemini w dniu 2026-05-29.

**Cel:** Budowa interaktywnego panelu strojenia parametrów w przeglądarce (suwaczki HTML) oraz inteligentnego algorytmu samostrojenia (Auto-Tuning Engine), który w 5 sekund automatycznie optymalizuje parametry kamery (AnkerWork C310) i preprocessingu pod kątem aktualnego oświetlenia. Zapewni to stabilną, obiektywną bazę pod przyszłe wdrożenia (np. korekcji perspektywy stołu i sieci YOLO).

---

## Architektura Systemu Samostrojenia

```
+---------------------------------------+
|  Przeglądarka AR (Vite/Three.js)      |
|  - UI: Chowany panel boczny           |
|  - Suwaki: Kontrast, Ostrość, CLAHE   |
|  - Przycisk: "AUTO-KALIBRACJA"        |
+---------------------------------------+
                  ^
                  |  dwukierunkowy JSON (WebSocket: ws://localhost:8765)
                  v
+---------------------------------------+
|  Serwer CV (Python / main.py)         |
|  - Odbiornik parametrów w locie       |
|  - Moduł sterowania kamerą (cap.set)  |
|  - Auto-Tuning Engine: Fitness Eval   |
+---------------------------------------+
```

### 1. Parametry Sterowania w Czasie Rzeczywistym

Panel będzie umożliwiał strojenie trzech krytycznych obszarów systemu:

| Kategoria | Parametr w Kodzie | Zakres | Opis |
| :--- | :--- | :--- | :--- |
| **Sprzęt Kamery** | `CAP_PROP_FOCUS` | `0 - 255` | Ręczne ustawienie ostrości Anker C310 po wyłączeniu Autofokusa. |
| | `CAP_PROP_EXPOSURE` | `-13 do -1` | Czas naświetlania matrycy (blokada i rozjaśnienie obrazu). |
| | `CAP_PROP_CONTRAST` | `0 - 255` | Podbicie kontrastu na poziomie elektroniki kamery. |
| **Preprocessing** | `clahe_clip_limit` | `1.0 - 5.0` | Czułość inteligentnego wzmacniania detali krawędzi. |
| | `canny_threshold1/2`| `10 - 250` | Czułość wykrywania prostokątów kart (algorytm Canny). |
| **Algorytm FSM** | `LOCK_DEAD_ZONE_POS`| `1.5 - 6.0` | Próg czułości ruchu konturu (eliminacja szumu cieni). |
| | `EMA_ALPHA` | `0.05 - 1.0` | Płynność ruchu wirtualnej karty w Three.js. |

---

## Algorytm Auto-Tuning Engine (Koncepcja)

Silnik automatycznego samostrojenia będzie działał w oparciu o **Matematyczną Funkcję Jakości (Fitness Function)**. Michał kładzie jedną kartę referencyjną na stół i klika przycisk. System przez 5 sekund bada kombinacje parametrów, szukając maksimum poniższej funkcji:

$$\text{Jakość} = (S \times 1000) + (P \times 2) - (N \times 15) - (J \times 100)$$

Gdzie:
*   $S$ = Czy karta została pomyślnie i bezbłędnie zidentyfikowana (0 lub 1).
*   $P$ = Liczba dopasowanych stabilnych punktów ORB (chcemy jak najwięcej).
*   $N$ = Liczba fałszywych konturów wykrytych na stole poza kartą (chcemy jak najmniej).
*   $J$ = Poziom drgania (Jitter) ramki w ostatnich 10 klatkach.

### Procedura Auto-Tuningu (Krok po Kroku):
1.  Użytkownik kładzie 1 kartę na stół i klika **„AUTO-KALIBRACJA”**.
2.  System blokuje Autofokus i Autoekspozycję.
3.  Uruchamia się szybki skan (np. *Hill-Climbing* lub *Grid Search* w uproszczonej przestrzeni):
    *   Krok A: Dostrojenie fizycznego kontrastu i jasności kamery, by odciąć kartę od stołu (ocena na podstawie minimalnej liczby fałszywych konturów $N$).
    *   Krok B: Dostrojenie ostrości obiektywu (ocena na podstawie maksymalnej liczby punktów ORB $P$).
    *   Krok C: Dostrojenie CLAHE i Canny dla idealnej gładkości śledzenia (ocena na podstawie minimalnego jitteru $J$).
4.  Wybrana najlepsza konfiguracja zostaje zapisana do pliku `logs/calibration_profile.json`.
5.  Ustawienia są stosowane jako stały profil dla nadchodzącej sesji nagraniowej.

---

## Kamienie Milowe Wdrożenia (Zadania)

### Task 1: Dwuwarstwowy Protokół JSON przez WebSocket
- [ ] Zaprojektować strukturę wiadomości `tuning_update` wysyłanych z frontendu do Pythona:
  ```json
  {"type": "tuning_update", "param": "LOCK_DEAD_ZONE_POS", "value": 3.5}
  ```
- [ ] Zaprojektować strukturę żądania kalibracji:
  ```json
  {"type": "trigger_auto_calibration"}
  ```
- [ ] Zaimplementować bezpieczne parsowanie komunikatów w wątku serwera WebSocket w `main.py` z użyciem blokady wątkowej `status_lock`.

### Task 2: Interfejs UI w Przeglądarce (HTML/CSS/JS)
- [ ] Stworzyć piękny, wysuwany z prawej strony panel boczny (*glassmorphic style* z ciemnym motywem) w aplikacji Vite (`app_ar`).
- [ ] Dodać suwaki dla każdego z parametrów ze wskazaniem aktualnych wartości.
- [ ] Dodać duży, podświetlany przycisk **„Uruchom Auto-Kalibrację”** z animacją wczytywania (spinner) w trakcie testu.
- [ ] Zaimplementować wysyłanie zmian suwaków w czasie rzeczywistym z debouncingiem 50ms (aby nie przeciążyć łącza WebSocket przy gwałtownym przesuwaniu suwaka).

### Task 3: Dynamiczny Odbiornik Parametrów w Pythonie
- [ ] Zaimplementować wątkowo bezpieczne modyfikowanie zmiennych konfiguracyjnych w pętli głównej `main.py`.
- [ ] Dodać obsługę dynamicznej zmiany parametrów kamery przez OpenCV:
  ```python
  cap.set(cv2.CAP_PROP_CONTRAST, nowa_wartosc)
  ```
- [ ] Zaimplementować obsługę wyłączenia / włączenia Autofokusa w locie.

### Task 4: Implementacja Silnika Auto-Kalibracji (Python)
- [ ] Napisać klasę `AutoTuningEngine`, która przejmuje kontrolę nad kamerą na czas kalibracji.
- [ ] Zaimplementować funkcję oceny jakości klatki (Fitness Evaluation).
- [ ] Stworzyć szybki algorytm poszukiwania optimum (np. przeszukiwanie siatki oparte o gradient zbieżności).
- [ ] Zaimplementować zapis wybranego profilu do pliku `calibration_profile.json` oraz automatyczne wczytywanie go przy każdym starcie TarotVision.

---

## Kryteria Akceptacji (Weryfikacja)
*   Suwaki w przeglądarce natychmiast i bez zacięć zmieniają kontrast podglądu w OpenCV.
*   Zmieniony parametr (np. `LOCK_DEAD_ZONE_POS`) w locie wywiera oczekiwany skutek na zachowanie kart bez restartu programu.
*   Kliknięcie przycisku automatycznej kalibracji w ciągu 5 sekund optymalizuje obraz, dając stabilną ramkę i zapisując plik konfiguracyjny.
*   Po zgaszeniu światła i ponownym włączeniu, kliknięcie przycisku automatycznie dostosowuje parametry do nowej jasności otoczenia.
