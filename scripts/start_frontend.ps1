# start_frontend.ps1 - Starts the HybridScan Next.js frontend (dev server).
#
# Usage:
#   .\scripts\start_frontend.ps1
#
# Requires the API to already be reachable at the URL configured in
# frontend/.env.local (NEXT_PUBLIC_HYBRIDSCAN_API_URL) - see
# scripts/start_backend.ps1. Frontend will be at http://localhost:3000.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"

if (-not (Test-Path (Join-Path $frontendDir ".env.local"))) {
    Write-Host "No frontend/.env.local found - copying from .env.example." -ForegroundColor Yellow
    Copy-Item (Join-Path $frontendDir ".env.example") (Join-Path $frontendDir ".env.local")
}

Set-Location $frontendDir
Write-Host "Starting HybridScan frontend (Next.js) from $frontendDir" -ForegroundColor Cyan
npm run dev -- -p 3000
