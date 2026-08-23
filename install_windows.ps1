param([switch]$NoPause)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $Admin) {
    $ElevatedArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
    if ($NoPause) { $ElevatedArgs += '-NoPause' }
    Start-Process powershell.exe -Verb RunAs -ArgumentList $ElevatedArgs
    exit
}

# pywin32, which provides the Windows service support, requires a standard
# CPython build. The optional free-threaded (3.13t/3.14t) builds are not compatible.
function Find-StandardPython {
    foreach ($Version in @('3.13', '3.12', '3.11')) {
        try {
            $Candidate = & py "-$Version" -c "import sys,sysconfig; print(sys.executable if not sysconfig.get_config_var('Py_GIL_DISABLED') else '')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $Candidate -and (Test-Path -LiteralPath $Candidate.Trim())) {
                return $Candidate.Trim()
            }
        } catch { }
    }
    return $null
}

$StandardPython = Find-StandardPython
if (-not $StandardPython) {
    $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $Winget) {
        throw 'A standard 64-bit Python is required. Install Python 3.12 from python.org (not the free-threaded build), then run this installer again.'
    }
    Write-Host 'The installed Python is a free-threaded build and cannot run a Windows service.' -ForegroundColor Yellow
    Write-Host 'Installing standard 64-bit Python 3.12...'
    & winget.exe install --id Python.Python.3.12 --exact --scope machine --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw 'Standard Python 3.12 installation failed.' }
    $StandardPython = Find-StandardPython
    if (-not $StandardPython) { throw 'Python 3.12 was installed but could not be located. Restart Windows, then run this installer again.' }
}

$env:RS3D_PYTHON = $StandardPython
Write-Host "Using standard Python: $StandardPython"
& (Join-Path $Root 'run_setup.bat')
if ($LASTEXITCODE -ne 0) { throw 'Python environment setup failed.' }
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$ServiceScript = Join-Path $Root 'service.py'
& $Python -c "import servicemanager, win32serviceutil, pywintypes; print('Direct venv service runtime verified:', servicemanager.__file__)"
if ($LASTEXITCODE -ne 0) { throw 'The virtual-environment Windows service runtime could not be imported.' }

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
try {
    Start-Service -Name 'RS3DPrinterStatusBar' -ErrorAction Stop
    $Service = Get-Service -Name 'RS3DPrinterStatusBar'
    $Service.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Running,[TimeSpan]::FromSeconds(20))
} catch {
    $DiagnosticPath = Join-Path $env:ProgramData 'RS3D Printer Status Bar\service-startup-diagnostic.txt'
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DiagnosticPath) | Out-Null
    $Diagnostic = @("Startup error: $($_.Exception.Message)", '', 'Service configuration:', (& sc.exe qc RS3DPrinterStatusBar 2>&1), '', 'Recent RS3D/Python events:')
    try {
        $Events = Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=(Get-Date).AddMinutes(-10)} -ErrorAction Stop |
            Where-Object { $_.ProviderName -match 'Python|Service Control Manager' } |
            Select-Object -First 12 TimeCreated,ProviderName,Id,LevelDisplayName,@{N='Details';E={($_.Properties | ForEach-Object Value) -join ' | '}} | Format-List | Out-String
        $Diagnostic += $Events
    } catch { $Diagnostic += "Event log lookup failed: $($_.Exception.Message)" }
    $Diagnostic | Set-Content -LiteralPath $DiagnosticPath -Encoding UTF8
    throw "Windows service startup failed. Diagnostic saved to: $DiagnosticPath"
}

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
if (-not $NoPause) { Read-Host 'Press Enter to close' }
