#!/usr/bin/env bash
# post-create.sh — se ejecuta una vez al crear el devcontainer.
# Prepara .venv (Linux) y node_modules dentro de sus volúmenes, e inicializa .env.
set -euo pipefail

# Los volúmenes se montan como root; devuélvelos al usuario del contenedor.
sudo chown -R "$(id -un)":"$(id -gn)" .venv frontend/node_modules 2>/dev/null || true

if [ ! -f ".venv/bin/activate" ]; then
  echo "Creando entorno virtual de Python..."
  python -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalando dependencias del frontend..."
( cd frontend && npm install )

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "AVISO: se ha creado .env desde .env.example — rellena tus claves (FMP, FRED)."
fi

echo
echo "Devcontainer listo. Arranca con:"
echo "  BUILD_FRONTEND=1 bash backend/run_backend.sh   # primera vez (compila la web)"
echo "  bash backend/run_backend.sh                    # siguientes"
