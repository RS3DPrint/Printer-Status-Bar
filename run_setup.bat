@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=.venv"
set "VPY=%VENV%\Scripts\python.exe"
if not exist "%VPY%" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  py -3 -m venv "%VENV%" || exit /b 1
)
"%VPY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  rmdir /s /q "%VENV%"
  py -3 -m venv "%VENV%" || exit /b 1
)
"%VPY%" -m pip install --upgrade pip setuptools wheel >nul
"%VPY%" -m pip install -r requirements.txt
exit /b %errorlevel%
