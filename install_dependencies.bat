@echo off
title TarotVision - Instalator Bibliotek Pythona
chcp 65001 >nul

echo =======================================================================
echo              TarotVision - Instalator Bibliotek Pythona
echo =======================================================================
echo.
echo Ten skrypt sprawdzi obecność Pythona i automatycznie zainstaluje
echo wszystkie biblioteki potrzebne do obróbki skanów i działania CV.
echo.
echo =======================================================================
echo KROK 1: Weryfikacja obecności Pythona...
echo -----------------------------------------------------------------------

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [BŁĄD] Python nie jest zainstalowany lub nie został dodany do zmiennej PATH!
    echo.
    echo Aby rozwiązać ten problem:
    echo 1. Pobierz i zainstaluj Python 3.10 lub nowszy z oficjalnej strony:
    echo    https://www.python.org/downloads/
    echo 2. Podczas instalacji KONIECZNIE zaznacz opcję:
    echo    "Add Python.exe to PATH" (Dodaj Pythona do zmiennej PATH).
    echo 3. Po instalacji uruchom ten plik (.bat) ponownie.
    echo.
    pause
    exit /b
)

echo [SUKCES] Wykryto środowisko Python:
python --version
echo.

echo =======================================================================
echo KROK 2: Aktualizacja menedżera pakietów (pip)...
echo -----------------------------------------------------------------------
python -m pip install --upgrade pip
echo.

echo =======================================================================
echo KROK 3: Instalacja wymaganych bibliotek z pliku requirements.txt...
echo (Instalacja obejmuje: OpenCV, NumPy, websockets, Pillow)
echo -----------------------------------------------------------------------
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [BŁĄD] Wystąpił problem podczas instalacji bibliotek!
    echo Upewnij się, że masz połączenie z Internetem i spróbuj ponownie.
    echo.
    pause
    exit /b
)
echo.

echo =======================================================================
echo              PODSUMOWANIE INSTALACJI
echo =======================================================================
echo [SUKCES] Wszystkie biblioteki zostały poprawnie zainstalowane!
echo.
echo Możesz teraz bez problemu uruchomić skrypt do obróbki skanów!
echo Przykładowe polecenie (automatyczne tło, format WebP):
echo.
echo   python scripts/process_scans.py scans_input scans_output --background auto --format webp
echo.
echo Aby zakończyć, naciśnij dowolny klawisz...
echo =======================================================================
pause >nul
