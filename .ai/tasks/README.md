# Zadania AI (Tasks Directory)

W tym katalogu gromadzone są szczegółowe informacje o poszczególnych zadaniach realizowanych przez zespół sztucznej inteligencji.

Każde zadanie ma własny folder o nazwie odpowiadającej jego identyfikatorowi (np. `TASK-WF-001/`).

---

## Zalecana struktura katalogu zadania:
```text
TASK-XXX/
├── TASK.md          # Cel, szczegółowe wymagania i zakres modyfikowanych plików (Scope)
├── STATE.md         # Aktualny status prac (Co zrobiono, co zostało do zrobienia)
├── CHANGELOG.md     # Spis wprowadzonych modyfikacji i dotkniętych plików produkcyjnych
├── TEST_REPORT.md   # Raport z przebiegu testów jednostkowych i kompilacji
├── GEMINI_NOTES.md  # Techniczne przemyślenia i notatki Gemini dla kolejnego agenta
└── OPEN_ISSUES.md   # Otwarte pytania i problemy techniczne wymagające decyzji ludzkiej
```

Szablony powyższych plików znajdują się w katalogu `_TEMPLATE/`. Przed rozpoczęciem nowego zadania, skopiuj całą strukturę szablonów i stwórz na jej bazie katalog dedykowany nowemu zadaniu.
