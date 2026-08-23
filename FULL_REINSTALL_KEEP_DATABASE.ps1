param()
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSCommandPath
$Admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $Admin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"")
    exit
}

$Database = Join-Path $Root 'rs3d_status.db'
$DataRoot = Join-Path $env:ProgramData 'RS3D Printer Status Bar'
$BackupRoot = Join-Path $DataRoot 'database-backups'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = Join-Path $BackupRoot "rs3d_status-$Stamp.db"

Write-Host 'RS3D Printer Status Bar - complete clean reinstall' -ForegroundColor Cyan
if (Test-Path -LiteralPath $Database) {
    New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
    Copy-Item -LiteralPath $Database -Destination $Backup -Force
    if ((Get-FileHash -LiteralPath $Database).Hash -ne (Get-FileHash -LiteralPath $Backup).Hash) {
        throw 'Database backup verification failed. Nothing was removed.'
    }
    Write-Host "Database preserved and verified: $Backup" -ForegroundColor Green
} else {
    Write-Host 'No existing database was found; a new empty database will be created.' -ForegroundColor Yellow
}

Stop-Service -Name 'RS3DPrinterStatusBar' -Force -ErrorAction SilentlyContinue
$OldPython = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $OldPython) {
    & $OldPython (Join-Path $Root 'service.py') remove 2>$null
}
if (Get-Service -Name 'RS3DPrinterStatusBar' -ErrorAction SilentlyContinue) {
    & sc.exe delete RS3DPrinterStatusBar | Out-Null
}
for ($Attempt = 0; $Attempt -lt 40; $Attempt++) {
    if (-not (Get-Service -Name 'RS3DPrinterStatusBar' -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 250
}
if (Get-Service -Name 'RS3DPrinterStatusBar' -ErrorAction SilentlyContinue) {
    throw 'Windows is still removing the old service. Restart Windows, then run this reinstall again; the database backup is safe.'
}

# Remove only known generated runtime folders inside this application directory.
foreach ($Generated in @('.venv','logs','__pycache__','app\__pycache__','app\connectors\__pycache__')) {
    $Target = Join-Path $Root $Generated
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Recurse -Force }
}
if (-not (Test-Path -LiteralPath $Database) -and (Test-Path -LiteralPath $Backup)) {
    Copy-Item -LiteralPath $Backup -Destination $Database -Force
}

& (Join-Path $Root 'install_windows.ps1') -NoPause
if ($LASTEXITCODE -ne 0) { throw 'Clean reinstall failed.' }

$Service = Get-Service -Name 'RS3DPrinterStatusBar' -ErrorAction Stop
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Counts = & $Python -c "import sqlite3; c=sqlite3.connect(r'$Database'); print('Printers:',c.execute('select count(*) from printers').fetchone()[0], '| Light bars:',c.execute('select count(*) from bars').fetchone()[0], '| Settings:',c.execute('select count(*) from settings').fetchone()[0])"
$Port = & $Python -c "from app.main import configured_port; print(configured_port())"
Write-Host ''
Write-Host 'Complete reinstall succeeded.' -ForegroundColor Green
Write-Host "Service status: $($Service.Status)"
Write-Host "Preserved database: $Counts"
Write-Host "Dashboard: http://localhost:$Port"
Write-Host "Safety backup: $Backup"
Read-Host 'Press Enter to close'
