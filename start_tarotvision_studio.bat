@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title TarotVision Studio - Launcher
color 0E
cd /d "%~dp0"

set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "TAROTVISION_LOG_DIR=%LOG_DIR%"
set "TAROTVISION_RESET_LOGS=1"
set "TAROTVISION_SNAPSHOT_FIRST=1"
set "TAROTVISION_DECK=rider-waite-smith"
set "LAUNCH_LOG=%LOG_DIR%\launcher_studio.log"

echo ========================================
echo    TAROTVISION STUDIO - Uruchamianie
echo ========================================
echo.
echo [LOG] Logi będą zapisane w: %LOG_DIR%
echo [CV] Tryb snapshot-first: WŁĄCZONY
echo [DECK] Aktywne talie wybierasz w Studio. Fallback backendu: %TAROTVISION_DECK%
echo [%date% %time%] Studio launcher start; deck fallback: %TAROTVISION_DECK% >> "%LAUNCH_LOG%"
echo.

echo ============================================================
echo [0/4] Weryfikacja dostępności portu 5173...
echo ============================================================
powershell -Command "$conn = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue; if ($conn) { exit 1 } else { exit 0 }"
if errorlevel 1 goto PORT_BUSY

echo [OK] Port 5173 jest wolny. Kontynuuję...
echo.
goto START_SERVERS

:PORT_BUSY
color 0C
echo.
echo ⚠️  [OSTRZEŻENIE] Port 5173 jest obecnie ZAJĘTY!
echo Prawdopodobnie inna sesja deweloperska (Vite / Node) działa w tle.
echo.
echo Konsekwencje kontynuacji:
echo Nowa sesja Vite wystartuje na porcie 5174, a przeglądarka spróbuje
echo otworzyć port 5173. Spowoduje to brak połączenia z nowym systemem!
echo.
echo Wybierz akcję:
echo ------------------------------------------------------------
echo [1] [Zalecane] Automatycznie zatrzymaj wiszące procesy na porcie 5173 i kontynuuj
echo [2] Kontynuuj uruchamianie mimo to [na własną odpowiedzialność]
echo [3] Przerwij i wyjdź z launchera
echo ------------------------------------------------------------
echo.
set /p PORT_CHOICE="Twój wybór [1-3] [domyślnie 3]: "
if "!PORT_CHOICE!"=="" set "PORT_CHOICE=3"

if "!PORT_CHOICE!"=="1" goto KILL_PORT_PROCESS
if "!PORT_CHOICE!"=="2" goto START_SERVERS
if "!PORT_CHOICE!"=="3" goto ABORT_LAUNCH

goto ABORT_LAUNCH

:KILL_PORT_PROCESS
echo.
echo [INFO] Zamykam wiszące procesy na porcie 5173...
powershell -Command "$proc = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($p in $proc) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; Write-Host 'Zatrzymano proces o ID' $p }"
echo [INFO] Odczekanie 2 sekund na zwolnienie portu...
timeout /t 2 /nobreak >nul
color 0E
goto START_SERVERS

:ABORT_LAUNCH
echo.
echo [INFO] Uruchamianie przerwane przez operatora.
color 0E
pause
exit /b 0

:START_SERVERS
color 0E
echo.

echo [1/4] Uruchamiam serwer AR (Vite)...
start "TarotVision AR" /D "%~dp0app_ar" powershell -NoExit -ExecutionPolicy Bypass -Command "npm run dev 2>&1 | Tee-Object -FilePath '%LOG_DIR%\ar_vite_studio.log'"

echo [2/4] Czekam 3 sekundy na start Vite...
timeout /t 3 /nobreak >nul

echo [3/4] Otwieram przeglądarkę w trybie Studio...
start "" "http://localhost:5173/?studio=1"

echo [4/4] Uruchamiam serwer CV (Python)...
start "TarotVision CV" /D "%~dp0app_cv" cmd /k "set TAROTVISION_LOG_DIR=%LOG_DIR%&& set TAROTVISION_RESET_LOGS=1&& set TAROTVISION_SNAPSHOT_FIRST=1&& set TAROTVISION_DECK=%TAROTVISION_DECK%&& set TAROTVISION_DISABLE_OPENCV_PREVIEW=1&& python main.py"

echo.
echo ========================================
echo    TarotVision Studio Uruchomione!
echo    AR:     http://localhost:5173/
echo    STUDIO: http://localhost:5173/?studio=1
echo    WS:     ws://localhost:8765/
echo    PREVIEW: http://localhost:8766/video_feed.mjpg
echo    MODE:   snapshot-first
echo    LOG:    %LOG_DIR%
echo ========================================
echo.
echo Możesz zamknąć to okno.
echo.
pause
