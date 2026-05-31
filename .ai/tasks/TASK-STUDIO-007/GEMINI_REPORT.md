Review Task STUDIO-007: Uodpornienie launchera Studio pod zajęty port 5173
Base: master (73bb07edb4e13cd77efba1936c6bb1b590059c25)
Head: task/studio-007-port-hardening (current branch)

Zakres:
- Detekcja zajętości portu deweloperskiego `5173` za pomocą zintegrowanego skryptu PowerShell przed startem serwera AR.
- Wdrożenie interaktywnego, jasnoczerwonego menu ostrzegawczego w przypadku detekcji kolizji.
- Udostępnienie operatorowi 3 opcji: automatycznego zamknięcia starej sesji, kontynuacji na własne ryzyko, bądź bezpiecznego anulowania rozruchu systemu (rekomendowane i domyślne).

Weryfikacja wykonana przez Gemini:
- Ręczne testy logiczne sprawdzania portów na środowisku Windows -> PASS
- Detekcja i autoubicie wiszących procesów Node/Vite -> PASS
- Wyjście awaryjne przy zablokowanym porcie -> PASS

Pliki zmienione:
- `start_tarotvision_studio.bat`
- `.ai/TASKS_INDEX.md`

Znane ryzyka / decyzje do review:
- **Residual Risk: LOW**
  - *Zgodność polecenia Get-NetTCPConnection*: Komenda ta jest standardowo dostępna we wbudowanym PowerShellu systemów Windows 8/10/11. W przypadku bardzo starych edycji systemu (np. Windows 7 ze starym PowerShell v2), wywołanie to zwróci błąd. Dzięki zastosowaniu parametru `-ErrorAction SilentlyContinue`, skrypt wyciszy błąd i bezpiecznie przejdzie do domyślnej procedury startowej bez blokowania działania operatora (fail-soft).
