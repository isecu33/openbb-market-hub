# bootstrap_run.ps1 — Instala y levanta OpenBB Market Hub, registrando todo en
# data\bootstrap.log para poder monitorizar el progreso.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path "data" | Out-Null
$log = Join-Path $root "data\bootstrap.log"
"" | Set-Content $log
function Log($m) { $ts = Get-Date -Format "HH:mm:ss"; Add-Content $log "[$ts] $m"; Write-Host "[$ts] $m" }

Log "STATUS: START"
Log "root=$root"

# 1) Detectar Python
$PyExe = $null; $PyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue)      { $PyExe = "py"; $PyArgs = @("-3") }
elseif (Get-Command python -ErrorAction SilentlyContinue)  { $PyExe = "python" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $PyExe = "python3" }
if (-not $PyExe) { Log "ERROR: no se encontro Python en PATH"; Log "STATUS: FAILED"; return }
$pv = (& $PyExe $PyArgs --version) 2>&1
Log "python: $PyExe $PyArgs -> $pv"

# 2) Crear venv si falta
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Log "STATUS: CREATING_VENV"
  & $PyExe $PyArgs -m venv .venv 2>&1 | Tee-Object -FilePath $log -Append
}
$vpy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) { Log "ERROR: no se creo el venv"; Log "STATUS: FAILED"; return }

# 3) Instalar dependencias Python (esto puede tardar varios minutos, sobre todo OpenBB)
Log "STATUS: PIP_UPGRADE"
& $vpy -m pip install --upgrade pip 2>&1 | Tee-Object -FilePath $log -Append
Log "STATUS: PIP_INSTALL (puede tardar 5-15 min por OpenBB)"
& $vpy -m pip install -r requirements.txt 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) { Log "WARN: pip install devolvio codigo $LASTEXITCODE (continuo igualmente)" }
Log "STATUS: PIP_DONE"

# 4) Frontend: limpiar node_modules roto, instalar y compilar
if (Get-Command npm -ErrorAction SilentlyContinue) {
  if (Test-Path "frontend\node_modules") {
    Log "Limpiando frontend\node_modules previo..."
    Remove-Item -Recurse -Force "frontend\node_modules" -ErrorAction SilentlyContinue
  }
  Push-Location frontend
  Log "STATUS: NPM_INSTALL"
  cmd /c "npm install" 2>&1 | Tee-Object -FilePath $log -Append
  Log "STATUS: NPM_BUILD"
  cmd /c "npm run build" 2>&1 | Tee-Object -FilePath $log -Append
  Pop-Location
  if (Test-Path "frontend\dist\index.html") { Log "STATUS: FRONTEND_OK" } else { Log "WARN: no se genero frontend\dist" }
} else {
  Log "WARN: npm no encontrado; se servira solo la API"
}

# 5) Abrir el navegador en cuanto el server responda (job en segundo plano)
Start-Job -ScriptBlock {
  for ($i=0; $i -lt 60; $i++) {
    try { Invoke-WebRequest -UseBasicParsing "http://localhost:8000/api/status" -TimeoutSec 2 | Out-Null; Start-Process "http://localhost:8000"; break }
    catch { Start-Sleep 2 }
  }
} | Out-Null

# 6) Arrancar el servidor (bloqueante)
Log "STATUS: LAUNCHING_SERVER"
& $vpy -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 2>&1 | Tee-Object -FilePath $log -Append
