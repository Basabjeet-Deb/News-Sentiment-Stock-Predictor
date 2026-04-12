$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

Write-Host "========================================"
Write-Host "  StockSense - One-click Launcher"
Write-Host "========================================"
Write-Host ""

function Activate-Venv {
  $candidates = @(
    Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
    Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
  )
  foreach ($p in $candidates) {
    if (Test-Path $p) {
      . $p
      Write-Host "[OK] Activated venv: $p"
      return $true
    }
  }
  Write-Host "[WARN] No venv found (.venv/venv). Using system Python."
  return $false
}

function Stop-PortListener([int]$Port) {
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    foreach ($c in $conns) {
      Write-Host "[INFO] Port $Port in use by PID $($c.OwningProcess). Stopping it..."
      Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  } catch {
    # Older Windows or no listener: ignore
  }
}

function Start-Backend {
  $cmd = 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8000'
  Write-Host ""
  Write-Host "[INFO] Starting backend on http://127.0.0.1:8000 ..."
  Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WindowStyle Normal | Out-Null
}

function Open-UI {
  Start-Sleep -Seconds 2
  Start-Process "http://127.0.0.1:8000/" | Out-Null
}

function Trigger-Pipeline {
  Write-Host ""
  Write-Host "[INFO] Triggering pipeline run via API..."
  try {
    Invoke-WebRequest -UseBasicParsing -Method POST "http://127.0.0.1:8000/api/v1/pipeline/run" | Out-Null
    Write-Host "[OK] Pipeline started."
  } catch {
    Write-Host "[WARN] Pipeline start failed: $($_.Exception.Message)"
  }
}

function Start-GdeltBackfill([int]$Days) {
  Write-Host ""
  Write-Host "[INFO] Starting GDELT backfill for $Days days..."
  $cmd = "python -m pipeline.gdelt_backfill --days $Days --max-per-day 250 --sleep 0.8"
  Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd -WindowStyle Normal | Out-Null
}

Activate-Venv | Out-Null
Stop-PortListener -Port 8000
Start-Backend
Open-UI

if ($env:AUTORUN_PIPELINE -eq "1") {
  Trigger-Pipeline
}

if ($env:AUTORUN_GDELT_DAYS) {
  $d = 0
  if ([int]::TryParse($env:AUTORUN_GDELT_DAYS, [ref]$d) -and $d -gt 0) {
    Start-GdeltBackfill -Days $d
  } else {
    Write-Host "[WARN] AUTORUN_GDELT_DAYS is not a valid positive integer."
  }
}

Write-Host ""
Write-Host "========================================"
Write-Host "Started."
Write-Host "- Backend window: StockSense Backend"
Write-Host "- UI: http://127.0.0.1:8000/"
Write-Host ""
Write-Host "Tip: Auto-run pipeline:"
Write-Host "  set AUTORUN_PIPELINE=1 && run_all.bat"
Write-Host "Tip: Backfill historical news from GDELT:"
Write-Host "  set AUTORUN_GDELT_DAYS=30 && run_all.bat"
Write-Host "========================================"

