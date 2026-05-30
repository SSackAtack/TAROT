# Changelog: TASK-SCAN-001 (Hardening & WIA Integration)

Wszystkie modyfikacje wprowadzone w ramach zadania **TASK-SCAN-001** w celu pełnego uodpornienia, parametryzacji, integracji sprzętowej oraz automatyzacji masowego skanowania kart tarota.

---

## [MODIFY] `scripts/process_scans.py`

* **Wdrożono sprzętową integrację ze skanerami (Windows WIA Acquisition):**
  * Zintegrowano moduł `win32com.client` i systemowy interfejs COM `WIA.CommonDialog`.
  * Dodano funkcję `scan_image_via_wia()`, wywołującą systemowy kreator skanowania Windows dla podłączonego skanera fizycznego.
  * Dodano flagę CLI `--scan` automatycznie wpinającą świeżo zeskanowany obraz do precyzyjnego pipeline'u obróbki.
  * Zaimplementowano odporność na błędy: przechwytywanie CancelError (anulowanie skanowania) oraz problemów z odłączonym sprzętem.

* **Wdrożono Interaktywnego Asystenta Masowego Skanowania:**
  * Dodano flagę CLI `--interactive` uruchamiającą polskiego asystenta krok po kroku w konsoli.
  * Zaimplementowano pętlę masowego skanowania (arkusz po arkuszu) monitorującą całkowitą zadeklarowaną liczbę kart (`--total-cards`) i zliczającą postęp.
  * Dodano dynamiczny przyrost indeksacji plików wyjściowych w formacie `{prefix}_{numer:02d}.png` (np. `tarot_marsylski_00.png` do `tarot_marsylski_21.png`).
  * Zaimplementowano obsługę szybkiego Skanu Próbnego z prefiksem `Test_` w celach kalibracji jasności tła.

* **Dodano ostrzeżenia o jakości Master (WIA JPEG vs PNG/TIFF):**
  * Dodano czytelne komunikaty ostrzegawcze w konsoli: bezpośrednie skanowanie WIA w Windowsie wymusza kompresję JPEG z powodu ograniczeń systemowych COM.
  * W celach zachowania bezkompromisowej jakości Master dla algorytmów CV zalecany jest tradycyjny workflow: skanowanie do bezstratnego PNG/TIFF w programie zewnętrznym skanera, a następnie masowa obróbka folderu `scans_input`.

* **Usprawniono obróbkę i kompatybilność konsoli:**
  * Wdrożono detekcję konturów na obrazie roboczym z wycinaniem homograficznym w pełnej rozdzielczości DPI.
  * Zaimplementowano Robust Corner Ordering (funkcja `order_points`).
  * Dodano generowanie maski zaokrąglonych rogów i rzuty typów do `uint8` w OpenCV.
  * Usunięto znaki Unicode (strzałki `➔`), zapobiegając błędom `UnicodeEncodeError` w terminalu Windows (kodowanie CP1250).
  * **Poprawiono zniekształcenia (rozciąganie) kart:** Zastąpiono niestabilną funkcję OpenCV `cv2.minAreaRect` (która potrafi losowo zamieniać szerokość i wysokość w zależności od wersji i kąta nachylenia) precyzyjnym wyznaczaniem orientacji kart na podstawie odległości euklidesowych wierzchołków (`width_real` i `height_real`).
  * **Wyeliminowano odbicie lustrzane (mirroring):** Skorygowano punkty docelowe `dst_pts` dla kart leżących poziomo (landscape), zachowując stały kierunek zgodny z ruchem wskazówek zegara.

---

## [NEW] `scripts/generate_test_scan.py`
* Utworzono generator syntetycznych obrazów testowych bezpośrednio w repozytorium, umożliwiający pomyślną reprodukcję testów ciemnego i jasnego tła przez innych agentów.

---

## [NEW] `obrob_skany.bat`
* Utworzono w pełni zautomatyzowane centrum wsadowe (batch launcher) z polskim menu wyboru i CRLF zakończeniami linii, dające szybki dostęp do asystenta, obróbki i generatora testów.

---

## [MODIFY] `install_dependencies.bat`
* Przebudowano instalator CMD na w 100% kompatybilną składnię `goto` i CRLF, dodając automatyczną instalację biblioteki `pywin32`.

---

## [MODIFY] `requirements.txt`
* Dodano paczkę `pywin32` ograniczoną warunkiem `sys_platform=='win32'`, co stabilizuje instalację w środowiskach CI GitHub Actions.
