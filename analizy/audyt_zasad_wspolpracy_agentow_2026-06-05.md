# Audyt zasad współpracy agentów AI

Data: 2026-06-05
Autor: Codex
Branch: `codex/project-mvp-recovery-audit-2026-06-05`

## Wniosek

Obecne zasady współpracy są zbyt ciężkie dla codziennej pracy nad kodem. Dobrze chronią projekt przed chaosem, ale jednocześnie tworzą nadmiarowe bramki decyzyjne: agent często traktuje review Supervisora jako warunek działania, zamiast jako narzędzie kontroli zmian podwyższonego ryzyka.

Rekomendowana zmiana: przejść na model **autonomii domyślnej z progami ryzyka**.

## Problem w obecnych zasadach

### 1. Supervisor stał się domyślnym gatekeeperem

W `AGENTS.md` sekcja workflow Gemini -> Codex/ChatGPT Review opisuje review jako docelowy model większych etapów. W praktyce zostało to zinterpretowane szerzej: nawet małe zadania zaczęły generować raporty, formalne decyzje i oczekiwanie na akceptację.

Skutek:

- wolniejszy feedback loop,
- więcej dokumentowania niż pracy produktowej,
- trudność w szybkim poprawianiu prostych błędów,
- przeniesienie odpowiedzialności z wykonawcy na Supervisora.

### 2. Każda sesja wymagała podobnego ciężaru dokumentacyjnego

Zasada aktualizacji planu, README, `STATE.md`, `CHANGELOG.md` i `TEST_REPORT.md` po każdej sesji jest sensowna dla tasków przekazywanych między modelami, ale przesadna dla małych poprawek.

Skutek:

- wzrost kosztu każdej małej zmiany,
- inflacja tasków i raportów,
- rozproszenie uwagi z MVP.

### 3. Brak progów ryzyka

Obecne zasady rozróżniają drobne, średnie i duże decyzje, ale nie definiują operacyjnie, kiedy agent może samodzielnie kodować, commitować i pushować.

Skutek:

- agenci wolą eskalować zbyt wcześnie,
- review jest nadużywane,
- Michał musi częściej rozstrzygać kwestie, które powinny być wykonawcze.

## Nowy model

### Green Lane — agent działa samodzielnie

Agent może samodzielnie implementować, testować, commitować i pushować, jeśli zmiana:

- mieści się w celu użytkownika,
- dotyczy małego lub średniego zakresu,
- nie zmienia publicznego API poza lokalnym modułem,
- nie kasuje danych ani plików użytkownika,
- nie zmienia architektury, stacku ani modelu produktu,
- ma jasną weryfikację lokalną.

Przykłady:

- poprawka błędu w istniejącym module,
- dodanie testu,
- drobny refaktor bez zmiany zachowania,
- aktualizacja dokumentacji,
- naprawa UI bez zmiany kontraktu backendu.

Supervisor nie jest wymagany.

### Yellow Lane — agent działa, ale oznacza ryzyko

Agent może wykonać pracę na branchu, ale powinien oznaczyć review jako rekomendowane przed merge, jeśli zmiana:

- dotyka kilku modułów naraz,
- zmienia zachowanie runtime,
- dodaje nowy moduł,
- zmienia protokół lub kontrakt między frontendem i backendem,
- wpływa na fizyczny workflow operatora,
- ma niepełną weryfikację.

Supervisor review jest rekomendowane przed merge, ale nie blokuje samej pracy nad kodem.

### Red Lane — wymagana decyzja Michała przed zmianą albo merge

Agent nie powinien samodzielnie wykonywać lub mergować zmian, jeśli obejmują:

- zmianę architektury,
- zmianę stacku,
- usunięcie dużych fragmentów kodu,
- usunięcie testów,
- zmianę modelu produktu,
- operacje destrukcyjne na danych,
- zmianę zasad bezpieczeństwa,
- merge do `master`.

Tu Supervisor może pomóc w review, ale finalna decyzja należy do Michała.

## Nowa rola Supervisora

Supervisor nie powinien być stałą bramką przed pracą. Jego rola:

- niezależny review zmian podwyższonego ryzyka,
- red-team architektury,
- pomoc przy sporach między agentami,
- kontrola przed merge do `master`,
- audyt, gdy testy nie pokrywają realnego ryzyka.

Supervisor nie powinien być wymagany dla każdej implementacji, każdego commita i każdego pushu na branch roboczy.

## Minimalny standard dla agentów

Każdy agent nadal musi:

- czytać kontekst projektu w zakresie potrzebnym do zadania,
- sprawdzić `git status`,
- nie niszczyć cudzych lokalnych zmian,
- działać na branchu roboczym,
- uruchomić adekwatną weryfikację,
- zapisać trwały handoff, jeśli praca jest duża, ryzykowna albo ma być przejęta przez inny model.

Ale agent nie musi:

- czekać na Supervisora przed kodowaniem,
- tworzyć pełnego raportu dla małej poprawki,
- aktualizować README przy każdej drobnej zmianie,
- tworzyć task metadata dla każdej jednoetapowej poprawki,
- oznaczać każdej zmiany jako `APPROVED_BY_CHATGPT_SUPERVISOR`.

## Efekt oczekiwany

Nowy model powinien skrócić pętlę pracy:

1. Agent rozumie zadanie.
2. Agent klasyfikuje ryzyko: Green / Yellow / Red.
3. Dla Green robi zmianę i weryfikuje.
4. Dla Yellow robi zmianę, ale oznacza potrzebę review przed merge.
5. Dla Red zatrzymuje się przed decyzją architektoniczną albo destrukcyjną.

To zachowuje jakość, ale usuwa paraliż decyzyjny.
