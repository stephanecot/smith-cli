# Smith - dead-simple local dev launcher.
# Launches 3 things in separate windows:
#   1. podman/docker compose up -d   (Postgres + Redis, detached)
#   2. mvn spring-boot:run           (backend on :8080)
#   3. npm start                     (frontend on :4200)
#
# Usage:  scripts\dev-up.ps1
# Stop:   scripts\dev-down.ps1   (or just close the windows)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot

$engine = if (Get-Command docker -ErrorAction SilentlyContinue) { 'docker' }
          elseif (Get-Command podman -ErrorAction SilentlyContinue) { 'podman' }
          else { Write-Host "[smith] need docker or podman" -ForegroundColor Red; exit 1 }

Write-Host "[smith] 1/3 compose up -d ($engine)" -ForegroundColor Cyan
Push-Location (Join-Path $RepoRoot 'deploy\local')
try { & $engine compose up -d } finally { Pop-Location }

Write-Host "[smith] 2/3 backend (mvn install + spring-boot:run) in new window" -ForegroundColor Cyan
$backendCmd = 'mvn -pl smith-api -am -DskipTests install && cd smith-api && mvn spring-boot:run'
Start-Process -FilePath 'cmd.exe' `
              -ArgumentList '/k', $backendCmd `
              -WorkingDirectory (Join-Path $RepoRoot 'backend')

Write-Host "[smith] 3/3 frontend (npm start) in new window" -ForegroundColor Cyan
Start-Process -FilePath 'cmd.exe' `
              -ArgumentList '/k','npm','start' `
              -WorkingDirectory (Join-Path $RepoRoot 'frontend')

Write-Host ""
Write-Host "Backend  : http://localhost:8080" -ForegroundColor Green
Write-Host "Frontend : http://localhost:4200" -ForegroundColor Green
