#!/usr/bin/env pwsh
# Builds and starts every container (Postgres + 3 backends + frontend).
# Usage:  ./start.ps1          start everything (build if needed)
#         ./start.ps1 -Down    stop and remove everything
#         ./start.ps1 -Logs    follow logs after starting

param(
    [switch]$Down,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Make sure the Docker engine is reachable before we do anything.
try {
    docker info | Out-Null
} catch {
    Write-Host "Docker engine is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

if ($Down) {
    Write-Host "Stopping and removing all containers..." -ForegroundColor Yellow
    docker compose down
    exit $LASTEXITCODE
}

Write-Host "Building and starting all services..." -ForegroundColor Cyan
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
docker compose ps
Write-Host ""
Write-Host "Services are up:" -ForegroundColor Green
Write-Host "  Frontend   ->  http://localhost:13000"
Write-Host "  Customer   ->  http://localhost:18001/docs"
Write-Host "  Worker     ->  http://localhost:18002/docs"
Write-Host "  Partner    ->  http://localhost:18003/docs"
Write-Host "  Postgres   ->  localhost:55432  (user/password/mydb)"
Write-Host ""
Write-Host "Stop everything with:  ./start.ps1 -Down" -ForegroundColor DarkGray

if ($Logs) {
    docker compose logs -f
}
