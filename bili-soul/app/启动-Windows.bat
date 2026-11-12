@echo off
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
  if errorlevel 1 exit /b 1
  call .venv\Scripts\activate
  python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
  if not exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    python -m playwright install chromium
    if errorlevel 1 exit /b 1
  )
) else (
  call .venv\Scripts\activate
)
if not exist .env copy .env.example .env
python main.py init
pause
