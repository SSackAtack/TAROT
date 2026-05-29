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
set "LAUNCH_LOG=%LOG_DIR%\launcher.log"

echo ========================================
echo    TAROT VISION - Uruchamianie
echo ========================================
echo.
echo [%date% %time%] Start TarotVision >> "%LAUNCH_LOG%"
echo [LOG] Logi beda zapisane w: %LOG_DIR%
echo.

echo [1/4] Uruchamiam serwer AR (Vite)...
start "TarotVision AR" /D "%~dp0app_ar" powershell -NoExit -ExecutionPolicy Bypass -Command "npm run dev 2>&1 | Tee-Object -FilePath '%LOG_DIR%\ar_vite.log'"

echo [2/4] Czekam 3 sekundy na start Vite...
timeout /t 3 /nobreak >nul

echo [3/4] Otwieram przegladarke...
start "" "http://localhost:5173/"

echo [4/4] Uruchamiam serwer CV (Python)...
start "TarotVision CV" /D "%~dp0app_cv" cmd /k "set TAROTVISION_LOG_DIR=%LOG_DIR%&& set TAROTVISION_RESET_LOGS=1&& python main.py"

echo.
echo ========================================
echo    Wszystko uruchomione!
echo    AR:  http://localhost:5173/
echo    WS:  ws://localhost:8765/
echo    CV:  Okno kamery OpenCV
echo    LOG: %LOG_DIR%
echo ========================================
echo.
echo Mozesz zamknac to okno.
echo.
pause
