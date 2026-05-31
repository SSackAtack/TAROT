@echo off
chcp 65001 >nul
setlocal
title TarotVision - Launcher
color 0A
cd /d "%~dp0"

set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "TAROTVISION_LOG_DIR=%LOG_DIR%"
set "TAROTVISION_RESET_LOGS=1"
set "TAROTVISION_SNAPSHOT_FIRST=1"
set "LAUNCH_LOG=%LOG_DIR%\launcher.log"

echo ========================================
echo    TAROT VISION - WYBOR TALII
echo ========================================
echo.
echo Wybierz talie tarot, ktora chcesz zaladowac:
echo 1) Rider-Waite-Smith (domyslna)
echo 2) Zodiak
echo 3) Magic (Tarot of Mystical Moments)
echo 4) Gilded (The Gilded Tarot)
echo 5) Marchetti (Tarot Marchetti)
echo 6) Boski (Boski Tarot)
echo.
set /p DECK_CHOICE="Twoj wybor [1-6] (domyslnie 1): "

set "TAROTVISION_DECK=rider-waite-smith"
if "%DECK_CHOICE%"=="2" (
    set "TAROTVISION_DECK=zodiak"
)
if "%DECK_CHOICE%"=="3" (
    set "TAROTVISION_DECK=magic"
)
if "%DECK_CHOICE%"=="4" (
    set "TAROTVISION_DECK=gilded"
)
if "%DECK_CHOICE%"=="5" (
    set "TAROTVISION_DECK=marchetti"
)
if "%DECK_CHOICE%"=="6" (
    set "TAROTVISION_DECK=boski"
)

echo.
echo Wybrano talie: %TAROTVISION_DECK%
echo [%date% %time%] Wybrana talia: %TAROTVISION_DECK% >> "%LAUNCH_LOG%"
echo.
echo ========================================
echo    TAROT VISION - Uruchamianie
echo ========================================
echo.
echo [LOG] Logi beda zapisane w: %LOG_DIR%
echo [CV] Tryb snapshot-first: WLACZONY
echo.

echo [1/4] Uruchamiam serwer AR (Vite)...
start "TarotVision AR" /D "%~dp0app_ar" powershell -NoExit -ExecutionPolicy Bypass -Command "npm run dev 2>&1 | Tee-Object -FilePath '%LOG_DIR%\ar_vite.log'"

echo [2/4] Czekam 3 sekundy na start Vite...
timeout /t 3 /nobreak >nul

echo [3/4] Otwieram przegladarke...
start "" "http://localhost:5173/?operator=1"

echo [4/4] Uruchamiam serwer CV (Python)...
start "TarotVision CV" /D "%~dp0app_cv" cmd /k "set TAROTVISION_LOG_DIR=%LOG_DIR%&& set TAROTVISION_RESET_LOGS=1&& set TAROTVISION_SNAPSHOT_FIRST=1&& set TAROTVISION_DECK=%TAROTVISION_DECK%&& python main.py"

echo.
echo ========================================
echo    Wszystko uruchomione!
echo    AR:  http://localhost:5173/
echo    OP:  http://localhost:5173/?operator=1
echo    WS:  ws://localhost:8765/
echo    CV:  Okno kamery OpenCV
echo    MODE: snapshot-first
echo    LOG: %LOG_DIR%
echo ========================================
echo.
echo Mozesz zamknac to okno.
echo.
pause
