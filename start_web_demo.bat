@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_web_demo.ps1"
if errorlevel 1 (
  echo.
  echo Failed to start the web demo. Review the message above.
  pause
)
endlocal