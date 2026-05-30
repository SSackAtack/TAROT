# Protokół statusu TarotVision (Status Payload v1)

Ten dokument opisuje oficjalny schemat wiadomości stanu (status payload) wysyłanych przez serwer WebSocket w aplikacji TarotVision na frontend AR.

## Założenia ogólne

1. **Jeden standard wiadomości**: Każdy broadcast stanu z serwera na frontend ma ten sam format.
2. **Defensywność**: Brak któregoś pola w JSON nie może spowodować awarii frontendu. Frontend normalizuje payload za pomocą `messageNormalizer.js`.
3. **Wersjonowanie**: Od wersji 1 protokół zawiera klucz `schema_version`.

## Struktura Payloadu (v1)

```json
{
  "schema_version": 1,
  "detected": true,
  "cards": [
    {
      "name": "00_fool",
      "x": 0.12,
      "y": -0.34,
      "angle": 1.57
    }
  ],
  "layout": {
    "layout_id": 1,
    "source": "snapshot",
    "state": "holding_last_good",
    "stable_for_ms": 3040,
    "quality_score": 0.92
  },
  "metrics": {
    "fps": 29.8,
    "matching_ms": 12.4
  },
  "runtime": {
    "profile": "default",
    "camera_index": 0
  },
  "operator": {
    "enabled": true,
    "active_profile": "default",
    "parameters": {},
    "calibration": {
      "state": "idle",
      "last_score": null
    }
  },
  "table": {
    "calibrated": true
  },
  "warnings": [],
  "studio": {
    "recording_state": "idle",
    "recording_id": null,
    "elapsed_ms": 0,
    "dropped_frames": 0,
    "audio_peak_db": null,
    "director_scene": "table"
  }
}
```

### Opis pól sekcji `studio`

- `recording_state` (string): Stan rekordera w studiu. Dopuszczalne wartości:
  - `"idle"`: Rekorder nie pracuje.
  - `"armed"`: Przygotowany do nagrywania (czeka na sygnał startu lub synchronizacji).
  - `"recording"`: W trakcie aktywnego nagrywania.
  - `"stopping"`: Proces zatrzymywania i zapisywania pliku.
  - `"error"`: Stan błędu zapisu/nagrywania.
- `recording_id` (string | null): Unikalny identyfikator nagrania (np. sygnatura czasowa `2026-05-30_13-05-00`).
- `elapsed_ms` (integer): Czas, który upłynął od rozpoczęcia nagrania.
- `dropped_frames` (integer): Liczba zgubionych klatek w procesie kompozycji/nagrywania.
- `audio_peak_db` (float | null): Maksymalny zarejestrowany poziom głośności w decybelach (db).
- `director_scene` (string): Aktualnie aktywny kadr / tryb reżyserski (np. `"table"`, `"wow"`, `"portrait_pip"`, `"title_card"`).
