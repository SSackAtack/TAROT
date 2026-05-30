# Plan Wykonawczy: Efektowne Wykładanie Kart i Mistyczna Scenografia 3D

## Status ogólny
Zaprojektowaliśmy i wdrożyliśmy pełne, nastrojowe środowisko 3D dla **Trybu Kinowego (WOW)** w aplikacji TarotVision, znosząc dotychczasową pustkę na rzecz mistycznego, dębowego biurka oraz tańczących płonących świec. Równocześnie zaimplementowaliśmy spektakularną animację wykładania kart (spadanie z dynamicznym podkręceniem typu spin i obrotem flip z rewersu na awers o 180 stopni), z zaokrąglonymi wierzchołkami i dwuwarstwowym WebGL eliminującym z-fighting.

---

## Session Status (2026-05-30)
W tej sesji pracował model **Gemini (Google DeepMind)** w trybie pair programmingu z Michałem. Wszystkie wytyczne zostały pomyślnie zaimplementowane, a kod pomyślnie skompilowany produkcyjnie. Commit hash: `b3f1ae2`.

### Zrobiono w tej sesji:
- **Krok 1:** Napisano proceduralny, mistyczny generator tekstury rewersu karty w locie na Canvasie (aksamitny fioletowy gradient, podwójne złote linie, ozdobne astrologiczne narożniki oraz 12-ramienna gwiazda solarna z gwiezdnym pyłem).
- **Krok 2:** Stworzono generator proceduralnej tekstury starego biurka mahoniowo-dębowego z wyrazistymi, naprzemiennie ciemnymi i jasnymi słojami drewna, sękami, winietą oraz centralnym, złotym kręgiem astrologicznym z podziałką i 8 wyrytymi runami planetarnymi (Słońce, Księżyc, Merkury, Wenus, Ziemia, Mars, Jowisz, Saturn) widocznymi bezpośrednio pod kartami w kadrze.
- **Krok 3:** Przebudowano geometrię kart w `createVirtualCard(name)` na zagnieżdżoną grupę (Double-Sided 3D Card) z trójwymiarowym korpusem `ExtrudeGeometry` pokrytym rewersem i złoconymi bokami, oraz płaskim płatkiem awersu `ShapeGeometry` o zaokrąglonych narożnikach i ręcznie przeliczonych współrzędnych UV. Płatek awersu został wysunięty na `z = 0.062` w celu wyeliminowania z-fighting.
- **Krok 4:** Pogrubiono i podwyższono świece 3D (`CylinderGeometry(0.42, 0.46, 2.8)`), postawiono je stabilnie na stole w osi Y oraz przesunięto bliżej kart (`x = ±8.2, z = -4.0`), by były w pełni widoczne w kadrze.
- **Krok 5:** Powiększono płomienie świec (`ConeGeometry(0.18, 0.60)`) i zastosowano dla nich emisyjne stopienie z otoczeniem za pomocą `THREE.AdditiveBlending` oraz `depthWrite: false` (żarzący się, prawdziwy ogień 3D z błękitnym jądrem u nasady).
- **Krok 6:** Zaimplementowano organiczne kołysanie się płomieni na wietrze oraz pulsowanie ich skali w pętli `animate()`.
- **Krok 7:** Przesunięto dynamiczne światła punktowe (`candleLight` na lewą świecę, `glowLight` na prawą świecę) i obniżono ich pozycję Y, w połączeniu z podniesieniem chropowatości stołu do `roughness: 0.65`. Dało to zjawiskowe, miękkie, malarskie, rozproszone odblaski stereo i dynamiczne cienie kart.
- **Krok 8:** Powiązano całą scenografię (biurko + świece) z trybem kinowym (WOW) – płynnie wyłaniają się z mroku (`fade-in`), a po jego wyłączeniu płynnie wygaszają się do zera (`fade-out`), pozwalając natychmiast wrócić do przezroczystego OBS overlay!
- **Krok 9:** Przetestowano i skompilowano produkcyjnie projekt za pomocą `npm run build` w czasie 317ms.

---

## Taski
- [x] Krok 1: Stworzenie proceduralnego generatora tekstury rewersu karty w pamięci (`createCardBackTexture` na Canvasie)
- [x] Krok 2: Przebudowa struktury geometrycznej kart w `createVirtualCard(name)` na zagnieżdżoną grupę (Double-Sided 3D Card) z zaokrąglonymi narożnikami awersu
- [x] Krok 3: Dostosowanie inicjalizacji stanów kart (start z góry, obrót tyłem) w `handleCardData()`
- [x] Krok 4: Wdrożenie animacji flip (odwracanie o 180 stopni), aerodynamicznego dzioba i amortyzacji lądowania w pętli `animate()`
- [x] Krok 5: Stworzenie generatora proceduralnego tekstury starego biurka dębowego (`createDeskTexture` na Canvasie) z centralnym kręgiem runicznym
- [x] Krok 6: Implementacja tworzenia geometrii biurka oraz grubszych 3D świec stojących na stole z emisyjnymi płomieniami Additive Blending (`initScenography`)
- [x] Krok 7: Powiązanie płynnej widoczności scenografii (`currentScenographyOpacity`) z przełączaniem trybu kinowego w `toggleWowMode()`
- [x] Krok 8: Wdrożenie dynamicznego migotania ognia, kołysania na wietrze i rozproszonego oświetlenia stereo stołu w pętli `animate()`
- [x] Krok 9: Weryfikacja poprawności kompilacji projektu za pomocą `npm run build`

---

## Kolejne kroki dla następcy
1. **Dalsza optymalizacja shaderów:** Jeśli wydajność WebGL będzie kluczowa na słabszych maszynach OBS, można połączyć emisyjne płomienie świec w jeden instancjonowany system lub zoptymalizować geometrie.
2. **Dodatkowe efekty cząsteczkowe:** Można dodać drobny dym (smoke particles) płynący z płomieni świec w kierunku góry sceny w trybie kinowym.
3. **Integracja z CV:** Zweryfikować zachowanie rzucanych cieni i rotacji kart pod kątem detekcji rzeczywistej w trudnych warunkach oświetleniowych, aczkolwiek w trybie produkcyjnym (non-WOW) wszystko powraca do przezroczystości i jasnego oświetlenia bezcieniowego, więc silnik CV ma idealne warunki pracy.
