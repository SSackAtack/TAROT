# 🔮 Synteza Analiz — Projekt TAROT

**Źródła:** Claude, Grok, DeepSeek, DeepResearch (Gemini), GLM, Kimi
**Data syntezy:** 2026-05-28

---

## 1. KONSENSUS — W czym wszyscy agenci się zgadzają

### ✅ Projekt jest technicznie wykonalny
Wszystkie 6 agentów jednoznacznie potwierdza: **projekt jest realny** do zbudowania obecnymi technologiami. Żaden nie widzi technologicznych blokerów.

### ✅ Wariant B (autorska talia AI) — jednomyślna rekomendacja
**6/6 agentów** jednoznacznie rekomenduje stworzenie **własnej autorskiej talii** zamiast skanowania komercyjnej:

| Agent | Stanowisko |
|-------|-----------|
| Claude | „Autorska talia AI jest zdecydowanie lepsza" |
| Grok | „Wariant B zdecydowanie wygrywa" |
| DeepSeek | „Wariant A odrzucony" |
| DeepResearch | „Własna talia eliminuje problem prawny i daje unikalny branding" |
| GLM | „Jedyna słuszna droga" |
| Kimi | „Strategicznie bezwzględnie lepszy" |

**Powody:**
- 🔒 **Bezpieczeństwo prawne** — skan komercyjnej talii = naruszenie praw autorskich, ryzyko strike'ów YT
- 💰 **Potencjał merch** — własna talia = możliwość sprzedaży fizycznej i cyfrowej
- 🎨 **Unikalność marki** — rozpoznawalna estetyka = branding kanału
- 📜 **Pełna kontrola** — brak zależności od wydawców

> **⚠️ Kluczowe zastrzeżenie (Kimi):** Nigdy nie mówić „wygenerowane przez AI" — używać: „autorska talia stworzona w cyfrowym atelier". Generować 300–400 kandydatów, wybrać 78 najlepszych, dopracować ręcznie (Procreate/Photoshop). Wydrukowany egzemplarz w rękach = psychologiczny „proof of work".

### ✅ Autentyczność to fundament
Wszyscy agenci podkreślają: **widz musi widzieć ślady prawdziwego rytuału** — dłonie, tasowanie, fizyczny stół. System zmienia tylko warstwę prezentacji, nie treść czytania.

> **Cytat DeepResearch:** „Nie budujcie narzędzia do «automatycznego wróżenia», tylko narzędzie do «doskonałej wizualizacji prawdziwego czytania»."

### ✅ Maszyna stanów (FSM) jako fundament stabilności
5/6 agentów opisuje niemal identyczną koncepcję maszyny stanów:
```
EMPTY → DETECTING/CANDIDATE → STABLE → LOCKED → REMOVING/OCCLUDED
```
Z debouncingiem 8-15 klatek, detekcją dłoni i grace periodem okluzji.

### ✅ Auto-Chapters YouTube z metadanych
5/6 agentów niezależnie zaproponowało automatyczne generowanie rozdziałów YouTube z logów detekcji kart — z timestampami, nazwami kart i pozycjami.

### ✅ OBS nie jest silnikiem AR — jest rejestratorem
Większość agentów zgadza się, że OBS powinien służyć jako warstwa rejestrująca, nie jako komposytor AR. Rendering powinien odbywać się w dedykowanym silniku.

---

## 2. ROZBIEŻNOŚCI — Gdzie agenci się nie zgadzają

### 🔀 Wybór stosu technologicznego

| Agent | Rekomendowany stack | Uzasadnienie |
|-------|-------------------|--------------|
| **Claude** | Python + Electron/React (WebGL) | Najlepszy dla vibe codera, AI zna ten stack |
| **Grok** | TouchDesigner + TDYolo LUB Unity 6 | Szybki vibe coding, zero kodu |
| **DeepSeek** | Unity (C#) + Python (mikrousługa CV) | Najlepszy rendering, nagrywanie z GPU |
| **DeepResearch** | Browser (TF.js + OpenCV.js) + OBS | Najprostszy start, "panel reżyserski" |
| **GLM** | Godot 4 + Python + OBS | Open source, świetny 2D renderer |
| **Kimi** | Godot 4.3 + Python/ONNX + ZeroMQ | Open source, najlepsza architektura hybrydowa |

**Analiza:** Godot 4 i Unity to dwie najczęściej rekomendowane opcje (po 2 głosy każda). TouchDesigner i Web mają po 1 głosie. 

### 🔀 Metoda rozpoznawania kart

| Podejście | Zwolennicy | Argumenty |
|-----------|-----------|-----------|
| **Feature matching (ORB/SIFT)** | DeepSeek, Grok | Prostsze, nie wymaga trenowania, szybkie dla znanych obiektów 2D |
| **Deep Learning (YOLO + klasyfikator)** | Claude, GLM, Kimi | Odporniejsze na zmienne oświetlenie, odblaski, okluzje |
| **Markery ArUco (start)** | DeepResearch | Najbardziej niezawodne MVP, zero ML |
| **Dwuetapowe (YOLO → ORB/EfficientNet)** | Claude, Kimi | Kompromis — detekcja + klasyfikacja to dwa odrębne zadania |

**⚠️ Istotna sprzeczność:**
- **Kimi** twierdzi: „SIFT/ORB zawiedzie — foliowane karty + oświetlenie LED powodują odbicia, które zabijają feature matching"
- **DeepSeek i Grok** uważają feature matching za wystarczający

**Rozwiązanie:** Architektura dwuetapowa (YOLO do detekcji + EfficientNet do klasyfikacji) wydaje się najbezpieczniejszym kompromisem — 3 agentów rekomenduje to podejście.

### 🔀 Szacowany czas realizacji

| Agent | Szacunek |
|-------|---------|
| Claude | 5-7 tygodni |
| Grok | Brak jednoznacznego szacunku (MVP szybko) |
| DeepSeek | Kilka dni (prototyp via vibe coding) |
| DeepResearch | 3 etapy, brak konkretnego czasu |
| GLM | Brak szacunku |
| Kimi | **8-12 tygodni** (najdłuższy, realistyczny) |

**Analiza:** DeepSeek jest najbardziej optymistyczny, Kimi najostroźniejszy. Realistyczny szacunek: **6-10 tygodni** na działające MVP.

---

## 3. NAJCIEKAWSZE UNIKALNE POMYSŁY

### 🌟 Top 10 pomysłów (posortowane wg potencjału)

| # | Pomysł | Agent | Dlaczego warto |
|---|--------|-------|---------------|
| 1 | **Autorska talia AI jako produkt (merch)** | Wszyscy | Kickstarter, Etsy, print-on-demand, licencje = nowe źródło przychodu |
| 2 | **Auto-Chapters & SEO Engine** | Claude, DeepSeek, GLM, Kimi | Oszczędność 30-60 min/film, lepsza widoczność w YT, wyższy Watch Time |
| 3 | **Dynamic Director (auto-reżyseria)** | Kimi | Automatyczne przełączanie ujęć, crop 4K→1080p, PiP — zero operatora |
| 4 | **Second Screen Companion** | GLM | Widz skanuje QR → na telefonie widzi karty z opisami w real-time |
| 5 | **Dual Version Export** | Grok | Jeden rozkład → dwie wersje: z dłońmi (YT) i czysto cyfrowa (Shorts/IG) |
| 6 | **Companion Mini-App** | Kimi | Spersonalizowane „czytanie na dziś" dla widzów → budowanie zaangażowania |
| 7 | **Inteligentne miniaturki** | DeepSeek | System wykrywa „dramatyczne" karty i auto-generuje thumbnails pod CTR |
| 8 | **Remotion do Shorts** | DeepResearch | React-owy rendering wideo klatka po klatce — idealne do automatycznych Shorts |
| 9 | **Dynamiczne efekty energii** | Grok | Particle/glow paths między kartami widoczne tylko w finalnym nagraniu |
| 10 | **E-SL (Emotive Subtle Labels)** | GLM | Subtelne napisy z symboliką karty — wartość edukacyjna bez obciążania prowadzącej |

### 🎨 Najlepsze pomysły wizualne/UX

| Pomysł | Agent | Opis |
|--------|-------|------|
| **Worn edge effect** | Claude | Postrzępione krawędzie cyfrowej karty eliminują „plastikowy" wygląd |
| **Proceduralny grain/noise** | GLM, Claude | Szum dopasowany do ISO kamery — cyfrowa karta wygląda jak fizyczna |
| **Fisheye shader** | GLM | Shader dopasowany do obiektywu Ankera — idealne dopasowanie perspektywy |
| **Contact shadows (Gauss 20px)** | Kimi | Realistyczne cienie kontaktowe między kartą a stołem |
| **Animacja ease_out_back** | Kimi | Sprężysta animacja wejścia karty (350-450 ms) |
| **Temperatura barw** | Claude | Dopasowanie sepia/warm tint do białego balansu kamery (np. 3200K przy świecach) |
| **Micro-niedoskonałości** | Kimi | Losowa rotacja ±0.8°, skala ±0.5% — karty wyglądają „naturalnie" |

---

## 4. MAPA RYZYK — Zgodność między agentami

### 🔴 Ryzyka krytyczne (zgodność 5-6/6 agentów)

| Ryzyko | Agenci | Mitygacja |
|--------|--------|-----------|
| **Prawa autorskie do talii komercyjnej** | 6/6 | → Autorska talia AI (Wariant B) |
| **Uncanny Valley AR (za perfekcyjne = fałszywe)** | 5/6 | → Grain, worn edges, micro-niedoskonałości, contact shadows |
| **Okluzja dłonią** | 5/6 | → MediaPipe Hands, maszyna stanów z grace period |

### 🟡 Ryzyka średnie (zgodność 2-4/6 agentów)

| Ryzyko | Agenci | Mitygacja |
|--------|--------|-----------|
| **Zmienne oświetlenie (świece)** | Claude, Kimi | → Dodatkowe stałe światło LED (~30-80 zł) |
| **Status prawny AI art w Polsce** | Claude | → „Ludzki twórczy wkład" (edycja, korekty) |
| **AI-stigma w społeczności ezoterycznej** | Kimi | → Framing: „cyfrowe atelier", nie „AI" |
| **Reused content policy YT** | DeepResearch | → Każde czytanie unikalne dzięki osobowości czytelniczki |
| **Dataset treningowy (15-23k zdjęć)** | Kimi | → Augmentacja (Albumentations), Roboflow |

### 🟢 Ryzyka niskie (1 agent)

| Ryzyko | Agent | Ocena |
|--------|-------|-------|
| Niespójność stylu AI talii | GLM | Rozwiązywalne przez Midjourney --sref |
| Wydajność TF.js w 4K | GLM | Dotyczy tylko stacku webowego |
| Linux vs Windows | Kimi | Preferuje Linux, ale Windows zadziała |

---

## 5. REKOMENDOWANY STOS TECHNOLOGICZNY (synteza)

Na podstawie analizy wszystkich 6 raportów, rekomendowany stos to:

### Architektura hybrydowa (konsensus)

```
[Kamera Anker C310] 
    → [Python: detekcja CV]
        → [WebSocket/ZeroMQ: komunikacja]
            → [Silnik renderujący: wizualizacja]
                → [OBS / wbudowany recorder: nagrywanie]
```

### Decyzje kluczowe

| Komponent | Rekomendacja | Uzasadnienie |
|-----------|-------------|--------------|
| **Detekcja kart** | Dwuetapowa: YOLOv8 → EfficientNet-B0 | 3/6 agentów, najlepszy kompromis niezawodności i prostoty |
| **Silnik renderujący** | **Godot 4.3+** (2 głosy) lub **Web (HTML5/Three.js)** | Godot: open source, świetny 2D. Web: najlepszy dla vibe codera |
| **Komunikacja** | WebSocket lub ZeroMQ | Niska latencja, prostota implementacji |
| **Nagrywanie** | Godot MovieWriter lub OBS Studio | Zależne od wybranego silnika |
| **Detekcja dłoni** | MediaPipe Hands | 4/6 agentów, standard branżowy |
| **Stabilizacja** | FSM per slot, debouncing 10-15 klatek | Konsensus wszystkich agentów |
| **Talia** | Autorska AI + ręczna korekta | 6/6 agentów, jednomyślnie |

---

## 6. REKOMENDOWANY PLAN DZIAŁANIA (synteza)

### Etap 0: Przygotowanie (1 tydzień)
- [ ] Decyzja o pierwszej talii (autorska AI vs licencjonowana)
- [ ] Zakup mikrofonu USB (~100-200 zł)
- [ ] Zakup lampy LED pierścieniowej (~30-80 zł)
- [ ] Przygotowanie stanowiska (stół, mata z pozycjami, oświetlenie)
- [ ] Wybór stylu wizualnego z żoną (mockupy motywów)

### Etap 1: Proof of Concept (1-2 tygodnie)
- [ ] Podstawowa detekcja karty kamerą (choćby 10 kart)
- [ ] Wyświetlenie rozpoznanej karty na ekranie
- [ ] Weryfikacja opóźnienia (<200ms)
- [ ] Test z OBS — czy da się przechwycić jako źródło

### Etap 2: MVP (3-4 tygodnie)
- [ ] Pełna detekcja 78 kart + orientacja
- [ ] System motywów (minimum 1 motyw)
- [ ] Animacje wejścia kart
- [ ] Layouty rozkładów (3 karty, Krzyż Celtycki)
- [ ] Maszyna stanów + debouncing
- [ ] Kompozycja PiP (stół + ręce)
- [ ] Pierwszy testowy film na YT

### Etap 3: Polish (2-3 tygodnie)
- [ ] Auto-Chapters
- [ ] Więcej motywów wizualnych
- [ ] Efekty wizualne (glow, particles, shadows)
- [ ] Wielojęzyczność (PL/EN)
- [ ] Auto-miniaturki

### Etap 4: Skalowanie (ciągłe)
- [ ] Dodawanie nowych talii
- [ ] Live streaming
- [ ] Companion app
- [ ] Monetyzacja (Patronite, merch)

---

## 7. KLUCZOWE CYTATY (po jednym z każdego agenta)

> **Claude:** „Największe ryzyko techniczne: Nie technologia — oświetlenie."

> **Grok:** „Projekt jest w pełni wykonalny już dziś na lokalnym PC. Największe ryzyko to nie technologia, tylko precyzyjne dostrojenie CV."

> **DeepSeek:** „TarotVision AR celnie rozwiązuje realny problem twórców ezoterycznych (...) Przy Vibe Codingu pierwszy prototyp można postawić w ciągu kilku dni."

> **DeepResearch:** „Nie budujcie narzędzia do «automatycznego wróżenia», tylko narzędzie do «doskonałej wizualizacji prawdziwego czytania»."

> **GLM:** „Główne wyzwanie inżynieryjne nie leży w samej detekcji, ale w bezsztucznym połączeniu analogowego wideo z cyfrową nakładką."

> **Kimi:** „Projekt jest wykonalny, innowacyjny i ma potencjał monetyzacyjny znacznie wykraczający poza AdSense."

---

*Synteza wykonana przez Antigravity na podstawie 6 niezależnych analiz AI.*
