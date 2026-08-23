@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_setup.bat
if errorlevel 1 exit /b %errorlevel%
".venv\Scripts\python.exe" -m app.tray
