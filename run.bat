@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_setup.bat
if errorlevel 1 (
 echo ERROR: Python environment setup failed.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m app.main
