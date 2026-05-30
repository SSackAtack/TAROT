@echo off
title TarotVision - Centrum Obrobki i Skanowania Kart
chcp 65001 >nul

:MENU
cls
echo =======================================================================
echo              TarotVision - Centrum Skanowania i Obrobki
echo =======================================================================
echo.
echo Wybierz, co chcesz zrobic:
echo.
echo   [1] ASYSTENT SKANOWANIA - Kreator masowego skanowania talii (WIA)
echo       (Prowadzi krok po kroku, umozliwia skan próbny lub calej talii)
echo.
echo   [2] OBROB GOTOWE PLIKI - Kadruje i prostuje obrazy z folderu scans_input
echo.
echo   [3] GENERUJ TESTY - Tworzy syntetyczne karty testowe do weryfikacji
echo.
echo   [4] ZAKONCZ
echo.
echo =======================================================================
set /p "choice=Wpisz numer (1-4) i nacisnij Enter: "

if "%choice%"=="1" goto INTERACTIVE_ASSISTANT
if "%choice%"=="2" goto PROCESS_FILES
if "%choice%"=="3" goto GENERATE_TESTS
if "%choice%"=="4" exit /b
goto MENU

:INTERACTIVE_ASSISTANT
cls
echo =======================================================================
echo      [1] ASYSTENT SKANOWANIA - Kreator masowego skanowania (WIA)
echo =======================================================================
echo.
echo Wymagania: System Windows + sterownik skanera WIA + pywin32.
echo.
echo [UWAGA] Bezposrednie skanowanie WIA w systemie Windows wymusza tymczasowy
echo format JPEG ze wzgledu na ograniczenia systemowych obiektow COM.
echo Dla bezkompromisowej jakosci referencyjnej (Master Quality) kart,
echo zalecamy skanowanie do bezstratnego formatu PNG/TIFF za pomoca
echo oprogramowania od skanera i wybranie opcji [2] OBROB GOTOWE PLIKI.
echo.
echo Uruchamianie interaktywnego asystenta w Pythonie...
python scripts/process_scans.py --interactive --format png --naming generic --debug-overlay

if errorlevel 1 goto ERROR_OCCURRED
goto MENU

:PROCESS_FILES
cls
echo =======================================================================
echo      [2] OBROB GOTOWE PLIKI - Przetwarzanie folderu scans_input
echo =======================================================================
echo.
echo Sprawdzanie plików wejsciowych w scans_input...
echo.

set "has_files=0"
if not exist scans_input mkdir scans_input

for %%i in (scans_input\*.jpg scans_input\*.jpeg scans_input\*.png scans_input\*.tiff scans_input\*.tif) do (
    set "has_files=1"
)

if "%has_files%"=="1" (
    echo [SUKCES] Znaleziono Twoje pliki skanow w scans_input.
    goto DO_PROCESS
)

echo [INFO] Brak plikow w scans_input!
echo Umiesc tam najpierw pliki ze swojego skanera.
echo.
pause
goto MENU

:DO_PROCESS
echo.
echo Uruchamianie ultra-precyzyjnej obrobki...
python scripts/process_scans.py scans_input scans_output --background auto --format png --naming generic --debug-overlay
if errorlevel 1 goto ERROR_OCCURRED
goto PROCESS_SUCCESS

:GENERATE_TESTS
cls
echo =======================================================================
echo      [3] GENERUJ TESTY - Tworzenie syntetycznych plikow testowych
echo =======================================================================
echo.
echo Tworzenie syntetycznych skanow testowych (Fool, Magician itd.)
echo w folderze scans_input...
echo.
python scripts/generate_test_scan.py
echo.
pause
goto MENU

:PROCESS_SUCCESS
echo.
echo =======================================================================
echo              PROCES ZAKONCZONY POWODZENIEM!
echo =======================================================================
echo Za chwile otworzy sie folder scans_output.
echo Zobaczysz tam wyciete karty oraz pliki debug_*.jpg z podgladem detekcji!
echo.
explorer scans_output
pause
goto MENU

:ERROR_OCCURRED
echo.
echo [BLAD] Wystapil problem podczas pracy asystenta!
echo Upewnij sie, ze zainstalowales biblioteki uruchamiajac install_dependencies.bat.
echo.
pause
goto MENU
