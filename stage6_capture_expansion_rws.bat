@echo off
chcp 65001 >nul
setlocal
title TarotVision Stage 6 - Minimal RWS Expansion
cd /d "%~dp0"

set "PYTHONPATH=C:\tmp\tarot_pydeps_stage6;C:\tmp\tarot_pydeps;%~dp0app_cv;%~dp0"
set "WIZARD=tools\cv_detection_lab\stage6_real_camera_fixture_expansion_wizard.py"

if /I "%~1"=="plan" (
  python "%WIZARD%" --print-plan
) else (
  python "%WIZARD%"
)

echo.
pause
