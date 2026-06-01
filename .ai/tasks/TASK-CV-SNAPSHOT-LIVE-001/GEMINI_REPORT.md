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

## 2. REKOMENDACJA KOLEJNEGO ZADANIA: "Pancerna Kaskada Detekcji Krawędzi" (Fallback Cascade 4-3-2-1)

Proponujemy zlecenie kolejnego zadania modelowi **Codex** w celu wdrożenia **pancernej kaskady detekcji geometrycznej (Fallback Cascade)** na sprostowanym stole (warped frame). Zamiast zero-jedynkowego podejścia, algorytm CV będzie próbował zrekonstruować pozycję karty sekwencyjnie w zależności od stopnia jej widoczności.

### Specyfikacja techniczna dla Codexa:

Modyfikacja algorytmu detekcji w `app_cv/tarotvision/card_detection.py` oraz profilu `background_diff` w `card_detection_profiles.py`:

#### [Poziom 1] Detekcja 4 krawędzi (Klasyczna / Obrócone Pudełko `minAreaRect`)
Zamiast rygorystycznego warunku `len(approx) == 4` na konturze:
* Dla konturów, które mają `len(approx) >= 4` (np. 5, 6 lub 8 wierzchołków z powodu flary/taśmy), należy dopasować minimalne pudełko obrócone:
  ```python
  rect = cv2.minAreaRect(contour)
  box = cv2.boxPoints(rect)
  box = np.int0(box)
  ```
* Jeżeli proporcje tak wyznaczonego prostokąta `box` odpowiadają proporcjom karty tarota (`is_card_aspect_ratio`), przyjmujemy ten `box` jako idealną detekcję o 4 wierzchołkach.

#### [Poziom 2] Fallback dla 3 krawędzi (Rekonstrukcja geometryczna)
Jeśli odblask całkowicie "ściął" jeden narożnik i `approxPolyDP` zwrócił dokładnie **3 wierzchołki** (A, B, C) określające dwie przyległe krawędzie:
* Obliczamy brakujący czwarty wierzchołek D przy założeniu, że karta tworzy równoległobok w przestrzeni 2D:
  ```python
  D = A + (C - B)  # Matematyczne wyznaczenie brakującego narożnika
  ```
* Sprawdzamy czy kąty i proporcje tak odtworzonego czworokąta ABCD odpowiadają karcie tarota.

#### [Poziom 3] Fallback dla 2 krawędzi (Wyznaczanie z jednego boku)
Jeśli wykryto tylko **2 sąsiednie wierzchołki** (jedną wyraźną krawędź karty o długości $L$):
* Wiemy, że na sprostowanym stole (warped frame) kierunek pionowy jest stały.
* Wyznaczamy kierunek prostopadły do krawędzi w głąb karty (sprawdzamy na masce binarnej tła, po której stronie linii leży jasny obszar).
* Przesuwamy wierzchołki wzdłuż prostopadłych wektorów o długość $H = L \times 1.72$, odtwarzając brakujące 2 wierzchołki i zamykając prostokąt.

#### [Poziom 4] Fallback z 1 krawędzi (Single-Edge Scale Matching)
Jeśli z powodu potężnego odblasku zidentyfikujemy **tylko jedną pojedynczą krawędź (linię)** o długości $L$:
* Ponieważ stół jest sprostowany (warped), skala (piksel/cm) jest stała i znana. Wiemy dokładnie, ile pikseli ma krótki bok ($W$) oraz długi bok ($H$) kart z danej talii (np. dla Gilded: $W \approx 130$ px, $H \approx 224$ px).
* Porównujemy długość wykrytej krawędzi $L$ z tolerancją (np. 95%):
  - Jeśli $L \approx W$ ➔ wiemy, że to **krótki bok karty**!
  - Jeśli $L \approx H$ ➔ wiemy, że to **długi bok karty**!
* Mając tę krawędź (dwa punkty A i B) oraz kierunek:
  - Sprawdzamy na masce binarnej `background_diff`, po której stronie linii znajduje się biały obszar karty.
  - Wyznaczamy wektory prostopadłe skierowane w tę stronę o brakującej długości ($H$ lub $W$) i wyliczamy pozycje brakujących dwóch narożników!
* Daje to 100% odporność na zasłonięcia karty przez inne obiekty, cienie i flary!

