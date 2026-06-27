#!/usr/bin/env bash
# run_backend.sh
# ----------------
# Levanta un backend FastAPI local que sirve los datos de OpenBB para que
# puedas conectarlo desde OpenBB Workspace (pro.openbb.co -> Apps -> Connect
# backend -> http://localhost:8000).
#
# Uso:
#   bash backend/run_backend.sh
#   PORT=9000 bash backend/run_backend.sh

set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"

if [ ! -d ".venv" ]; then
  echo "No se encontró .venv. Crea el entorno primero:"
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Arrancando backend OpenBB en http://localhost:${PORT} ..."
echo "Conéctalo desde OpenBB Workspace (pro.openbb.co) como backend personalizado."
uvicorn backend.app:app --host 0.0.0.0 --port "${PORT}" --reload
