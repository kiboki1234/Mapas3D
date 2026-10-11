[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"
$testRunRoot = Join-Path $projectRoot "backend\.test-runs"
$testTemp = Join-Path $testRunRoot ([guid]::NewGuid().ToString("N"))
$testCache = Join-Path $projectRoot "backend\.test-cache"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Ejecute scripts\setup-windows.ps1 antes de las pruebas."
}

New-Item -ItemType Directory -Path $testRunRoot -Force | Out-Null
New-Item -ItemType Directory -Path $testCache -Force | Out-Null

Push-Location (Join-Path $projectRoot "backend")
try {
    & $python -m pytest --cov=app --cov-report=term-missing --basetemp $testTemp -o "cache_dir=$testCache"
    if ($LASTEXITCODE -ne 0) {
        throw "Las pruebas del backend fallaron con código $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

Push-Location (Join-Path $projectRoot "frontend")
try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "El build del frontend falló con código $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

Write-Host "Pruebas y build completados." -ForegroundColor Green

