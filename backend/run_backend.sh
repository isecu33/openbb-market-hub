#!/usr/bin/env bash
# run_backend.sh
# ----------------
# Levanta el backend FastAPI de OpenBB Market Hub. Sirve la API en /api/* y,
# si existe frontend/dist, también la web React. Conéctalo además desde OpenBB
# Workspace (pro.openbb.co -> Apps -> Connect backend -> http://localhost:8000).
#
# Uso:
#   bash backend/run_backend.sh                # arranca el backend
#   BUILD_FRONTEND=1 bash backend/run_backend.sh   # compila la web antes de arrancar
#   PORT=9000 bash backend/run_backend.sh

set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8000}"

# Comprueba bin/activate (no solo el directorio): en el devcontainer el .venv
# de Windows del host queda tapado por un volumen vacío hasta que post-create
# lo rellena, y un venv de Windows no tiene bin/.
if [ ! -f ".venv/bin/activate" ]; then
  echo "No se encontró un .venv de este sistema. Créalo primero:"
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  echo "  (en el devcontainer: bash .devcontainer/post-create.sh)"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

if [ "${BUILD_FRONTEND:-0}" = "1" ]; then
  echo "Compilando frontend..."
  ( cd frontend && npm install && npm run build )
fi

echo "Arrancando OpenBB Market Hub en http://localhost:${PORT} ..."
uvicorn backend.app:app --host 0.0.0.0 --port "${PORT}" --reload
