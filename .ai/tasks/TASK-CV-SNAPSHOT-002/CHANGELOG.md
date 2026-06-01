# CHANGELOG: TASK-CV-SNAPSHOT-002

## 2026-06-01

- Dodano `imread_unicode`, `imread_grayscale_unicode` i `imwrite_unicode`.
- Dodano `ReferenceLoadResult` oraz `load_active_reference_cards()`.
- Przeniesiono ladowanie wzorcow aktywnych talii z `main.py` do `reference_loader.py`.
- Zmieniono `card_recognition.load_reference_cards()` na Unicode-safe odczyt obrazow.
- Dodano testy dla polskich sciezek i diagnostyki nieczytelnych wzorcow.
