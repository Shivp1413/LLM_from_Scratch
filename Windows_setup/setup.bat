@echo off
setlocal
cd /d "%~dp0.."
echo ============================================================
echo    LLM Studio - Windows one-time setup
echo ============================================================
for /f "tokens=2 delims=[]" %%V in ('ver') do set "WINVER=%%V"
echo Detected Windows version: %WINVER%
if not exist "Windows_setup\setup.ps1" (
  echo ERROR: Could not find Windows_setup\setup.ps1
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Read the message above, then retry setup.bat.
  pause
  exit /b 1
)
echo.
echo Setup complete. Double-click Windows_setup\run.bat to open the dashboard.
pause
