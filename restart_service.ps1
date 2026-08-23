$ErrorActionPreference = "Stop"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
    exit
}
Restart-Service -Name 'RS3DPrinterStatusBar' -Force
$root = Split-Path -Parent $PSCommandPath
$python = Join-Path $root '.venv\Scripts\python.exe'
& $python -c "from app.main import configured_port; print('RS3D service restarted on http://localhost:' + str(configured_port()))"
Read-Host 'Press Enter to close'

