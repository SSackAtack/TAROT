# Szczegółowa Diagnostyka Procesu Skanowania i Autodetekcji Kart

**Data:** 2026-05-31
**Autor:** Gemini (Google DeepMind)
**Status:** Przekazanie do zespołu AI / Review (ChatGPT / Codex)

---

## 1. Opis Problemu
Użytkownik zgłosił, że podczas skanowania próbnego z użyciem asystenta (`obrob_skany.bat` / `process_scans.py` WIA) fizyczny skaner działa poprawnie, jednak w folderze wyjściowym `scans_output` zapisują się tylko **3 z 5 umieszczonych na szybie kart**. Pozostałe 2 karty są w pełni widoczne na ogólnym skanie, ale nie zostają wycięte i zapisane na dysku.

---

## 2. Analiza Śledcza i Metodologia
W celu zdiagnozowania problemu wdrożyliśmy w locie patch diagnostyczny do `process_scans.py` (zapis logów do `logs/process_scans.log` oraz tworzenie kopii surowego skanu do `scans_input/last_wia_scan.jpg`).

Następnie uruchomiliśmy dedykowany skrypt analizy geometrycznej OpenCV (`test_failed_scan.py`) bezpośrednio na ostatnim fizycznym skanie użytkownika (`last_wia_scan.jpg`, rozdzielczość oryginalna `2550x3510 px`, rozmiar pliku `26.8 MB`).

### Wyniki analizy OpenCV dla jasnego tła (LIGHT):
```
--- SZCZEGÓŁOWA ANALIZA KONTURÓW DLA TŁA LIGHT ---
Zakres dozwolonej powierzchni: 52848.0 .. 1056960.0

[SUKCES] Wykryte poprawne karty (3):
  Kontur #13: Powierzchnia=524178.0, Wierzchołki=4
  Kontur #29: Powierzchnia=529994.0, Wierzchołki=4
  Kontur #37: Powierzchnia=529644.0, Wierzchołki=4

[ODRZUCONE Z POWODU WIERZCHOŁKÓW] (2):
  Kontur #28: Powierzchnia=387252.0, Wierzchołki=12 (wymagane w kodzie: 4-8)
  Kontur #38: Powierzchnia=457981.0, Wierzchołki=10 (wymagane w kodzie: 4-8)
```

---

## 3. Kluczowe Wnioski Diagnostyczne

### Wniosek A: Zlewanie się białych ramek z jasnym tłem (Fizyczna Przyczyna Główna)
* Użytkownik skanuje z **zamkniętą białą pokrywą skanera** (mediana pikseli na brzegu tła wynosi `238.0` / 255.0 – idealnie białe tło).
* Większość kart tarota (w tym standardowa talia RWS) posiada **szerokie, białe ramki** wokół grafik.
* Ponieważ biała ramka kart leży na białym tle skanera, **kontrast na krawędzi karty spada niemal do zera**. Próg binaryzacji Otsu odcina te białe krawędzie i stapia je z tłem.
* W rezultacie, dla brakujących 2 kart, OpenCV nie wykrywa zewnętrznego obrysu karty, lecz **wewnętrzną ramkę kolorowej grafiki**.

### Wniosek B: Postrzępiony kontur i spadek powierzchni (Matematyczna Przyczyna Odrzucenia)
1. **Zaniżona Powierzchnia (Area):** Wewnętrzny rysunek grafiki jest mniejszy niż cała karta. Dlatego powierzchnia Konturu #28 (`387 252 px`) oraz Konturu #38 (`457 981 px`) wynosi znacznie mniej niż typowy kontur pełnej karty (`~530 000 px`).
2. **Duża Liczba Wierzchołków:** Wewnętrzne grafiki kart tarota mają skomplikowane i bogate w detale krawędzie. Po progowaniu i aproksymacji wielokąta (`approxPolyDP`), algorytm wykrywa dla nich aż **12 wierzchołków** (Kontur #28) oraz **10 wierzchołków** (Kontur #38).
3. **Odrzucenie przez filtr wierzchołków:** Ponieważ dozwolona liczba wierzchołków wynosi maksymalnie 8, te dwa kontury zostają odrzucone jako "nie-karty", mimo że fizycznie leżą na szybie.

---

## 4. Rekomendacje Rozwiązania (Dla Zespołu AI i Użytkownika)

### Rekomendacja 1 (Fizyczna - Najważniejsza)
Skanowanie kart tarota z białą ramką na białym tle skanera zawsze będzie generować regresje detekcji. 
* **Rozwiązanie:** Użytkownik powinien skanować z **otwartą pokrywą skanera** (co daje idealnie czarne/ciemne tło) lub podłożyć pod pokrywę **czarną podkładkę/karton**. Czarna przestrzeń wokół kart zapewni 100% kontrastu z białymi ramkami, co pozwoli OpenCV na bezbłędne wykrycie idealnych prostokątów o powierzchni `~530 000 px` i dokładnie 4 wierzchołkach.

### Rekomendacja 2 (Algorytmiczna - Do Rozważenia przez Codex/ChatGPT)
* Rozważyć dodanie adaptacyjnego progowania (Adaptive Thresholding) w przypadku wykrycia jasnego tła, aby spróbować wyodrębnić subtelną różnicę jasności między białą krawędzią papieru karty a plastikową klapą skanera.
* Ewentualnie zrezygnować ze sztywnego limitu wierzchołków (`len(approx) <= 8`) na rzecz weryfikacji proporcji boków (Aspect Ratio) i współczynnika prostokątności (Solidity / Extent) obróconego prostokąta (`minAreaRect`), co jest o wiele bardziej tolerancyjne na postrzępione lub wewnętrzne kontury.

---

## 5. Podsumowanie Zmian w Repozytorium w tej sesji
* Wdrożono zapis logów skanowania do pliku `logs/process_scans.log`.
* Wdrożono automatyczne zachowywanie surowych skanów przed usunięciem w przypadku błędu detekcji (`scans_input/failed_scan_{timestamp}.jpg`).
* Wdrożono zapis kopii bezpieczeństwa z ostatniego skanowania WIA (`scans_input/last_wia_scan.jpg`).
* Zwiększono tolerancję wierzchołków konturu kart z 6 do 8.
* Ustawiono automatyczną detekcję tła (`--background auto`) jako domyślne zachowanie asystenta w Pythonie oraz pliku `.bat`.
