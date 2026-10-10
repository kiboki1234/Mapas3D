[CmdletBinding()]
param(
    [switch]$WithoutOverture
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot "check-dependencies.ps1")

$backend = Join-Path $projectRoot "backend"
$frontend = Join-Path $projectRoot "frontend"
$venvPython = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Push-Location $backend
    try { python -m venv .venv } finally { Pop-Location }
}

$extra = if ($WithoutOverture) { ".[test]" } else { ".[test,overture]" }
Push-Location $backend
try { & $venvPython -m pip install -e $extra } finally { Pop-Location }

Push-Location $frontend
try { npm install } finally { Pop-Location }

$envPath = Join-Path $projectRoot ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath (Join-Path $projectRoot ".env.example") -Destination $envPath
    Write-Host "Se creó .env desde .env.example." -ForegroundColor Cyan
}

Write-Host "City3D Engine quedó preparado. Ejecute scripts\start-dev.ps1" -ForegroundColor Green

