# start.ps1 — Compila el frontend y arranca un único servidor (backend sirve la web).
# Uso:  powershell -ExecutionPolicy Bypass -File .\start.ps1
# Todo en http://localhost:8000

Write-Host "OpenBB Market Hub — arranque" -ForegroundColor Cyan

# Python del proyecto: SIEMPRE .venv (el `python` del PATH puede ser otro entorno).
$venvPython = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
  Write-Host "Creando entorno virtual e instalando dependencias..." -ForegroundColor Yellow
  $sysPython = Get-Command py -ErrorAction SilentlyContinue
  if ($sysPython) { py -3 -m venv .venv } else { python -m venv .venv }
  & $venvPython -m pip install -r requirements.txt
}

# Puerto ocupado -> probablemente ya hay una instancia corriendo.
$busy = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($busy) {
  Write-Host "El puerto 8000 ya está en uso (PID $($busy[0].OwningProcess))." -ForegroundColor Red
  Write-Host "Cierra esa instancia (Stop-Process -Id $($busy[0].OwningProcess)) o abre http://localhost:8000" -ForegroundColor Yellow
  exit 1
}

Push-Location frontend
if (-Not (Test-Path "node_modules\.bin\vite.cmd")) { npm install }
npm run build
Pop-Location

Start-Sleep 2
Start-Process "http://localhost:8000"
& $venvPython -m uvicorn backend.app:app --port 8000
