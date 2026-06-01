# GEMINI REPORT: TASK-CV-SNAPSHOT-LIVE-001

* **Status rekomendacji:** **`GREEN`** (Gotowy do scalenia / merge do `master`).
* **Weryfikacja jakości:** 
  * Backend: Pomyślny test na żywo z fizyczną kamerą USB (AnkerWork C310), kompletną talią Gilded na ciemnej maty oraz udane wyuczenie tła (Background Difference).
  * Frontend: Vite build przechodzi w 100% poprawnie po modyfikacjach.

---

## 1. Wykryte ryzyka i problemy (Do wglądu dla ChatGPT Supervisor)

1. **Szum ArUco z rewersu kart:** Wzory geometryczne słońca w rogach rewersu kart Gilded/Światło i Cień bywają błędnie interpretowane przez ArUco jako marker `37`. Ponieważ markery kalibracji stołu mają sztywny zakres `10-13`, detektor ArUco powinien ignorować i odfiltrowywać wszelkie detekcje markerów spoza tego zestawu, aby nie resetować kalibracji stołu.
2. **Czułość na odblaski (Zabrudzenia krawędzi):** Przezroczysta taśma klejąca na Siódemce Kielichów dała niebieski błysk, co zniekształciło kontur. W obecnym kodzie wymóg idealnego czworokąta konturu (`len(approx) == 4`) natychmiast odrzucił tę kartę.

---

## 2. REKOMENDACJA KOLEJNEGO ZADANIA: "Pancerna detekcja kart pod odblaski" (Fallback Cascade)

Proponujemy zlecenie kolejnego zadania modelowi **Codex** w celu uodpornienia detekcji krawędzi kart na odblaski i taśmy klejące poprzez wdrożenie geometrycznego fallbacku (4 ➔ 3 ➔ 2 wierzchołki).

### Specyfikacja techniczna dla Codexa:

Modyfikacja algorytmu detekcji w `app_cv/tarotvision/card_detection.py` oraz profilu `background_diff` w `card_detection_profiles.py`:

#### Krok A: Dopasowanie obróconego prostokąta (`minAreaRect`)
Zamiast rygorystycznego warunku `len(approx) == 4` na konturze:
* Dla konturów, które mają `len(approx) >= 4` (np. 5, 6 lub 8 wierzchołków z powodu flary/taśmy), należy dopasować minimalne pudełko obrócone:
  ```python
  rect = cv2.minAreaRect(contour)
  box = cv2.boxPoints(rect)
  box = np.int0(box)
  ```
* Jeżeli proporcje tak wyznaczonego prostokąta `box` odpowiadają proporcjom karty tarota (`is_card_aspect_ratio`), przyjmujemy ten `box` jako idealną detekcję o 4 wierzchołkach!

#### Krok B: Fallback dla 3 wierzchołków (Rekonstrukcja geometryczna)
Jeśli odblask całkowicie "ściął" jeden narożnik i `approxPolyDP` zwrócił dokładnie **3 wierzchołki** (A, B, C), z których AB i BC są prostopadłymi bokami karty:
* Obliczamy brakujący czwarty wierzchołek D przy założeniu, że karta tworzy równoległobok w przestrzeni 2D (na sprostowanym stole warped):
  ```python
  D = A + (C - B)  # Matematyczne wyznaczenie brakującego narożnika
  ```
* Sprawdzamy czy kąty i proporcje tak odtworzonego czworokąta ABCD odpowiadają karcie tarota.

#### Krok C: Fallback dla 2 wierzchołków (Wyznaczanie z jednego boku)
Jeśli wykryto tylko **2 sąsiednie wierzchołki** (jedną wyraźną krawędź karty o długości $L$):
* Wiemy, że na sprostowanym stole (warped frame) kierunek pionowy jest stały.
* Wyznaczamy kierunek prostopadły do krawędzi w głąb karty (sprawdzamy na masce binarnej tła, po której stronie linii leży jasny obszar).
* Przesuwamy wierzchołki wzdłuż prostopadłych wektorów o długość $H = L \times 1.72$, odtwarzając brakujące 2 wierzchołki!
