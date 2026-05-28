# TarotVision AR — Raport Stress-Test

**Panel ekspercki:** Główny Architekt Oprogramowania (Systemy RT / Computer Vision) · Strateg UX/UI · Ekspert ds. Rozwoju na YouTube

---

## Sekcja 1: Architektura Technologiczna

### Rekomendowany Stack #1 (Optymalny): Python + Electron/React

To złoty środek między wydajnością a podatnością na vibe-coding z asystentem AI.

```
┌─────────────────────────────────────────────────────────────────────┐
│  WARSTWA WEJŚCIA                                                    │
│  Kamera 4K (Anker C310) → cv2.VideoCapture → Raw frame 1080p/60fps │
├─────────────────────────────────────────────────────────────────────┤
│  WARSTWA DETEKCJI                                                   │
│  YOLOv8-nano (lokalizacja + orientacja) → ORB/SIFT (identyfikacja) │
├─────────────────────────────────────────────────────────────────────┤
│  WARSTWA LOGIKI                                                     │
│  Debounce Engine → State Manager → emit JSON (WebSocket :5000)      │
├─────────────────────────────────────────────────────────────────────┤
│  WARSTWA WYJŚCIA                                                    │
│  Electron/React (WebGL compositing) → VirtualCam → OBS Studio      │
└─────────────────────────────────────────────────────────────────────┘
```

**Rdzeń detekcji** to Python (OpenCV + YOLOv8 + biblioteki CV) — język najlepiej obsługiwany przez asystentów AI, z najdojrzalszym ekosystemem Computer Vision. **Frontend AR-overlay** to Electron z React + WebGL (Three.js lub Pixi.js) — środowisko webowe, gdzie animacja kart, cienie i efekty blendowania są trywialne do generowania z pomocą AI. **Komunikacja** między procesami przez lokalny WebSocket emitujący obiekty JSON z metadanymi kart.

**Szacowane opóźnienie całkowite: 25–45 ms** (dobrze poniżej progu percepcji ~80 ms).

---

### Alternatywny Stack #2 (Dla maksymalnej jakości renderingu): Godot 4 + Python sidecar

Jeśli wizualny realizm nakładki jest priorytetem (refleksy, realistyczne cienie, particle effects):

- **Python sidecar** wykonuje całą detekcję CV i emituje JSON przez named pipe lub UDP localhost.
- **Godot 4** (GDExtension lub GDScript) odbiera metadane i renderuje karty jako pełnoprawne obiekty 3D z fizyką materiałów — `CardMaterial` z subsurface scattering sprawia, że papier wygląda jak papier.
- Wbudowane `ViewportTexture` w Godot pipuje rendering do OBS przez Virtual Camera.

**Wada:** Godot/GDScript jest gorzej reprezentowany w zbiorach treningowych LLM-ów niż Python/JavaScript — niższy komfort vibe-codingu.

**Werdykt:** Stack #1 jest optymalny dla startu. Stack #2 dla twórcy gotowego zainwestować więcej czasu w artystyczne dopracowanie.

---

### Narzędzie do nagrywania

Nie jesteście "skazani" na OBS, ale warto go użyć jako ostatni etap kompozycji z jednego prostego powodu — enkoder H.264/HEVC sprzętowy (NVENC / AMF / VideoToolbox) jest w OBS zoptymalizowany pod YouTube. Alternatywa: Electron-app może renderować do pamięci i pipować przez FFmpeg bezpośrednio do pliku MP4, eliminując OBS — ale wymaga własnej implementacji miksowania audio, co jest niepotrzebnym nakładem pracy.

---

## Sekcja 2: Computer Vision — Logika i Edge Cases

### Model detekcji: podejście dwuetapowe

Najważniejsza decyzja architektury CV: **nie używaj jednego modelu do wszystkiego**. Identyfikacja 78 unikalnych obiektów 2D z rotacją to dwa oddzielne zadania.

#### Etap 1 — Detekcja i lokalizacja (gdzie jest karta, jaka orientacja)

YOLOv8-nano lub YOLOv8s dotrenowany na 3 klasach: `card_upright`, `card_reversed`, `hand`. Model trenuje się na 200–400 zdjęciach każdej karty (generatywna augmentacja: różne oświetlenia, lekkie zakrzywienia, częściowa okluzja).

- Inference na GPU: ~8 ms na klatkę
- Inference CPU only: ~25 ms — wciąż akceptowalne

#### Etap 2 — Identyfikacja (która konkretnie karta)

Po wykryciu ROI przez YOLO, wycięty prostokąt karty trafia do klasycznego **Feature Matching: ORB + FLANN-based matcher** (ewentualnie AKAZE dla lepszej odporności na zmiany oświetlenia). ORB buduje bazę deskryptorów z 78 wzorcowych obrazów i wykonuje match w czasie 3–8 ms. Podejście jest deterministyczne i nie halucynuje. Dla karty ~60×100 px na frame 1080p dokładność identyfikacji osiąga >97%.

**Alternatywa hybrydowa:** EfficientNet-B0 jako klasyfikator 78 klas (fine-tuning na własnej talii) — lepszy accuracy (~99,5%), ale wymaga ~500 próbek per karta i GPU do trenowania. Naturalne rozszerzenie po uruchomieniu MVP.

---

### Debouncing i okluzja — niezawodna logika stanów

Maszyna stanów dla każdego slotu na blacie:

```
EMPTY
  └─▶ (karta wykryta ≥ 3 klatki z rzędu)
        CANDIDATE
          └─▶ (stabilna ≥ 12 klatek, IoU > 0.88)
                CONFIRMED ◀──────────────────────┐
                  ├─▶ (niewidoczna ≤ 8 klatek)   │
                  │     OCCLUDED                  │
                  │       ├─▶ (widoczna, match > 0.85) ──┘  (bez re-animacji)
                  │       └─▶ (niewidoczna > 8 klatek)
                  │             EMPTY  (overlay znika z exit-anim)
                  └─▶ (nowa karta na tym slocie)
                        TRANSITION
```

**Kluczowe parametry:**

| Parametr | Wartość | Uzasadnienie |
|---|---|---|
| Klatki do potwierdzenia | 12 @ 60 fps = 200 ms | Ręka zdąży się odsunąć |
| Grace period okluzji | 8 klatek = 133 ms | Eliminuje flickering przy ruchu palca |
| Promień snapowania do slotu | 40 px | Karty "przyklejają się" do predefiniowanych pozycji |
| IoU threshold (stabilność) | 0.88 | Odporność na mikrodrgania dłoni |

**Rozwiązanie odbicia światła na foliowanych kartach:** Preprocessing klatki przed detekcją — adaptywne usuwanie połysku przez `cv2.fastNlMeansDenoisingColored` + CLAHE (Contrast Limited Adaptive Histogram Equalization). Koszt ~5 ms, ale dramatycznie poprawia detekcję foliowanych kart w świetle świec.

---

## Sekcja 3: Strategia, Prawa Autorskie i Psychologia Widza

### Wariant A vs Wariant B

#### Wariant A — Skan rynkowej talii + AI Upscaler

**Aspekty prawne:**
- Talie wydane po 1923 r. są chronione prawem autorskim. Skanowanie bez licencji = naruszenie.
- YouTube ContentID może zaflagnować wideo po rozpoznaniu grafik — monetyzacja zagrożona.
- Wyjątek: Rider-Waite (pre-1923) jest w domenie publicznej — ten konkretny przypadek jest bezpieczny.

**Potencjał biznesowy:**
- Zero potencjału merchandisingowego — nie można drukować ani sprzedawać grafik.
- Brak unikalności wizualnej kanału. Każdy twórca używa tych samych kart.

**Wykonalność techniczna:**
- Szybki start — skany gotowe od razu, model CV trenuje się na istniejących danych.
- Dobra opcja dla fazy MVP/prototypu, zanim kanał osiągnie skalę.

---

#### ✦ Wariant B — Autorska talia AI (REKOMENDOWANY)

**Aspekty prawne:**
- Pełna kontrola nad prawami przy odpowiednim workflow generacji i dokumentacji promptów.
- Brak ryzyka ContentID — YouTube nie rozpozna grafik jako istniejące IP.
- Uwaga dla polskich twórców: AI-generated art ma niepewny status prawnoautorski — warto dodać "ludzki twórczy wkład" (edycja, kompozycja, korekty w Photoshop/Affinity).

**Potencjał biznesowy:**
- Merchandising: sprzedaż fizycznych talii (print-on-demand), plakaty, NFT-ready.
- Brand identity: unikalna estetyka staje się rozpoznawalną marką kanału.
- Licencjonowanie grafik innym twórcom jako dodatkowy strumień przychodów.

**Wykonalność techniczna:**
- Cyfrowe oryginały w natywnej rozdzielczości 4K — zero kompromisów jakościowych w systemie AR.
- Jednorazowy nakład: ~2–3 tygodnie na stworzenie spójnej talii 78 kart.

**Praktyczny workflow:** Generować karty w stylu spójnym wizualnie (ten sam style reference w Midjourney: `--sref` z pierwszej zatwierdzonej karty). Drukować na macie laminowanym papierze 300 g — ważne: **mat, nie glossy**, co redukuje odbicia na blacie. Cyfrowe oryginały PNG 4K trafiają bezpośrednio do systemu AR.

---

### UX/UI nakładki — psychologia autentyczności

Widz ezoteryczny jest wyczulony na "CGI feel". Poniższe zabiegi eliminują ten efekt:

**Blending:**
Nakładka nigdy nie powinna być na 100% opacity. Ustaw overlay na **92–95% opacity** z trybem blendowania `Multiply` lub `Screen` (zależnie od tła blatu). Mikrotekstura drewnianego blatu przeświecająca przez cyfrową grafikę sprawia, że mózg widza klasyfikuje obiekt jako fizyczny.

**Subtelny shadow casting:**
Rzuć miękkiego cienia pod cyfrową kartą zgodnie z kierunkiem oświetlenia w kadrze. Nawet 4 px blur + 3 px offset w prawidłowym kierunku przekonuje mózg o trójwymiarowości. Cień "pływający" w złym kierunku wygląda gorzej niż brak cienia.

**Animacja wejścia (200 ms):**
Karta nie "pojawia się" — ona "opada". Animacja: przesunięcie 8 px w górę przy jednoczesnym `opacity: 0 → 1` + `scale: 0.95 → 1.0`. Naśladuje ruch odkładania karty przez rękę.

| Czas animacji | Efekt wizualny |
|---|---|
| < 150 ms | Wygląda jak błysk / glitch |
| 200 ms | Optymalne — naturalne odkładanie |
| > 300 ms | Wygląda jak loading screen |

**Granica krawędzi:**
Mały "worn edge" efekt na obramowaniu cyfrowej karty (nieregularne, lekko postrzępione krawędzie symulowane przez SVG filter lub pre-renderowany PNG border) dramatycznie redukuje "plastikowy" wygląd. Jest to jednorazowy asset nakładany na wszystkie karty.

**Temperatura barw:**
Match cyfrowej karty z białym balansem kamery. Przy ciepłym oświetleniu świec (3200 K) nałóż lekki warm color grade na overlay: `sepia(5%) + warm tint +5` w CSS filter lub dedykowany LUT w postprodukcji.

---

## Sekcja 4: Innowacje i Wartość Dodana

Zakładając stabilny strumień metadanych w formacie:

```json
{
  "card": "The Moon",
  "position": 3,
  "rotation": "reversed",
  "spread": "celtic_cross",
  "timestamp": 1718123456
}
```

Poniżej trzy innowacje o wysokim stosunku wartości do nakładu implementacyjnego:

---

### Innowacja 1: Auto-generowanie opisów kart z AI

**Opis:** Każde potwierdzenie karty na slocie triggeruje call do API (Claude / GPT-4o) z kontekstem: jaka karta, jaka pozycja w spreadzie, jaka orientacja, jakie pytanie zadał widz (definiowane przez twórczynię przed nagraniem w formularzu pre-session). System generuje gotowy **skrypt voiceover** w stylu twórczyni po jednokrotnym przykładowym fine-tuningu.

**Wdrożenie:** Formularz pre-session (pytanie / intencja czytania) → Python odbiera JSON event → call API → skrypt TXT czeka w folderze obok nagranego wideo.

**Szacunek oszczędności: 4–6 godzin tygodniowo** z przygotowania opisów i scenariuszy.

---

### Innowacja 2: Auto-generowanie rozdziałów YouTube

**Opis:** Na podstawie timestampów odkładania kart system automatycznie generuje plik rozdziałów YouTube w formacie gotowym do wklejenia w opis wideo:

```
00:00 Intro
02:14 Stos 1 — Karta: The Moon (odwrócona)
05:33 Stos 2 — Karta: The Sun
08:41 Stos 3 — Karta: Ace of Cups
```

**Wdrożenie:** JSON z timestamps → skrypt Python → gotowy tekst do opisu. Implementacja zajmuje ~2 godziny.

**Efekt:** Widz przeskakuje bezpośrednio do swojego stosu kart zamiast przewijać. Wzrost watch time i retention bezpośrednio przekłada się na algorytm YouTube.

---

### Innowacja 3: Live overlay dla streamów ze statystykami sesji

**Opis:** Dla sesji na żywo JSON metadanych strumieniuje do nakładki OBS (Browser Source w HTML/CSS), która wyświetla: nazwę bieżącej karty, jej tradycyjne znaczenie (z lokalnej bazy danych), licznik "która karta wypadła najczęściej w tej sesji". Widzowie w chacie widzą to samo co twórczyni — wzmacnia zaangażowanie.

**Wdrożenie:** OBS Browser Source + lokalny WebSocket serwer (ten sam serwer co w architekturze Stacku #1, z dodatkowym subskrybentem "read-only"). Nakład: ~4–6 godzin implementacji.

---

## Werdykt końcowy

**Wykonalność: Wysoka.**

Projekt nie wymaga żadnej nieudowodnionej technologii. Każdy komponent (YOLOv8, OpenCV, Electron, WebSocket) jest produkcyjnie dojrzały i doskonale obsługiwany przez asystentów AI przy kodowaniu.

**Krytyczna ścieżka do MVP:**

| Etap | Nakład | Wynik |
|---|---|---|
| Python + OpenCV — detekcja 1 karty | 1 weekend | Proof of concept |
| Pełna detekcja 78 kart + debouncing | 2–3 tygodnie | Działający silnik CV |
| Electron overlay + animacje | 1–2 tygodnie | Kompletny system AR |
| Integracja OBS + testy produkcyjne | 3–5 dni | Gotowy do nagrywania |

**Największe ryzyko techniczne:** Nie technologia — oświetlenie. Kamera nad blatem w świetle świec to najtrudniejszy przypadek dla CV ze względu na zmienne warunki. 

**Rekomendacja praktyczna:** Jedno dodatkowe stałe, zimne źródło światła (mała lampa pierścieniowa za kadrem, ~3500 K) skierowane na blat. Eliminuje oświetlenie jako zmienną i dramatycznie redukuje potrzebę rozbudowanego preprocessingu — to inwestycja 30–80 zł, która oszczędza tygodnie debugowania modelu.

---

*Raport przygotowany przez: Panel Ekspercki TarotVision AR*
*Wersja: 1.0*
