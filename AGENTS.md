# AGENTS.md — Zasady Pracy Zespolu AI

> **Ten plik jest OBOWIAZKOWY do przeczytania przez kazdego agenta AI przed rozpoczeciem pracy.**
> Dotyczy kazdego modelu (Codex, Opus, Gemini, i kazdy inny) niezaleznie od narzedzia (Antigravity, Cursor, CLI, API).

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

Po kazdej sesji roboczej (niezaleznie od modelu) nalezy:

1. **Zaktualizowac plan wykonawczy** (`docs/superpowers/plans/`) — oznaczyc wykonane taski, dodac sekcje `Session Status` z data i opisem.
2. **Zaktualizowac README** jesli zmienily sie metryki, architektura lub instrukcje uruchomienia.
3. **Commit + push** — nie zostawiaj niezacommitowanych zmian.

### 3.3 Konwencje Kodu

- **Jezyk kodu**: angielski (nazwy zmiennych, funkcji, klas, komentarze techniczne inline).
- **Jezyk dokumentacji**: polski (README, plany, opisy commitow, komentarze architektoniczne).
- **Testy**: kazdy nowy modul musi miec testy jednostkowe w `app_cv/tests/`.
- **Istniejace komentarze**: nie usuwaj komentarzy innych autorow, chyba ze kod sie zmienil i komentarz jest nieaktualny.

### 3.4 Podejmowanie Decyzji

- **Drobne decyzje** (nazewnictwo, refaktor lokalny): podejmuj samodzielnie, opisz w ucommicie.
- **Srednie decyzje** (nowy modul, zmiana API): opisz w planie, poczekaj na akceptacje Michala.
- **Duze decyzje** (zmiana architektury, nowa biblioteka, zmiana stacku): opisz w planie z analiza za/przeciw, poczekaj na akceptacje Michala.
- **Nigdy nie usuwaj kodu innego modelu** bez wyjasnienia dlaczego i co go zastepuje.

### 3.5 Napotkane Problemy

Jesli napotkasz problem lub niejasnosc w kodzie innego modelu:
1. **Nie przepisuj od zera** — najpierw zrozum intencje.
2. **Dodaj komentarz** wyjasniajacy problem (np. `# TODO(zespol): ten prog moze byc za niski — do weryfikacji w Task 8`).
3. **Opisz w planie** co wymaga dyskusji.

### 3.6 Workflow Gemini -> Codex/ChatGPT Review

Docelowy model pracy przy wiekszych etapach:

- **Gemini jest wykonawca tokenochlonnych dzialan**: moze robic szerokie analizy, czytac duze fragmenty repozytorium, uruchamiac pelne testy, budowac frontend, porownywac warianty i przygotowywac obszerne notatki robocze.
- **Codex/ChatGPT jest kuratorem i audytorem jakosci**: po zakonczonym tasku robi niezalezny review zmian, weryfikuje ryzyka regresji, sprawdza zgodnosc z planem i wydaje decyzje `green/yellow/red light`.
- **Michal podejmuje decyzje produktowe i architektoniczne**: modele moga rekomendowac, ale srednie i duze decyzje nadal wymagaja akceptacji Michala zgodnie z sekcja 3.4.

Gemini po kazdym tasku przekazuje Codexowi krotki pakiet review, zamiast pelnego strumienia rozumowania:

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

Codex/ChatGPT odpowiada w stalym, oszczednym formacie:

```markdown
LIGHT: GREEN | YELLOW | RED
BLOCKERS: <tylko problemy blokujace>
VERIFY: <co Codex faktycznie sprawdzil>
NEXT: <kolejny bezpieczny krok>
```

Zasady optymalizacji tokenow:
- Gemini wykonuje szerokie, tokenochlonne sprawdzenia i streszcza wynik.
- Codex/ChatGPT w pierwszej kolejnosci analizuje `git diff`, nowe/zmienione testy, punkty integracji i ryzyka runtime.
- Pelny opis zmian jest wymagany tylko przy `RED light`, zmianie architektury, zmianie publicznego API albo gdy testy nie pokrywaja ryzyka.
- Nie duplikujemy dlugich opisow w czacie, jesli sa juz zapisane w planie wykonawczym lub commitach.

---

## 4. Struktura Planow i Dokumentacji

```
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

---

*Ostatnia aktualizacja: 2026-05-30 | Autorzy: Opus (Anthropic Claude), Codex (OpenAI)*
*Zatwierdzil: Michal*
