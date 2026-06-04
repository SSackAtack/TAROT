# Pomysły na rozwój strony TarotKA

## 1. Styl „Analog Film / Cinematic Warm"

**Źródło inspiracji:** kadr filmowy „A Quiet Year in Berlin" — 35mm, light leak, kinowy minimalizm.

### Paleta kolorów
- Tło: głęboki czekoladowy brąz `#12090a` (zamiast czerni)
- Akcent: ciepłe bursztynowe złoto `#c9a55a`
- Tekst: kremowy ecru `#f0e6d3` (nie ostry biały)
- Light leak: radialny blur w złoto-bursztynowych tonach

### Typografia
- Nagłówki: **EB Garamond italic** — klasyczny kaligraficzny serif
- UI/meta: **Space Mono uppercase** — monospace z szerokim letter-spacing
- Tagline'y w stylu `REEL III · TITLE`

### Elementy wizualne
- Ramka filmowa (border) wokół całego viewportu
- Ciepły light leak w hero zamiast cząsteczek
- Ziarnistość filmowa (grain overlay — już mamy)
- Numeracja sekcji w stylu filmowym: `REEL I`, `REEL II`
- Minimalizm — dużo pustej przestrzeni, zero ozdobników
- Czysta typografia jako główny element designu

### Nastrój
Kinowy, analogowy, intymny, premium. Jak zaproszenie na prywatny pokaz.

---

*Dodano: 2026-06-04*

## 2. Dynamiczne prezentacje i efekty z html-video

**Źródło inspiracji:** Repozytorium [html-video](https://github.com/nexu-io/html-video) (meta-warstwa wideo-z-HTML dla agentów).

### Dynamiczne wideo z wróżbą
- Generowanie spersonalizowanych filmów MP4 z wróżbą/kartą dnia bezpośrednio z kodu HTML/CSS przy użyciu bezgłowego renderera (np. do udostępniania w social media).
- Dołączanie automatycznych podkładów muzycznych AI do generowanych wróżb.

### Efekt "Typewriter" z kursorem VFX
- Wykorzystanie efektu dynamicznego pisania interpretacji karty tarota na ekranie z migającym, mistycznym kursorem stylizowanym na stary terminal (`vfx-text-cursor`), co buduje suspens i wrażenie seansu w czasie rzeczywistym.

### Płynne tła (Liquid Aurora Gradients)
- Zastosowanie hipnotyzującego, powolnego ruchu płynnych gradientów w tle sekcji hero (na wzór `frame-liquid-bg-hero`), mieszających burgund, głębokie złoto i czerń, zamiast statycznego obrazu.

### Animowane efekty Cinematic Light Leaks
- Dodanie subtelnych, animowanych błysków światła (light leaks) nakładających się na elementy interfejsu (inspirowane `frame-light-leak-cinema`), co idealnie współgra z kinową/analogową estetyką.

---

*Zaktualizowano o inspiracje html-video: 2026-06-04*
