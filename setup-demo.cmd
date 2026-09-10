@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "SKILLHUB_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%SKILLHUB_PYTHON%" set "SKILLHUB_PYTHON=python"

"%SKILLHUB_PYTHON%" -c "import sys; raise SystemExit(0 if sys.platform == 'win32' else 1)"
if errorlevel 1 (
  echo A Windows Python 3.11 or newer is required.
  echo Install Python from python.org, then run this file again.
  if /I not "%~1"=="--no-pause" pause
  exit /b 1
)

if not exist "backend\.demo-venv\Scripts\python.exe" (
  echo Preparing the backend environment...
  "%SKILLHUB_PYTHON%" -m venv "backend\.demo-venv"
  if errorlevel 1 goto :failed
)

"backend\.demo-venv\Scripts\python.exe" -m pip install -e "backend[dev]"
if errorlevel 1 goto :failed

if not exist "frontend\node_modules" (
  pushd frontend
  call npm install
  if errorlevel 1 goto :failed_popd
  popd
)

pushd backend
".demo-venv\Scripts\python.exe" -m app.seed
if errorlevel 1 goto :failed_popd
popd

echo SkillHub demo setup is ready.
if /I not "%~1"=="--no-pause" pause
exit /b 0

:failed_popd
popd
:failed
echo Setup failed. Keep this window open and check the message above.
if /I not "%~1"=="--no-pause" pause
exit /b 1
