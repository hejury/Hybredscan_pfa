# start_hybridscan.ps1 - Convenience launcher for the HybridScan WEB
# workflow: opens the FastAPI backend and the Next.js frontend in two
# separate windows. Does NOT start Streamlit (fallback only, launch it
# yourself with `streamlit run app.py` if needed) and does NOT start the
# folder watcher (Protection) - activate that from the /protection page.
#
# For the DESKTOP application (a single native window, no browser tab to
# open manually), use `python run_desktop.py` at the repo root instead -
# see README.md, section "Application Desktop HybridScan". This script
# remains for developers who want the API and the frontend in their own
# terminal windows.
#
# Usage:
#   .\scripts\start_hybridscan.ps1
#
# Then open http://localhost:3000 and verify the API is healthy at
# http://127.0.0.1:8000/api/v1/health. Local requests (127.0.0.1/::1/
# localhost) always open directly on the dashboard, no login required
# (see api/dependencies.py) - real authentication stays available at
# http://localhost:3000/login for a genuine, named session.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Launching HybridScan API in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command", "& '$PSScriptRoot\start_backend.ps1'"
)

Write-Host "Launching HybridScan frontend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command", "& '$PSScriptRoot\start_frontend.ps1'"
)

Write-Host ""
Write-Host "HybridScan is starting in two separate windows:" -ForegroundColor Green
Write-Host "  API:      http://127.0.0.1:8000/api/v1/health"
Write-Host "  Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Opens directly on Tableau de bord, no login required (local access)." -ForegroundColor Yellow
Write-Host "Close each window individually to stop that process." -ForegroundColor Yellow
