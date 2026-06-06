@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title TarotVision Studio - State-First Diff Smoke
color 0B
cd /d "%~dp0"

set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "TAROTVISION_LOG_DIR=%LOG_DIR%"
set "TAROTVISION_RESET_LOGS=1"
set "TAROTVISION_SNAPSHOT_FIRST=1"
set "TAROTVISION_PIPELINE=state_first_diff"
set "TAROTVISION_DECK=gilded"
set "LAUNCH_LOG=%LOG_DIR%\launcher_studio_state_first_diff.log"

echo ========================================
echo    TAROTVISION STUDIO - STATE-FIRST DIFF
echo ========================================
echo.
echo [LOG] Logi beda zapisane w: %LOG_DIR%
echo [CV] Pipeline: %TAROTVISION_PIPELINE%
echo [DECK] Fallback backendu: %TAROTVISION_DECK%
echo [SMOKE] Uzyj w Studio sekcji: Sesja state-first
echo [%date% %time%] State-first diff launcher start; deck fallback: %TAROTVISION_DECK% >> "%LAUNCH_LOG%"
echo.

echo ============================================================
echo [0/4] Weryfikacja dostepnosci portow 5173, 8765 i 8766...
echo ============================================================
powershell -Command "$conn = Get-NetTCPConnection -LocalPort 5173,8765,8766 -ErrorAction SilentlyContinue; if ($conn) { exit 1 } else { exit 0 }"
if errorlevel 1 goto PORT_BUSY

echo [OK] Porty 5173, 8765 i 8766 sa wolne. Kontynuuje...
echo.
goto START_SERVERS

:PORT_BUSY
color 0C
echo.
echo [OSTRZEZENIE] Port 5173, 8765 albo 8766 jest obecnie zajety.
echo Prawdopodobnie inna sesja Studio/CV/Vite dziala w tle.
echo.
echo Wybierz akcje:
echo ------------------------------------------------------------
echo [1] [Zalecane] Automatycznie zatrzymaj procesy na portach 5173, 8765 i 8766 i kontynuuj
echo [2] Kontynuuj mimo to
echo [3] Przerwij i wyjdz z launchera
echo ------------------------------------------------------------
echo.
set /p PORT_CHOICE="Twoj wybor [1-3] [domyslnie 3]: "
if "!PORT_CHOICE!"=="" set "PORT_CHOICE=3"

if "!PORT_CHOICE!"=="1" goto KILL_PORT_PROCESS
if "!PORT_CHOICE!"=="2" goto START_SERVERS
if "!PORT_CHOICE!"=="3" goto ABORT_LAUNCH

goto ABORT_LAUNCH

:KILL_PORT_PROCESS
echo.
echo [INFO] Zamykam procesy na portach 5173, 8765 i 8766...
powershell -Command "$proc = Get-NetTCPConnection -LocalPort 5173,8765,8766 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($p in $proc) { if ($p -ne 0) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; Write-Host 'Zatrzymano proces o ID' $p } }"
echo [INFO] Czekam 2 sekundy na zwolnienie portow...
timeout /t 2 /nobreak >nul
color 0B
goto START_SERVERS

:ABORT_LAUNCH
echo.
echo [INFO] Uruchamianie przerwane przez operatora.
color 0B
pause
exit /b 0

:START_SERVERS
color 0B
echo.

echo [1/4] Uruchamiam serwer AR (Vite)...
start "TarotVision AR" /D "%~dp0app_ar" powershell -NoExit -ExecutionPolicy Bypass -Command "npm run dev 2>&1 | Tee-Object -FilePath '%LOG_DIR%\ar_vite_studio_state_first_diff.log'"

echo [2/4] Czekam 3 sekundy na start Vite...
timeout /t 3 /nobreak >nul

echo [3/4] Otwieram przegladarke w trybie Studio...
start "" "http://localhost:5173/?studio=1"

echo [4/4] Uruchamiam serwer CV (Python) w trybie state-first diff...
start "TarotVision CV - StateFirstDiff" /D "%~dp0app_cv" cmd /k "set TAROTVISION_LOG_DIR=%LOG_DIR%&& set TAROTVISION_RESET_LOGS=1&& set TAROTVISION_SNAPSHOT_FIRST=1&& set TAROTVISION_PIPELINE=%TAROTVISION_PIPELINE%&& set TAROTVISION_DECK=%TAROTVISION_DECK%&& set TAROTVISION_DISABLE_OPENCV_PREVIEW=1&& python main.py"

echo.
echo ========================================
echo    TarotVision Studio State-First uruchomione
echo    STUDIO:   http://localhost:5173/?studio=1
echo    WS:       ws://localhost:8765/
echo    PREVIEW:  http://localhost:8766/video_feed.mjpg
echo    PIPELINE: %TAROTVISION_PIPELINE%
echo    DECK:     %TAROTVISION_DECK%
echo    LOG:      %LOG_DIR%
echo ========================================
echo.
echo Smoke:
echo 1. Sesja state-first - Start
echo 2. Pusta mata - Capture Empty
echo 3. Sprawdz active=true i empty_reference_locked=true
echo 4. Testuj EMPTY, ONE_CARD, THREE_CARDS
echo.
echo Mozesz zamknac to okno.
echo.
pause
