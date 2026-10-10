[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Ejecute scripts\setup-windows.ps1 antes de las pruebas."
}

Push-Location (Join-Path $projectRoot "backend")
try { & $python -m pytest --cov=app --cov-report=term-missing } finally { Pop-Location }

Push-Location (Join-Path $projectRoot "frontend")
try { npm run build } finally { Pop-Location }

Write-Host "Pruebas y build completados." -ForegroundColor Green

