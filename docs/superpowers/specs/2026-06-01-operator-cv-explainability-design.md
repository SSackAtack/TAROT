# Operator CV Explainability Design

## Status ogolny

Zaakceptowany wariant: **B. Prowadzona diagnostyka z przyczynami i nastepnym krokiem**.

## Stan aktualny

Studio Console pokazuje podstawowy `CV Health` oraz pojedynczy ostatni komunikat warning. Operator widzi, ze system ma problem, ale nie dostaje uporzadkowanej odpowiedzi, gdzie w pipeline wystapil problem i co zrobic jako nastepny krok.

Backend publikuje juz metryki, runtime, layout, operator warnings i aktywne talie w payloadzie WebSocket. Snapshot-first pipeline posiada stany typu `settling`, `sampling_snapshots`, `analyzing_snapshot`, `holding_last_good` oraz diagnostyki detekcji/rozpoznania, ktore mozna wykorzystac bez zmiany glownego protokolu sterowania.

## Cel

Dac operatorowi czytelny panel `CV Explain`, ktory pokazuje:

- status ArUco,
- status snapshotu,
- liczbe kandydatow kart,
- status rozpoznania,
- aktywne talie,
- jeden konkretny nastepny krok.

## Zakres

Zmiana obejmuje maly, stabilny panel w prawym sidebarze Studio, pod istniejacym `CV Health`. Panel nie zmienia silnika rozpoznawania kart i nie dodaje nowych bibliotek.

## Architektura

Backend doda do payloadu statusu obiekt `operator.explainability`. Obiekt bedzie skladal sie z listy krokow diagnostycznych oraz pola `next_action`.

Frontend Studio wyrenderuje ten obiekt w nowej sekcji `CV Explain`. Gdy backend nie wysle `operator.explainability`, frontend pokaze bezpieczny fallback oparty o istniejace pola `layout`, `cards`, `warnings` i `operator.active_decks`.

## Format danych

```json
{
  "operator": {
    "explainability": {
      "severity": "ok | warn | error",
      "next_action": "Zostaw mate nieruchomo 3s",
      "steps": [
        {
          "id": "aruco",
          "label": "ArUco",
          "state": "ok | warn | error | wait",
          "value": "4/4",
          "message": "Stol skalibrowany"
        }
      ]
    }
  }
}
```

## Reguly diagnostyczne MVP

1. Brak aktywnych talii: `error`, next action: wybierz 1-3 talie w Studio.
2. Layout `no_camera`: `error`, next action: sprawdz kamere i launcher CV.
3. Brak kalibracji ArUco lub zbyt malo markerow: `warn/error`, next action: pokaz wszystkie markery ArUco w kadrze.
4. Snapshot w stanie `settling` lub `sampling_snapshots`: `wait/warn`, next action: zostaw mate nieruchomo przez kilka sekund.
5. Brak kandydatow kart: `warn`, next action: popraw swiatlo, kontrast albo polozenie kart.
6. Karty wykryte i zaakceptowane: `ok`, next action: mozna prowadzic sesje.
7. Ostatni warning backendu jest zachowany jako kontekst pomocniczy, ale nie zastepuje uporzadkowanej diagnostyki.

## UI

Panel ma byc zwarty i pasowac do istniejacego stylu Studio:

- naglowek `CV Explain`,
- mala plakietka statusu `OK`, `UWAGA`, `BLAD` albo `WAIT`,
- lista 4-5 krokow z ikona tekstowa: `✓`, `•`, `!`, `×`,
- dolny boks `Nastepny krok`.

## Testy

- Test backendowy: builder explainability zwraca oczekiwane `next_action` dla braku talii, `no_camera`, oczekiwania na snapshot i poprawnego rozpoznania.
- Test status store / payload: `operator.explainability` przechodzi przez `update_cv_state`.
- Test statyczny frontendu: `studioConsole.js` zawiera sekcje `CV Explain`, renderowanie `next_action` i klasy stanu.

## Kolejne kroki

1. Utworzyc plan implementacji TDD.
2. Dodac backendowy builder explainability.
3. Podlaczyc builder do payloadu runtime.
4. Dodac panel w Studio.
5. Uruchomic testy backendowe i build frontendu.
