# AI Workflow Failover — Zasady Pracy Zespołu AI i Przejmowania Zadań

Ten dokument określa rygorystyczne reguły współpracy zespołu sztucznej inteligencji (AI) pracującego nad projektem **TarotVision (TAROT)**. Zapewnia on bezproblemowe i bezpieczne przejmowanie zadań (failover) przez różne modele AI w dowolnym momencie.

---

## 1. Role i Struktura Zespołu

* **Właściciel Projektu (Michał):** Jedyny decydent i kurator projektu. Każdy merge do gałęzi `master` wymaga jego wyraźnej zgody i akceptacji.
* **Główny Wykonawca Kodu (Gemini / Antigravity):** Model odpowiedzialny za większość prac implementacyjnych, tworzenie kodu, refaktoryzację, pisanie testów i szeroką analizę repozytorium.
* **Audytor i Kurator Jakości (ChatGPT Supervisor / Backup Codex):** Model odpowiedzialny za niezależny przegląd kodu (review), zatwierdzanie commitów w trybie "bramki jakościowej" (GREEN/YELLOW/RED light) oraz weryfikację ryzyk integracyjnych.
* **Reviewerzy Awaryjni (Codex / Opus):** Modele wspierające w trudnych sesjach debugowania, projektowaniu architektury i szybkim review.

---

## 2. Rygorystyczne Zasady Wdrażania (AI Safety & Quality)

1. **Zasada 1–3 Plików Produkcyjnych:**
   Każde pojedyncze zadanie (Task) może modyfikować maksymalnie **od 1 do 3 plików produkcyjnych** w jednym PR/commicie. Chroni to kod przed niekontrolowanymi, rozległymi zmianami.
2. **Zakaz Dużych Refaktorów bez Zgody:**
   Nie wolno przeprowadzać dużych zmian architektonicznych ani refaktoryzacji bez wyraźnego zatwierdzenia przez właściciela (tzw. **Human Override**).
3. **Pętla Informacji Zwrotnej (Test Report):**
   Każde zadanie i każdy Pull Request **musi** zawierać kompletny raport z testów jednostkowych backendu oraz kompilacji frontendu. Brak testów = brak możliwości merge'a.
4. **Ciągłość Pracy (Failover Readiness):**
   Każdy agent AI kończący swoją sesję ma obowiązek pozostawić stan kodu oraz dokumentację w taki sposób, aby kolejny agent mógł wejść w zadanie bez czytania historii poprzednich czatów.

---

## 3. Struktura Dokumentacji Zadań w `.ai/`

Każde zadanie realizowane przez dowolnego agenta musi mieć dedykowany podkatalog w `.ai/tasks/TASK-XXX/`, zawierający pliki opisujące jego cykl życia:

* `TASK.md` — cele, zakres (Scope), pliki dopuszczone do zmiany i kryteria akceptacji.
* `STATE.md` — aktualny status prac, co zostało zrobione, a co zostało do zrobienia.
* `CHANGELOG.md` — precyzyjny spis wprowadzonych zmian i modyfikowanych plików.
* `TEST_REPORT.md` — wyniki testów jednostkowych, kompilacji oraz testów manualnych.
* `GEMINI_NOTES.md` / `OPUS_NOTES.md` — wewnętrzne notatki techniczne i przemyślenia dla kolejnych modeli.
* `OPEN_ISSUES.md` — napotkane problemy, błędy techniczne i decyzje wymagające konsultacji z Michałem.

---

## 4. Procedura Rozpoczęcia Pracy przez Agenta AI

Zanim napiszesz jakikolwiek kod:
1. Odczytaj plik `.ai/PROJECT_STATE.md` — aby zrozumieć ogólny stan projektu.
2. Odczytaj plik `.ai/TASKS_INDEX.md` — aby zlokalizować aktualnie przypisane zadanie.
3. Przeczytaj szczegółowe wytyczne w `.ai/tasks/TASK-XXX/TASK.md`.
4. **Bezwzględnie przestrzegaj dopuszczalnego zakresu (Scope) plików.** Zmiana plików poza zakresem bez zgody jest niedozwolona.
