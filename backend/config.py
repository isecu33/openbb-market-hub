"""
backend/config.py
=================
Configuración central del backend. Carga el .env de la raíz del proyecto y
expone rutas y constantes usadas por el resto de módulos.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Carpeta de datos persistentes (SQLite, uploads procesados, etc.)
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "market_hub.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Frontend: en producción servimos el build de Vite (frontend/dist);
# en desarrollo el frontend corre aparte con `npm run dev`.
FRONTEND_DIST = ROOT / "frontend" / "dist"

# Divisa base para consolidar la cartera.
BASE_CURRENCY = os.getenv("BASE_CURRENCY", "EUR")

# Claves API (las leen los scripts de OpenBB).
FMP_API_KEY = os.getenv("FMP_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")

PORT = int(os.getenv("PORT", "8000"))

# Intervalos del scheduler (minutos).
PRICE_REFRESH_MINUTES = int(os.getenv("PRICE_REFRESH_MINUTES", "30"))
ALERT_CHECK_MINUTES = int(os.getenv("ALERT_CHECK_MINUTES", "15"))
NEWS_REFRESH_MINUTES = int(os.getenv("NEWS_REFRESH_MINUTES", "60"))

# Hora local (HH:MM) a la que se genera la sugerencia diaria; la semanal se
# genera los lunes a la misma hora.
SUGGESTION_HOUR = os.getenv("SUGGESTION_HOUR", "08:30")

# Clave opcional de Anthropic: si está, las sugerencias incluyen un briefing
# redactado por Claude además del ranking cuantitativo.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
