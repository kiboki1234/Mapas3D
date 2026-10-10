[CmdletBinding()]
param(
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $projectRoot "backend"
$frontend = Join-Path $projectRoot "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source

if (-not (Test-Path -LiteralPath $python)) {
    throw "No existe backend\.venv. Ejecute scripts\setup-windows.ps1 primero."
}
if (-not $npm) { throw "npm.cmd no está disponible." }

$logs = Join-Path $projectRoot "logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$backendOut = Join-Path $logs "backend.out.log"
$backendErr = Join-Path $logs "backend.err.log"
$frontendOut = Join-Path $logs "frontend.out.log"
$frontendErr = Join-Path $logs "frontend.err.log"

$backendArguments = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000")
if ($Reload) { $backendArguments += "--reload" }
$backendProcess = Start-Process -FilePath $python -ArgumentList $backendArguments -WorkingDirectory $backend -WindowStyle Hidden -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru
$frontendProcess = Start-Process -FilePath $npm -ArgumentList "run", "dev" -WorkingDirectory $frontend -WindowStyle Hidden -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru

$processFile = Join-Path $projectRoot ".city3d-processes.json"
@{
    backendPid = $backendProcess.Id
    frontendPid = $frontendProcess.Id
    startedAt = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content -LiteralPath $processFile -Encoding UTF8

$healthy = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2
        if ($health.status -eq "ok") { $healthy = $true; break }
    } catch { }
}

if (-not $healthy) {
    Write-Warning "El backend no respondió a tiempo. Revise logs\backend.err.log."
}

Write-Host "Backend: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "PID backend $($backendProcess.Id), PID frontend $($frontendProcess.Id)" -ForegroundColor DarkGray

