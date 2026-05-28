@echo off
chcp 65001 >nul
title TarotVision - Launcher
color 0A

echo ========================================
echo    TAROT VISION - Uruchamianie
echo ========================================
echo.

echo [1/4] Uruchamiam serwer AR (Vite)...
start "TarotVision AR" /D "%~dp0app_ar" cmd /k "npm run dev"

echo [2/4] Czekam 3 sekundy na start Vite...
timeout /t 3 /nobreak >nul

echo [3/4] Otwieram przegladarke...
start "" "http://localhost:5173/"

echo [4/4] Uruchamiam serwer CV (Python)...
start "TarotVision CV" /D "%~dp0app_cv" cmd /k "python main.py"

echo.
echo ========================================
echo    Wszystko uruchomione!
echo    AR:  http://localhost:5173/
echo    WS:  ws://localhost:8765/
echo    CV:  Okno kamery OpenCV
echo ========================================
echo.
echo Mozesz zamknac to okno.
echo.
pause
