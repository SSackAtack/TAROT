# 🃏 TarotVision — Hybrydowy System Wizualizacji Tarota

**System rozpoznawania kart tarota z cyfrową wizualizacją AR dla kanału YouTube.**

## Wizja

Kamera rozpoznaje fizycznie rozkładane karty tarota, a aplikacja generuje perfekcyjną cyfrową wizualizację w czasie rzeczywistym. Widz na YouTube widzi pięknie animowane karty + realne ręce czytelniczki, słysząc autentyczną interpretację.

## Kluczowe cechy

- 📷 **Rozpoznawanie kart** — kamera identyfikuje kartę (YOLOv8 + EfficientNet-B0)
- 🎨 **Wizualizacja AR** — animowane cyfrowe karty na mistycznym tle
- 🎭 **System motywów** — zmiana klimatu wizualnego jednym kliknięciem
- 👐 **Autentyczność** — widok na ręce + głos = dowód prawdziwego czytania
- 🗂️ **Biblioteka talii** — obsługa wielu talii kart
- 📊 **Auto-SEO** — automatyczne rozdziały YouTube, miniaturki, napisy

## Architektura

```
[Kamera Anker C310] → [Python: CV] → [WebSocket] → [Web: Three.js] → [OBS] → [YouTube]
```

## Stos technologiczny

| Komponent | Technologia |
|-----------|-------------|
| Detekcja kart | Python + YOLOv8 + EfficientNet-B0 |
| Detekcja dłoni | MediaPipe Hands |
| Wizualizacja | HTML5 + JavaScript + Three.js |
| Komunikacja | WebSocket (JSON) |
| Nagrywanie | OBS Studio |
| Skanowanie kart | Epson Perfection V39II, 600 PPI |

## Dokumentacja

- [Plan koncepcyjny (FINAL)](docs/plan_koncepcyjny_v4.md)
- [Synteza analiz AI](analizy/synteza/synteza_glowna.md)
- [Raporty poszczególnych agentów](analizy/raporty/)

## Status

🟡 **Faza koncepcyjna zakończona** — następny krok: implementacja.

## Sprzęt

- Kamera: Anker Work C310 (4K, autofokus AI)
- Skaner: Epson Perfection V39II (4800 DPI)
- Mikrofon: do zakupu (~100-200 zł)
- Oświetlenie: lampa LED (~30-80 zł)

---

*Projekt rozwijany przy wsparciu Antigravity (AI vibe coding).*
