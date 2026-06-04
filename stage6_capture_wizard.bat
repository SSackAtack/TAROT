@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title TarotVision Stage 6 - Capture Wizard
color 0E
cd /d "%~dp0"

set "PYTHONPATH=C:\tmp\tarot_pydeps_stage6;C:\tmp\tarot_pydeps;%~dp0app_cv;%~dp0"
set "WIZARD=tools\cv_detection_lab\stage6_real_camera_capture_wizard.py"

if /I "%~1"=="plan" goto PRINT_PLAN
if /I "%~1"=="run" goto RUN_WIZARD

echo ============================================================
echo    TAROTVISION - Stage 6 Real-Camera Capture Wizard
echo ============================================================
echo.
echo This launcher starts the camera snapshot wizard.
echo Default mode: backend and Studio can be OFF. Enter takes one camera photo.
echo The wizard does not change runtime.
echo.
echo Choose action:
echo ------------------------------------------------------------
echo [1] Print 28-step plan
echo [2] Run camera snapshot wizard
echo [3] Exit
echo ------------------------------------------------------------
echo.
set /p CHOICE="Choice [1-3] [default 2]: "
if "!CHOICE!"=="" set "CHOICE=2"

if "!CHOICE!"=="1" goto PRINT_PLAN
if "!CHOICE!"=="2" goto RUN_WIZARD
if "!CHOICE!"=="3" goto EXIT_OK
goto RUN_WIZARD

:PRINT_PLAN
echo.
python "%WIZARD%" --print-plan
echo.
pause
exit /b %ERRORLEVEL%

:RUN_WIZARD
echo.
python "%WIZARD%"
echo.
pause
exit /b %ERRORLEVEL%

:EXIT_OK
echo.
echo [INFO] Closing launcher.
pause
exit /b 0
