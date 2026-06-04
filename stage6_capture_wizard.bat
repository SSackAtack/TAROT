@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title TarotVision Stage 6 - Minimal RWS Expansion
color 0E
cd /d "%~dp0"

set "PYTHONPATH=C:\tmp\tarot_pydeps_stage6;C:\tmp\tarot_pydeps;%~dp0app_cv;%~dp0"
set "EXPANSION_WIZARD=tools\cv_detection_lab\stage6_real_camera_fixture_expansion_wizard.py"
set "LEGACY_WIZARD=tools\cv_detection_lab\stage6_real_camera_capture_wizard.py"

if /I "%~1"=="plan" goto PRINT_EXPANSION_PLAN
if /I "%~1"=="legacy-plan" goto PRINT_LEGACY_PLAN

set "CAMERA_OWNER_PID="
for /f %%P in ('powershell -NoProfile -Command "$p = @(Get-CimInstance Win32_Process).Where({ $_.Name -eq 'python.exe' -and $_.CommandLine -match 'main\.py' }); if ($p.Count -gt 0) { $p[0].ProcessId }"') do set "CAMERA_OWNER_PID=%%P"
if defined CAMERA_OWNER_PID (
  echo ============================================================
  echo [BLOKADA] Kamera jest zajeta przez backend TarotVision.
  echo Proces: python main.py, PID !CAMERA_OWNER_PID!
  echo Zamknij backend przed uruchomieniem wizarda.
  echo ============================================================
  pause
  exit /b 2
)

if /I "%~1"=="rws" goto RUN_EXPANSION
if /I "%~1"=="legacy" goto RUN_LEGACY

echo ============================================================
echo    TAROTVISION - Minimal RWS Expansion - 8 samples
echo ============================================================
echo.
echo Default action captures the NEW isolated RWS expansion pack.
echo It does NOT run the completed legacy 28-sample Gilded plan.
echo Backend and Studio can be OFF. The wizard does not change runtime.
echo.
echo Choose action:
echo ------------------------------------------------------------
echo [1] Run Minimal RWS Expansion - 8 samples [default]
echo [2] Print the new 8-sample RWS plan
echo [3] Legacy 28-sample Gilded wizard [explicit only]
echo [4] Exit
echo ------------------------------------------------------------
echo.
set /p CHOICE="Choice [1-4] [default 1]: "
if "!CHOICE!"=="" set "CHOICE=1"

if "!CHOICE!"=="1" goto RUN_EXPANSION
if "!CHOICE!"=="2" goto PRINT_EXPANSION_PLAN
if "!CHOICE!"=="3" goto CONFIRM_LEGACY
if "!CHOICE!"=="4" goto EXIT_OK
goto RUN_EXPANSION

:PRINT_EXPANSION_PLAN
echo.
python "%EXPANSION_WIZARD%" --print-plan
echo.
pause
exit /b %ERRORLEVEL%

:RUN_EXPANSION
echo.
python "%EXPANSION_WIZARD%"
echo.
pause
exit /b %ERRORLEVEL%

:CONFIRM_LEGACY
echo.
echo WARNING: the legacy 28-sample Gilded fixture is already complete.
set /p LEGACY_CONFIRM="Type LEGACY to run it anyway: "
if /I not "!LEGACY_CONFIRM!"=="LEGACY" goto EXIT_OK
goto RUN_LEGACY

:PRINT_LEGACY_PLAN
echo.
python "%LEGACY_WIZARD%" --print-plan
echo.
pause
exit /b %ERRORLEVEL%

:RUN_LEGACY
echo.
python "%LEGACY_WIZARD%"
echo.
pause
exit /b %ERRORLEVEL%

:EXIT_OK
echo.
echo [INFO] Closing launcher.
pause
exit /b 0
