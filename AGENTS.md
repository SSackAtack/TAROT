# AGENTS.md — Zasady Pracy Zespolu AI

> **Ten plik jest OBOWIAZKOWY do przeczytania przez kazdego agenta AI przed rozpoczeciem pracy.**
> Dotyczy kazdego modelu (Codex, Opus, Gemini, i kazdy inny) niezaleznie od narzedzia (Antigravity, Cursor, CLI, API).

---

## Required startup sequence for AI agents

Before coding:

1. Read `.ai/PROJECT_STATE.md`.
2. Read `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`.
3. Read `.ai/TASKS_INDEX.md`.
4. If the task has an assigned `.ai/tasks/TASK-XXX/TASK.md`, read it.
5. Check `git status` and identify local changes that must not be overwritten.
6. Confirm the practical scope from the user request, current branch and nearby code.
7. For small Green Lane tasks, a dedicated task folder is optional; use commit message, tests and a short final handoff.
8. For Yellow/Red Lane tasks or work that another agent must continue, update `STATE.md`, `CHANGELOG.md` and `TEST_REPORT.md`.

---

## 1. Zespol

Nad projektem TarotVision pracuje **zespol kilku modeli AI** koordynowanych przez czlowieka (Michal). Kazdy model moze w dowolnym momencie przejac kontynuacje prac rozpoczetych przez inny model.

Aktualny sklad:
- **Codex** (OpenAI) — glownie praca offline/batch, implementacja modulow, testy
- **Opus** (Anthropic Claude) — sesje interaktywne, architektura, code review, debugging
- **Gemini** (Google DeepMind) — sesje interaktywne, planowanie, research, integracja

Sklad moze sie zmieniac. Nowe modele moga dolaczyc w dowolnym momencie.

---

## 2. Zasada Naczelna

> **Jestesmy spojnym zespolem. Nasz cel to dostarczenie najlepszego produktu.
> Nie rywalizujemy — dzialamy na zasadzie synergii i syntezy pracy i pomyslow.**

---

## 3. Reguly Wspolpracy

### 3.1 Czytelnosc dla Nastepcy

Kazdy commit, komentarz, plan i decyzja architektoniczna musza byc zrozumiale dla modelu, ktory **nie uczestniczyl** w biezacej sesji. Pisz tak, jakby nastepna osoba czytajaca Twoj kod widziala go pierwszy raz.

Konkretnie:
- **Komentarze w kodzie**: wyjasniaj *dlaczego*, nie tylko *co*. Nastepny model moze nie znac kontekstu decyzji.
- **Commity**: opisowe komunikaty z kontekstem. Nie `fix bug`, lecz `fix: karta 15_devil traci tracking przy niskim IoU — zwieksz margines inflate_box`.
- **Plany**: kazdy plan musi zawierac sekcje `Stan aktualny`, `Co zostalo zrobione`, `Kolejne kroki` — tak zeby mozna go czytac bez znajomosci historii czatu.

### 3.2 Dokumentacja Sesji

Dokumentacja ma utrwalac decyzje, a nie blokowac szybka prace. Po sesji roboczej agent dobiera ciezar dokumentacji do ryzyka:

- **Green Lane / mala zmiana**: wystarcza czytelny commit, adekwatne testy i krotki finalny handoff w czacie.
- **Yellow Lane / srednia zmiana**: zaktualizuj task, plan albo raport, jesli praca ma byc przejeta przez inny model lub wymaga review przed merge.
- **Red Lane / duza decyzja**: zapisz plan/analize i uzyskaj decyzje Michala przed zmiana architektury, stacku, danych lub merge do `master`.
- **README** aktualizuj tylko wtedy, gdy zmienily sie instrukcje uruchomienia, architektura, metryki projektu albo zachowanie widoczne dla operatora.
- **Commit + push** wykonuj po zakonczonej, zweryfikowanej pracy na branchu roboczym, chyba ze Michal wyraznie chce pozostawic zmiany lokalnie.

### 3.3 Konwencje Kodu

- **Jezyk kodu**: angielski (nazwy zmiennych, funkcji, klas, komentarze techniczne inline).
- **Jezyk dokumentacji**: polski (README, plany, opisy commitow, komentarze architektoniczne).
- **Testy**: kazdy nowy modul musi miec testy jednostkowe w `app_cv/tests/`.
- **Istniejace komentarze**: nie usuwaj komentarzy innych autorow, chyba ze kod sie zmienil i komentarz jest nieaktualny.

### 3.4 Podejmowanie Decyzji

- **Green Lane — autonomia domyslna**: agent moze samodzielnie implementowac, testowac, commitowac i pushowac zmiany niskiego ryzyka w zakresie zadania. Dotyczy to m.in. poprawek bugow, testow, dokumentacji, lokalnych refaktorow i zmian bez publicznego API.
- **Yellow Lane — praca samodzielna, review przed merge rekomendowane**: agent moze pracowac na branchu, ale oznacza ryzyko w handoffie, jesli zmiana dotyka kilku modulow, runtime, kontraktu frontend/backend, nowego modulu albo ma niepelna weryfikacje.
- **Red Lane — decyzja Michala wymagana**: zmiana architektury, stacku, modelu produktu, operacje destrukcyjne, usuwanie testow, kasowanie danych, duze usuniecia kodu i merge do `master`.
- **Nigdy nie usuwaj kodu innego modelu** bez wyjasnienia dlaczego i co go zastepuje.

### 3.5 Napotkane Problemy

Jesli napotkasz problem lub niejasnosc w kodzie innego modelu:
1. **Nie przepisuj od zera** — najpierw zrozum intencje.
2. **Dodaj komentarz** wyjasniajacy problem (np. `# TODO(zespol): ten prog moze byc za niski — do weryfikacji w Task 8`).
3. **Opisz w planie** co wymaga dyskusji.

### 3.6 Autonomia agentow i review

Docelowy model pracy to **autonomia domyslna z progami ryzyka**.

- Kazdy agent moze samodzielnie pracowac nad kodem w Green Lane.
- Supervisor review nie jest wymagany przed kazda implementacja, kazdym commitem ani kazdym pushem na branch roboczy.
- Review ChatGPT/Codex jest narzedziem dla zmian Yellow/Red Lane, pracy spornej, audytu jakosci albo kontroli przed merge do `master`.
- Gemini, Codex i Opus moga wykonywac kompletne taski end-to-end, jesli mieszcza sie w zakresie i maja adekwatna weryfikacje.
- **Michal podejmuje decyzje produktowe, architektoniczne i Red Lane**: modele moga rekomendowac i samodzielnie realizowac Green/Yellow Lane na branchu roboczym, ale Red Lane i merge do `master` wymagaja akceptacji Michala zgodnie z sekcja 3.4.

Agent konczacy Yellow/Red Lane task albo proszacy o review przekazuje krotki pakiet, zamiast pelnego strumienia rozumowania:

```markdown
Review Task X: <nazwa>
Base: <commit przed taskiem>
Head: <commit po tasku>
Zakres:
- <najwazniejsza zmiana 1>
- <najwazniejsza zmiana 2>

Weryfikacja wykonana przez Gemini:
- <komenda testowa> => PASS/FAIL
- <komenda build/compile> => PASS/FAIL

Pliki zmienione:
- <sciezka 1>
- <sciezka 2>

Znane ryzyka / decyzje do review:
- <ryzyko albo "brak">
```

Reviewer odpowiada w stalym, oszczednym formacie:

```markdown
LIGHT: GREEN | YELLOW | RED
BLOCKERS: <tylko problemy blokujace>
VERIFY: <co Codex faktycznie sprawdzil>
NEXT: <kolejny bezpieczny krok>
```

Szczegółowy standard przekazywania informacji przez GitHub opisuje `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md`.

Zasady optymalizacji tokenow:
- Agent wykonawczy sam odpowiada za podstawowa weryfikacje swojej zmiany.
- Reviewer w pierwszej kolejnosci analizuje `git diff`, nowe/zmienione testy, punkty integracji i ryzyka runtime.
- Pelny opis zmian jest wymagany tylko przy `RED light`, zmianie architektury, zmianie publicznego API albo gdy testy nie pokrywaja ryzyka.
- Nie duplikujemy dlugich opisow w czacie, jesli sa juz zapisane w planie wykonawczym lub commitach.

---

## 4. Struktura Planow i Dokumentacji

```
.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md — standard komunikacji między modelami AI przez GitHub
docs/superpowers/plans/     — plany wykonawcze (roadmapa, state-first plan, itp.)
analizy/                    — raporty analityczne i synteza
README.md                   — glowna dokumentacja projektu
AGENTS.md                   — ten plik (reguly zespolu)
```

Kazdy plan wykonawczy powinien miec format:
```markdown
# Tytul planu

## Status ogolny
Krotki opis: co jest zrobione, co zostaje.

## Session Status (DATA)
Co zrobiono w tej sesji, kto pracowal, commit hash.

## Taski
- [x] Task 1: ...
- [ ] Task 2: ...

## Kolejne kroki
Natychmiastowe nastepne dzialanie dla nastepnego modelu.
```

---

## 5. Workflow Git

- **Branch glowny**: `master` — stabilny kod.
- **Branch roboczy**: np. `codex-state-first-cv-roadmap` — prace w toku.
- **Merge do master**: tylko po akceptacji Michala.
- **Kazdy model pushuje na swoj branch** lub kontynuuje na branchu innego modelu jesli to kontynuacja prac.

---

## 6. Czego NIE Robic

- ❌ Nie przepisuj kodu innego modelu "bo bym zrobil to lepiej" — zaproponuj refaktor z uzasadnieniem.
- ❌ Nie usuwaj testow — nawet jesli wydaja Ci sie nadmiarowe.
- ❌ Nie zmieniaj interfejsow publicznych modulow bez aktualizacji wszystkich uzyc.
- ❌ Nie commituj kodu bez uruchomienia testow (`python -m unittest discover app_cv/tests`).
- ❌ Nie ignoruj istniejacych planow — przeczytaj je zanim zaczniesz nowa prace.
- ❌ Nie wymuszaj review Supervisora dla kazdej malej zmiany Green Lane.
- ❌ Nie ignoruj `.ai/AI_AGENT_COMMUNICATION_PROTOCOL.md` przy przekazywaniu pracy między modelami.

---

*Ostatnia aktualizacja: 2026-06-05 | Autorzy: Opus (Anthropic Claude), Codex (OpenAI), Gemini (Google DeepMind)*
*Zatwierdzil: Michal*
