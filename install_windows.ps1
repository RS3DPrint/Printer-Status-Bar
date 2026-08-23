$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $Admin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
    exit
}

& (Join-Path $Root 'run_setup.bat')
if ($LASTEXITCODE -ne 0) { throw 'Python environment setup failed.' }
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$ServiceScript = Join-Path $Root 'service.py'

$Existing = Get-Service -Name 'RS3DPrinterStatusBar' -ErrorAction SilentlyContinue
if ($Existing) {
    Stop-Service -Name 'RS3DPrinterStatusBar' -Force -ErrorAction SilentlyContinue
    & $Python $ServiceScript update --startup auto
} else {
    & $Python $ServiceScript --startup auto install
}
if ($LASTEXITCODE -ne 0) { throw 'Windows service installation failed.' }

& sc.exe failure RS3DPrinterStatusBar reset= 86400 actions= restart/5000/restart/15000/restart/30000 | Out-Null
& sc.exe failureflag RS3DPrinterStatusBar 1 | Out-Null
Start-Service -Name 'RS3DPrinterStatusBar'

$Shell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath('Desktop')
$Shortcut = $Shell.CreateShortcut((Join-Path $Desktop 'RS3D Printer Status Bar.lnk'))
$Shortcut.TargetPath = (Join-Path $Root 'run_desktop.bat')
$Shortcut.WorkingDirectory = $Root
$Shortcut.Description = 'RS3D Printer Status Bar'
$Shortcut.Save()

$StartupShortcut = Join-Path ([Environment]::GetFolderPath('Startup')) 'RS3D Printer Status Bar Tray.lnk'
Remove-Item -LiteralPath $StartupShortcut -Force -ErrorAction SilentlyContinue
$Port = & $Python -c "from app.main import configured_port; print(configured_port())"
Write-Host "Installed and started the RS3D Printer Status Bar Windows service."
Write-Host "Dashboard: http://localhost:$Port"
Read-Host 'Press Enter to close'

