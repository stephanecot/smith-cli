# Smith - local dev shutdown (Windows / PowerShell mirror of dev-down.sh).
#
# Stops the processes started by scripts\dev-up.ps1 and (optionally) the
# infrastructure containers.
#
# Container engine: prefers `docker compose`; falls back to `podman compose`
# or `podman-compose` if Docker is not installed.
#
# Usage:
#   scripts\dev-down.ps1                # stop backend + frontend, keep infra
#   scripts\dev-down.ps1 -All           # also stop compose (Postgres + Redis)
#   scripts\dev-down.ps1 -InfraOnly     # only stop compose
#   scripts\dev-down.ps1 -Backend       # stop backend only
#   scripts\dev-down.ps1 -Frontend      # stop frontend only

[CmdletBinding()]
param(
    [switch]$All,
    [switch]$InfraOnly,
    [switch]$Backend,
    [switch]$Frontend
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LogDir   = Join-Path $RepoRoot '.logs'

$StopBackend  = $true
$StopFrontend = $true
$StopInfra    = $false
if ($All)       { $StopInfra = $true }
if ($InfraOnly) { $StopInfra = $true; $StopBackend = $false; $StopFrontend = $false }
if ($Backend)   { $StopBackend = $true; $StopFrontend = $false }
if ($Frontend)  { $StopBackend = $false; $StopFrontend = $true }

function Say { param($Msg) Write-Host "[smith] $Msg" -ForegroundColor Cyan }

function Test-Cmd { param([string]$Name) [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

# Pick a compose front-end (only used if -All / -InfraOnly).
# Mirrors dev-up.ps1: prefer `docker compose`, then `podman compose` (with a
# space), then `podman-compose`.
function Resolve-Compose {
    if (Test-Cmd 'docker')         { return [pscustomobject]@{ Exe='docker';         Sub=@('compose') } }
    if (Test-Cmd 'podman')         { return [pscustomobject]@{ Exe='podman';         Sub=@('compose') } }
    if (Test-Cmd 'podman-compose') { return [pscustomobject]@{ Exe='podman-compose'; Sub=@() } }
    Write-Host "[smith] Neither Docker nor Podman is available; cannot stop infra." -ForegroundColor Red
    return $null
}

# Stop the cmd.exe wrapper PID and its whole tree (mvn / java / ng / node ...).
function Stop-PidTree {
    param([string]$Label, [string]$PidFile)
    if (-not (Test-Path $PidFile)) {
        Say "$Label not running (no pid file)"
        return
    }
    $procId = (Get-Content $PidFile -ErrorAction SilentlyContinue) -as [int]
    if (-not $procId -or -not (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
        Say "$Label already stopped"
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return
    }
    Say "Stopping $Label (PID $procId) ..."
    & taskkill /T /PID $procId 2>$null | Out-Null
    for ($i = 0; $i -lt 15; $i++) {
        if (-not (Get-Process -Id $procId -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Seconds 1
    }
    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
        Say "$Label did not stop cleanly - sending /F"
        & taskkill /F /T /PID $procId 2>$null | Out-Null
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

if ($StopBackend)  { Stop-PidTree -Label 'backend'  -PidFile (Join-Path $LogDir 'backend.pid') }
if ($StopFrontend) { Stop-PidTree -Label 'frontend' -PidFile (Join-Path $LogDir 'frontend.pid') }

if ($StopInfra) {
    $compose = Resolve-Compose
    if ($compose) {
        Say "Stopping compose (Postgres + Redis) via $($compose.Exe) $($compose.Sub -join ' ') down ..."
        Push-Location (Join-Path $RepoRoot 'deploy\local')
        try {
            & $compose.Exe @($compose.Sub + @('down'))
        } finally {
            Pop-Location
        }
    }
}

Say "Done."
