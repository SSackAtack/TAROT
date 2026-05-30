@echo off
title TarotVision - Instalator pakietow Pythona
chcp 65001 >nul

echo =======================================================================
echo              TarotVision - Instalator pakietow Pythona
echo =======================================================================
echo.
echo Ten skrypt sprawdzi obecnosc Pythona i automatycznie zainstaluje
echo wszystkie biblioteki potrzebne do obrobki skanow i dzialania CV.
echo.
echo =======================================================================
echo KROK 1: Weryfikacja obecnosci Pythona...
echo -----------------------------------------------------------------------

python --version >nul 2>&1
if errorlevel 1 goto NO_PYTHON

echo [SUKCES] Wykryto srodowisko Python:
python --version
echo.

echo =======================================================================
echo KROK 2: Aktualizacja menedzera pakietow (pip)...
echo -----------------------------------------------------------------------
python -m pip install --upgrade pip
echo.

echo =======================================================================
echo KROK 3: Instalacja wymaganych bibliotek z pliku requirements.txt...
echo Instalacja obejmuje: OpenCV, NumPy, websockets, Pillow
echo -----------------------------------------------------------------------
pip install -r requirements.txt
if errorlevel 1 goto INSTALL_ERROR
echo.

echo =======================================================================
echo              PODSUMOWANIE INSTALACJI
echo =======================================================================
echo [SUKCES] Wszystkie biblioteki zostaly poprawnie zainstalowane!
echo.
echo Mozesz teraz bez problemu uruchomic skrypt do obrobki skanow!
echo Przykladowe polecenie (automatyczne tlo, format WebP):
echo.
echo   python scripts/process_scans.py scans_input scans_output --background auto --format webp
echo.
echo Aby zakonczyc, nacisnij dowolny klawisz...
echo =======================================================================
pause >nul
exit /b

:NO_PYTHON
echo [BLAD] Python nie jest zainstalowany lub nie zostal dodany do PATH!
echo.
echo Aby rozwiazac ten problem:
echo 1. Pobierz i zainstaluj Python 3.10 lub nowszy z oficjalnej strony:
echo    https://www.python.org/downloads/
echo 2. Podczas instalacji KONIECZNIE zaznacz opcje:
echo    "Add Python.exe to PATH" (Dodaj Pythona do PATH).
echo 3. Po instalacji uruchom ten plik ponownie.
echo.
pause
exit /b

:INSTALL_ERROR
echo.
echo [BLAD] Wystapil problem podczas instalacji bibliotek!
echo Upewnij sie, ze masz polaczenie z Internetem i sprobuj ponownie.
echo.
pause
exit /b
