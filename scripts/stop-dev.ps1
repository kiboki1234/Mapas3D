[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$processFile = Join-Path $projectRoot ".city3d-processes.json"
if (-not (Test-Path -LiteralPath $processFile)) {
    Write-Host "No hay procesos registrados por City3D Engine."
    exit 0
}

$processes = Get-Content -Raw -LiteralPath $processFile | ConvertFrom-Json
foreach ($processId in @($processes.backendPid, $processes.frontendPid)) {
    if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $processId
    }
}
Remove-Item -LiteralPath $processFile
Write-Host "Procesos de desarrollo detenidos." -ForegroundColor Green

