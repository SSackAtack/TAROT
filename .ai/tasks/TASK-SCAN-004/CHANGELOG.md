# Rejestr Zmian (CHANGELOG) — TASK-SCAN-004

Precyzyjny rejestr zmian wprowadzonych w ramach usprawnienia segmentacji tła i orientacji kart.

## Modyfikowane pliki produkcyjne

### Moduł obróbki skanów
* [scripts/process_scans.py](file:///e:/Antigravity/Projekty/TAROT/scripts/process_scans.py)
  - Dodano funkcję `get_orientation_score` do automatycznej analizy jasności krawędzi karty.
  - Zastąpiono tradycyjną binaryzację szarości Otsu zaawansowanym obliczaniem euklidesowego dystansu barwnego w przestrzeni **CIE L*a*b*** względem mediany tła pobranej z krawędzi skanu.
  - Zintegrowano maskę barwną z krawędziami Canny'ego za pomocą logicznego `OR`.
  - Powiększono kernel morfologicznego domykania konturów (`MORPH_CLOSE`) do rozmiaru `11x11`.
  - Wdrożono wycinanie 4 wariantów pionowych (0°, 180°, 90° CW, 90° CCW) i automatyczny wybór najlepszego obrotu na podstawie scoringu.
  - Rozbudowano logowanie o parametry fizyczne konturów (`area`, `aspect_ratio`, `solidity`, `background_mode`) oraz szczegółowe punktacje wariantów orientacji dla każdej karty.

---

## Dodane pliki dokumentacji AI

* [.ai/tasks/TASK-SCAN-004/TASK.md](file:///e:/Antigravity/Projekty/TAROT/.ai/tasks/TASK-SCAN-004/TASK.md) — Zakres i kryteria akceptacji.
* [.ai/tasks/TASK-SCAN-004/STATE.md](file:///e:/Antigravity/Projekty/TAROT/.ai/tasks/TASK-SCAN-004/STATE.md) — Status zadań.
* [.ai/tasks/TASK-SCAN-004/TEST_REPORT.md](file:///e:/Antigravity/Projekty/TAROT/.ai/tasks/TASK-SCAN-004/TEST_REPORT.md) — Precyzyjny raport z testów.
* [.ai/tasks/TASK-SCAN-004/GEMINI_REPORT.md](file:///e:/Antigravity/Projekty/TAROT/.ai/tasks/TASK-SCAN-004/GEMINI_REPORT.md) — Oficjalny raport końcowy Gemini.
