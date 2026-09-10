@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if not exist "backend\.demo-venv\Scripts\python.exe" goto :setup
if not exist "frontend\node_modules" goto :setup
goto :start

:setup
  call "%~dp0setup-demo.cmd" --no-pause
  if errorlevel 1 (
    pause
    exit /b 1
  )

:start

start "SkillHub Backend" /D "%~dp0backend" cmd /k ".demo-venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "SkillHub Frontend" /D "%~dp0frontend" cmd /k "npm run dev -- --host 127.0.0.1"
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173/"

echo SkillHub is opening in your browser.
echo Keep the Backend and Frontend windows open during the presentation.
echo Close those two windows after the presentation.
timeout /t 5 /nobreak >nul
