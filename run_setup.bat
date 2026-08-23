@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=.venv"
set "VPY=%VENV%\Scripts\python.exe"
set "BASEPY=%RS3D_PYTHON%"
if not defined BASEPY (
  for /f "usebackq delims=" %%P in (`py -3.12 -c "import sys; print(sys.executable)" 2^>nul`) do set "BASEPY=%%P"
)
if not defined BASEPY (
  echo Standard Python 3.12 is required. The free-threaded Python build is not supported.
  exit /b 1
)
if exist "%VPY%" (
  "%VPY%" -c "import sysconfig; raise SystemExit(1 if sysconfig.get_config_var('Py_GIL_DISABLED') else 0)" >nul 2>&1
  if errorlevel 1 rmdir /s /q "%VENV%"
)
if not exist "%VPY%" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%BASEPY%" -m venv "%VENV%" || exit /b 1
)
"%VPY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  rmdir /s /q "%VENV%"
  "%BASEPY%" -m venv "%VENV%" || exit /b 1
)
"%VPY%" -m pip install --upgrade pip setuptools wheel >nul
"%VPY%" -m pip install -r requirements.txt
exit /b %errorlevel%
