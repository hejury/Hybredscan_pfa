# start_backend.ps1 - Starts the HybridScan FastAPI bridge.
#
# Usage:
#   .\scripts\start_backend.ps1                 # normal mode
#   .\scripts\start_backend.ps1 -Reload         # development mode (auto-reload)
#
# The API does NOT auto-start the folder watcher (Protection) - it must
# be activated explicitly from /protection or POST /api/v1/protection/start.
# Health check once running: http://127.0.0.1:8000/api/v1/health
#
# Local access bypass (api/dependencies.py::get_current_user): a request
# whose client address is 127.0.0.1/::1/localhost is always let through
# without a login, so both the web frontend and the desktop app
# (run_desktop.py, at the repo root) open directly on the dashboard.
# It does nothing for a request arriving from any other host. Real
# authentication (/auth/login, /auth/register, /auth/logout) keeps
# working normally on top of it, and a real session always takes
# priority over the bypass.

param(
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Starting HybridScan API (FastAPI) from $repoRoot" -ForegroundColor Cyan

$uvicornArgs = @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000")
if ($Reload) {
    $uvicornArgs += "--reload"
    Write-Host "Reload mode enabled (development only)." -ForegroundColor Yellow
} else {
    Write-Host "Stable mode (no --reload) - recommended for demo/soutenance." -ForegroundColor Green
}

python @uvicornArgs
