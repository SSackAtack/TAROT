@echo off
title TarotVision - Automatyczna Obrobka Skanow
chcp 65001 >nul

echo =======================================================================
echo              TarotVision - Automatyczny Procesor Skanow
echo =======================================================================
echo.
echo Ten skrypt automatycznie wytnie, wyprostuje i przygotuje Twoje karty.
echo.
echo =======================================================================
echo KROK 1: Sprawdzanie plików wejsciowych w scans_input...
echo -----------------------------------------------------------------------

set "has_files=0"
if not exist scans_input mkdir scans_input

for %%i in (scans_input\*.jpg scans_input\*.jpeg scans_input\*.png scans_input\*.tiff scans_input\*.tif) do (
    set "has_files=1"
)

if "%has_files%"=="1" (
    echo [SUKCES] Znaleziono Twoje pliki skanow w scans_input.
    goto PROCESS_NOW
)

echo [INFO] Brak plików skanow w scans_input!
echo.
echo Czy chcesz wygenerowac syntetyczne skany testowe (Fool, Magician itd.),
echo aby od razu przetestowac dzialanie i zobaczyc jak wyglada podglad?
echo.
set /p "choice=Wpisz T (Tak) lub N (Nie) i nacisnij Enter: "

if /i "%choice%"=="T" (
    echo.
    echo Generowanie syntetycznego zestawu testowego...
    python scripts/generate_test_scan.py
    goto PROCESS_NOW
) else (
    echo.
    echo [INFO] Umiesc pliki ze skanera w scans_input i uruchom ten skrypt ponownie.
    pause
    exit /b
)

:PROCESS_NOW
echo.
echo =======================================================================
echo KROK 2: Uruchamianie ultra-precyzyjnej obrobki...
echo -----------------------------------------------------------------------
echo Parametry: Autodetekcja tla, bezstratny PNG, podglad debug_*.jpg
echo.

python scripts/process_scans.py scans_input scans_output --background auto --format png --naming generic --debug-overlay

if %errorlevel% neq 0 (
    echo.
    echo [BLAD] Wystapil problem podczas przetwarzania skanow!
    echo Upewnij sie, ze zainstalowales biblioteki uruchamiajac install_dependencies.bat
    pause
    exit /b
)

echo.
echo =======================================================================
echo KROK 3: Otwieranie katalogu z wycietymi kartami...
echo -----------------------------------------------------------------------
echo Za chwile otworzy sie folder scans_output.
echo Zobaczysz tam wyciete karty oraz obrazy debug_*.jpg z podgladem detekcji!
echo.

explorer scans_output

echo =======================================================================
echo              PROCES ZAKONCZONY POWODZENIEM!
echo =======================================================================
echo Zrobione! Karty zostaly wyciete. Nacisnij klawisz, aby zamknac...
echo =======================================================================
pause >nul
