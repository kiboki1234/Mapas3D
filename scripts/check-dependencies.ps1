[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

function Read-ToolVersion {
    param([string]$Name, [string[]]$Arguments = @("--version"))
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        return [PSCustomObject]@{ Tool = $Name; Available = $false; Version = "No encontrado"; Required = $true }
    }
    try {
        $output = & $command.Source @Arguments 2>&1 | Select-Object -First 1
    } catch {
        $output = $_.Exception.Message
    }
    return [PSCustomObject]@{ Tool = $Name; Available = $true; Version = "$output"; Required = $true }
}

$results = @(
    Read-ToolVersion "node"
    Read-ToolVersion "npm"
    Read-ToolVersion "python"
    Read-ToolVersion "git"
    Read-ToolVersion "java" @("-version")
)

$osmHome = $env:CITY3D_OSM2WORLD_HOME
$osmAvailable = $false
$osmDetail = "Opcional; configure CITY3D_OSM2WORLD_HOME"
if ($osmHome -and (Test-Path -LiteralPath $osmHome)) {
    $osmAvailable = $true
    $osmDetail = (Resolve-Path -LiteralPath $osmHome).Path
}
$results += [PSCustomObject]@{ Tool = "OSM2World"; Available = $osmAvailable; Version = $osmDetail; Required = $false }

$results | Format-Table -AutoSize

$requiredMissing = $results | Where-Object { $_.Required -and -not $_.Available }
if ($requiredMissing) {
    throw "Faltan dependencias obligatorias. Revise la tabla anterior."
}

Write-Host "Dependencias base verificadas para $projectRoot" -ForegroundColor Green

