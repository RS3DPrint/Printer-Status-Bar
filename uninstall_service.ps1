$ErrorActionPreference = "Stop"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
    exit
}
$root = Split-Path -Parent $PSCommandPath
$python = Join-Path $root '.venv\Scripts\python.exe'
Stop-Service -Name 'RS3DPrinterStatusBar' -Force -ErrorAction SilentlyContinue
& $python (Join-Path $root 'service.py') remove
Write-Host 'RS3D Printer Status Bar service removed.'
Read-Host 'Press Enter to close'

