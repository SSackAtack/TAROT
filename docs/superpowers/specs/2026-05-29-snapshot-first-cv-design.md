# Snapshot-First CV Design

## Status

Spec projektowy zaakceptowany kierunkowo przez Michala 2026-05-29. Dokument opisuje zmiane podejscia z ciaglego rozpoznawania kart w strumieniu wideo na automatyczna analize stabilnych snapshotow.

## Cel

TarotVision ma wspierac interpretacje kart bez rozpraszania osoby prowadzacej sesje. System nie powinien wymagac recznego przycisku ani ciaglego strojenia podczas pracy. Priorytetem jest stabilnosc i precyzja, a nie minimalne opoznienie.

Nowa zasada:

```text
watch lightly -> wait for stable layout -> analyze one good snapshot -> publish full table state
```

## Uzasadnienie

Rozklady tarota sa w praktyce statycznymi ukladami z krotkimi okresami ruchu, gdy karta jest dokladana, przesuwana albo zdejmowana. Ciagle rozpoznawanie tozsamosci kart przy 30 FPS optymalizuje niewlasciwy problem: dynamiczne sledzenie sceny, ktora zwykle nie musi byc dynamiczna.

Snapshot-first zmniejsza koszt obliczeniowy i ryzyko niestabilnego overlayu. Przegladarka moze trzymac ostatni dobry uklad, a backend publikuje nowy stan dopiero po zatwierdzeniu stabilnego obrazu.

## Stan aktualny

- `app_cv/main.py` prowadzi aktualnie petle kamery, ORB/FLANN matching, tracking konturowy, WebSocket i diagnostyke.
- `app_cv/tarotvision/motion.py` zawiera lekki detektor ruchu, ktory moze zostac uzyty jako watcher.
- `app_cv/tarotvision/card_detection.py` i `card_recognition.py` zawieraja elementy przydatne do analizy pojedynczej klatki.
- `app_ar/main.js` potrafi renderowac stan kart i ma tryb operatorski pod `?operator=1`.
- Obecny frontend powinien docelowo dostawac pelny zatwierdzony stan ukladu, a nie nerwowy strumien detekcji z kazdej klatki.

## Zakres pierwszej wersji

Pierwsza wersja ma udowodnic, ze snapshot-first daje stabilniejszy wynik niz ciagle rozpoznawanie.

W zakresie:

- automatyczne wykrycie, ze scena sie zmienila,
- oczekiwanie na dluzsza stabilizacje po ruchu,
- pobranie serii kilku snapshotow kontrolnych,
- podstawowa ocena jakosci snapshotow,
- analiza najlepszej statycznej klatki istniejacym silnikiem CV,
- publikacja kompletnego ukladu jako jednego zatwierdzonego stanu,
- utrzymywanie ostatniego dobrego ukladu w przegladarce,
- metryki diagnostyczne dla czasu reakcji i odrzucen snapshotow.

Poza zakresem pierwszej wersji:

- YOLO/ONNX/OpenVINO jako domyslny silnik produkcyjny,
- rozbudowany panel recznej obslugi podczas interpretacji,
- idealna automatyczna detekcja rak,
- dynamiczne ROI jako glowny mechanizm optymalizacji,
- przepisywanie calego `main.py` od zera.

## Model stanow

Nowy watcher powinien pracowac jako prosta maszyna stanow:

```text
HOLDING_LAST_GOOD
  -> MOTION_DETECTED
  -> SETTLING
  -> SAMPLING_SNAPSHOTS
  -> QUALITY_CHECK
  -> ANALYZING_SNAPSHOT
  -> PUBLISHING_LAYOUT
  -> HOLDING_LAST_GOOD
```

Znaczenie stanow:

- `HOLDING_LAST_GOOD`: brak aktywnej analizy, overlay pokazuje ostatni zatwierdzony uklad.
- `MOTION_DETECTED`: watcher wykryl istotna zmiane obrazu; nie rozpoznajemy jeszcze kart.
- `SETTLING`: system czeka, az scena bedzie spokojna przez wymagany czas.
- `SAMPLING_SNAPSHOTS`: po stabilizacji pobieramy kilka klatek kontrolnych.
- `QUALITY_CHECK`: odrzucamy klatki ewidentnie nieczytelne.
- `ANALYZING_SNAPSHOT`: ciezszy pipeline CV dziala na jednej wybranej klatce.
- `PUBLISHING_LAYOUT`: backend wysyla kompletny nowy stan ukladu do przegladarki.

## Parametry startowe

Startujemy konserwatywnie, bo stabilnosc jest wazniejsza niz szybkosc.

```text
settle_seconds = 3.0
sample_count = 3
sample_interval_ms = 250
publish_only_if_changed = true
```

Parametry do strojenia po testach:

- `motion_threshold`: jak duza zmiana obrazu oznacza ruch,
- `quiet_threshold`: jak maly ruch oznacza stabilna scene,
- `settle_seconds`: wymagany czas ciszy po ruchu,
- `sample_count`: liczba snapshotow kontrolnych,
- `sample_interval_ms`: odstep miedzy snapshotami,
- `quality_min_score`: minimalna ocena czytelnosci klatki.

## Ocena jakosci snapshotu

Pierwsza wersja powinna miec prosta, deterministyczna ocene:

- ostrosc przez wariancje Laplacianu,
- stabilnosc wzgledem sasiednich probek,
- jasnosc i kontrast w dopuszczalnym zakresie,
- liczba kandydatow prostokatow kart, jesli detektor jest dostepny,
- brak duzej naglej zaslony w centralnej czesci stolu, jesli da sie to wykryc tanio.

Jezeli wszystkie probki sa slabe, system nie publikuje nowego ukladu. Overlay trzyma ostatni dobry wynik, a log diagnostyczny zapisuje powod odrzucenia.

## Payload do frontendu

Backend powinien wysylac pelny stan ukladu jako snapshot layout, na przyklad:

```json
{
  "detected": true,
  "layout_id": 17,
  "source": "snapshot",
  "state": "holding_last_good",
  "stable_for_ms": 3040,
  "analysis_ms": 420,
  "quality_score": 0.82,
  "cards": [
    {
      "name": "00_fool",
      "x": 1.2,
      "y": -0.4,
      "angle": 0.03,
      "confidence": 0.91
    }
  ]
}
```

Frontend nie powinien czyscic kart tylko dlatego, ze watcher widzi ruch albo backend jest w stanie `SETTLING`. Karty znikaja albo zmieniaja pozycje dopiero po opublikowaniu nowego zatwierdzonego ukladu.

## Metryki

Nowa diagnostyka powinna mierzyc:

- `snapshot_gate_state`,
- `motion_changed_ratio`,
- `stable_for_ms`,
- `snapshot_samples_taken`,
- `snapshot_rejected_count`,
- `snapshot_reject_reason`,
- `snapshot_quality_score`,
- `snapshot_analysis_ms`,
- `layout_publish_count`,
- `layout_changed`,
- `time_from_motion_to_publish_ms`.

Te metryki sa wazniejsze niz surowy FPS, bo celem nie jest 30 FPS, tylko przewidywalny i poprawny moment publikacji.

## Obsluga bledow

- Jesli kamera dziala, ale snapshot jest slaby, system trzyma ostatni dobry uklad.
- Jesli analiza snapshotu nie znajduje kart, system nie usuwa automatycznie overlayu po pojedynczej nieudanej probie.
- Jesli kilka kolejnych stabilnych snapshotow wskazuje pusty stol, dopiero wtedy mozna opublikowac pusty uklad.
- Jesli WebSocket chwilowo nie dziala, backend zachowuje ostatni zatwierdzony layout i publikuje go po ponownym polaczeniu.

## Testy akceptacyjne

Pierwszy milestone uznajemy za udany, gdy:

- po polozeniu lub przesunieciu karty overlay aktualizuje sie automatycznie po okolo 3 sekundach stabilnosci,
- ruch reki nie powoduje natychmiastowego publikowania blednego ukladu,
- overlay trzyma ostatni dobry wynik podczas ruchu,
- system nie publikuje nowego layoutu, gdy wszystkie snapshoty sa rozmazane albo zasloniete,
- metryki pokazuja czas od wykrycia ruchu do publikacji,
- mozna zmniejszac `settle_seconds` w testach bez zmiany architektury.

## Kolejne kroki

1. Stworzyc plan implementacji snapshot-first jako nowego trybu obok obecnego pipeline.
2. Dodac testowalny modul gate, np. `snapshot_gate.py`, bez zaleznosci od kamery.
3. Dodac wrapper analizujacy pojedyncza klatke istniejacymi narzedziami CV.
4. Zmienic payload tak, aby frontend rozroznial stan watchera od zatwierdzonego layoutu.
5. Przeprowadzic test live z 3-5 kartami i parametrem `settle_seconds = 3.0`.
