"""
backend/app.py
==============
Backend FastAPI de OpenBB Market Hub.

Orquesta:
  - Persistencia SQLite (cartera, transacciones, alertas, snapshots).
  - Routers: portfolio, market, news, alerts, research.
  - Scheduler en segundo plano (refresco de precios + evaluación de alertas).
  - Servido del frontend React (build de Vite en frontend/dist) en producción.

Compatibilidad: los endpoints "legacy" (/thesis, /politician-trades, /portfolio)
se mantienen para no romper integraciones con OpenBB Workspace.

Arranque: bash backend/run_backend.sh   (o: uvicorn backend.app:app --reload)
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.config import FRONTEND_DIST  # noqa: E402
from backend.db import init_db  # noqa: E402
from backend.scheduler import start_scheduler, shutdown_scheduler  # noqa: E402
from backend.routers import portfolio, market, news, alerts, research  # noqa: E402
from backend.services import openbb_client  # noqa: E402

# Legacy (compatibilidad con OpenBB Workspace).
from src.thesis_energy import ThesisCriteria, screen_candidates  # noqa: E402
from src.politician_tracker import _fetch_government_trades, build_mirror_watchlist  # noqa: E402
from src.portfolio_tracker import Position as LegacyPosition, fetch_quote_and_news  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        start_scheduler()
    except Exception:  # noqa: BLE001
        pass
    yield
    shutdown_scheduler()


app = FastAPI(
    title="OpenBB Market Hub",
    description="Plataforma personal de research e inversión sobre OpenBB.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers nuevos --------------------------------------------------------
app.include_router(portfolio.router)
app.include_router(market.router)
app.include_router(news.router)
app.include_router(alerts.router)
app.include_router(research.router)


@app.get("/api/status")
def api_status():
    return {"status": "ok", "service": "openbb-market-hub", "openbb": openbb_client.available()}


# --- Endpoints legacy (compatibilidad OpenBB Workspace) --------------------
@app.get("/thesis")
def thesis(sector: str | None = None, min_revenue_growth: float | None = None, max_pe: float | None = None):
    criteria = ThesisCriteria(sector=sector, min_revenue_growth=min_revenue_growth, max_pe=max_pe)
    try:
        return {"candidates": screen_candidates(criteria)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/politician-trades")
def politician_trades(politician: str | None = None, days_back: int = 180,
                      build_watchlist: bool = False, min_trades: int = 2):
    try:
        trades, source = _fetch_government_trades(politician, days_back)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    if build_watchlist:
        return {"source": source, "watchlist": build_mirror_watchlist(trades, min_trades)}
    df = trades.to_df() if hasattr(trades, "to_df") else trades
    records = df.to_dict("records") if hasattr(df, "to_dict") else df
    return {"source": source, "trades": records}


@app.get("/portfolio")
def legacy_portfolio(symbols: list[str] = Query(...)):
    return {"positions": [fetch_quote_and_news(LegacyPosition(symbol=s.upper()).symbol) for s in symbols]}


# --- Servir el frontend React (build de Vite) ------------------------------
# La existencia de frontend/dist se comprueba en cada petición (no al importar):
# así, compilar el frontend con el backend ya arrancado funciona sin reiniciar.
@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """SPA fallback: cualquier ruta no-API devuelve index.html."""
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        return JSONResponse({
            "message": "Frontend no compilado. Ejecuta 'npm install && npm run build' en /frontend, "
                       "o arranca el dev server con 'npm run dev'.",
        })
    candidate = (FRONTEND_DIST / full_path).resolve()
    if candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
        return FileResponse(candidate)
    return FileResponse(index)
