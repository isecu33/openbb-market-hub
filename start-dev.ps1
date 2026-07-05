# start-dev.ps1 — Arranca backend (FastAPI) y frontend (Vite) en modo desarrollo.
# Uso:  powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
# Backend en http://localhost:8000  ·  Frontend en http://localhost:5173

Write-Host "OpenBB Market Hub — modo desarrollo" -ForegroundColor Cyan

# Python del proyecto: SIEMPRE .venv (el `python` del PATH puede ser otro entorno).
$venvPython = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
  Write-Host "Creando entorno virtual e instalando dependencias..." -ForegroundColor Yellow
  $sysPython = Get-Command py -ErrorAction SilentlyContinue
  if ($sysPython) { py -3 -m venv .venv } else { python -m venv .venv }
  & $venvPython -m pip install -r requirements.txt
}

$busy = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($busy) {
  Write-Host "El puerto 8000 ya está en uso (PID $($busy[0].OwningProcess)); no arranco otro backend." -ForegroundColor Yellow
} else {
  Start-Process powershell -ArgumentList '-NoExit','-Command',`
    '& .\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --port 8000'
}

# Frontend
if (-Not (Test-Path "frontend\node_modules\.bin\vite.cmd")) {
  Write-Host "Instalando dependencias del frontend..." -ForegroundColor Yellow
  Push-Location frontend; npm install; Pop-Location
}
Start-Process powershell -ArgumentList '-NoExit','-Command','cd frontend; npm run dev'

Start-Sleep 3
Start-Process "http://localhost:5173"
Write-Host "Backend: http://localhost:8000  |  Frontend: http://localhost:5173" -ForegroundColor Green
