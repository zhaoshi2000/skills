@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Run setup first to install dependencies.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "gui.py"
