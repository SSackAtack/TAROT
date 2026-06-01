# TEST REPORT: TASK-CV-SNAPSHOT-LIVE-001

* **Data testu:** 2026-06-01
* **Operator (Tester):** Michał
* **Asystent AI:** Gemini 3.5 Flash (High)
* **Gałąź testowa:** `codex/snapshot-first-recognition-hardening`

---

## 1. Przebieg i Wyniki Scen Testowych

| Lp. | Scena | Status | Szczegóły / Obserwacje |
| :--- | :--- | :--- | :--- |
| 1 | **Pusta mata** | `PASS` | Brak false positives (system trzymał pusty stan). |
| 2 | **1 jasna karta** | `PASS` | Szybka detekcja i stabilne rozpoznanie. |
| 3 | **1 ciemna karta (Gilded) na ciemnej macie** | `PASS` | **Kluczowy sukces!** Początkowo brak detekcji z powodu zlewających się krawędzi. Po wdrożeniu i kliknięciu przycisku **"Ucz maty (Capture)"** (Background Difference), system natychmiast poprawnie wykrył i bezbłędnie zidentyfikował **Dziesiątkę Kielichów (`Gilded_73`)**. |
| 4 | **Odporność na odblaski (Siódemka Kielichów z taśmą)** | `FAIL` | Karta Siódemka Kielichów miała przyklejoną przezroczystą folię dającą silny odblask w obiektyw kamery, co ucięło kontur i zablokowało detekcję 4 wierzchołków. Wykazało to potrzebę poluzowania rygoru detekcji prostokąta. |
| 5 | **Szum kalibracji (błędny marker 37)** | `RESOLVED` | Wykryto, że geometryczne wzory słońca/mandali na **rewersie karty Gilded** były błędnie interpretowane przez algorytm ArUco jako marker o ID `37`. Po usunięciu odwróconej karty z maty, kalibracja stołu wzrosła z 17% do **78.4%** i stała się w pełni stabilna. |
| 6 | **Ruch ręką nad matą** | `PASS` | Bramka snapshot-first poprawnie wykrywała ruch (`stable 0 ms`, stan `holding_last_good`) i wyzwalała analizę dopiero po całkowitym ustaniu ruchu i odczekaniu 500 ms stabilności. |

---

## 2. Kluczowe Metryki z Sukcesu (17:41:37)

* `Detected:` **`True`**
* `Cards:` **`['Gilded_73']`** (Dziesiątka Kielichów, 100% poprawność)
* `snapshot_quads_found:` `0.167` (uśredniona detekcja w oknie wideo)
* `snapshot_recognition_rejections:` **`0.0`** (brak odrzuceń na wykrytej karcie!)
* `snapshot_analysis_ms:` **`77.1 ms`** (ekstremalnie szybka, lekka analiza snapshotu w locie!)
* `time_from_motion_to_publish_ms:` **`908 ms`** (poniżej 1 sekundy od ustania ruchu do publikacji w Studio!)

---

## 3. Usprawnienia Wdrożone w Trakcie Testu

* **Wdrożenie przycisków na stałe:** Operator (Michał) w locie pomyślnie dopisał przyciski **"Ucz maty (Capture)"** (data-action="background_capture") oraz **"Wyczyść matę (Clear)"** (data-action="background_clear") bezpośrednio do kodu Panelu Operatora (`operatorPanel.js`), co pomyślnie przeszło build Vite i działa produkcyjnie.
