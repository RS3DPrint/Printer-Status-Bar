$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Shell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath('Desktop')
$Shortcut = $Shell.CreateShortcut((Join-Path $Desktop 'RS3D Printer Status Bar.lnk'))
$Shortcut.TargetPath = (Join-Path $Root 'run_desktop.bat')
$Shortcut.WorkingDirectory = $Root
$Shortcut.Description = 'RS3D Printer Status Bar'
$Shortcut.Save()

$Startup = [Environment]::GetFolderPath('Startup')
$Tray = $Shell.CreateShortcut((Join-Path $Startup 'RS3D Printer Status Bar Tray.lnk'))
$Tray.TargetPath = (Join-Path $Root 'run_tray.bat')
$Tray.WorkingDirectory = $Root
$Tray.Description = 'Start RS3D Printer Status Bar with Windows'
$Tray.Save()
Write-Host "Installed desktop shortcut and Windows startup tray shortcut."
