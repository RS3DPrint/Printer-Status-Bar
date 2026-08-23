@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV=.venv"
set "VPY=%VENV%\Scripts\python.exe"

echo ============================================================
echo  RS3D Printer Status Bar - Windows Launcher
echo ============================================================

rem Create the virtual environment if it does not exist.
if not exist "%VPY%" (
  echo [1/4] Creating Python virtual environment...
  if exist "%VENV%" rmdir /s /q "%VENV%"
  py -3 -m venv "%VENV%"
  if errorlevel 1 goto :venv_error
)

rem Verify pip inside the venv. If it is damaged, rebuild the venv.
"%VPY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo [1/4] Existing virtual environment is damaged. Rebuilding it...
  rmdir /s /q "%VENV%"
  py -3 -m venv "%VENV%"
  if errorlevel 1 goto :venv_error
)

echo [2/4] Updating pip in the virtual environment...
"%VPY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :pip_error

echo [3/4] Installing application requirements...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto :pip_error

rem Sanity check that required modules are actually importable from the venv.
"%VPY%" -c "import flask, requests, paho.mqtt.client, waitress" >nul 2>&1
if errorlevel 1 (
  echo Required Python modules are still missing. Rebuilding the environment once...
  rmdir /s /q "%VENV%"
  py -3 -m venv "%VENV%"
  if errorlevel 1 goto :venv_error
  "%VPY%" -m pip install --upgrade pip setuptools wheel
  if errorlevel 1 goto :pip_error
  "%VPY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :pip_error
)

echo [4/4] Starting RS3D Printer Status Bar...
"%VPY%" -m app.main
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo Application exited with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%

:venv_error
echo.
echo ERROR: Could not create the Python virtual environment.
echo Make sure Python 3 is installed and the Windows "py" launcher is available.
pause
exit /b 1

:pip_error
echo.
echo ERROR: Could not install the required Python packages into .venv.
pause
exit /b 1
