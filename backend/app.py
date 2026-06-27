"""
backend/app.py
==============
App FastAPI mínima que expone los tres casos de uso del proyecto como
endpoints HTTP, pensada para conectarse desde OpenBB Workspace o para
consumirse desde cualquier otro cliente (script, navegador, etc.).

Arranque: bash backend/run_backend.sh
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.thesis_energy import ThesisCriteria, screen_candidates  # noqa: E402
from src.politician_tracker import _fetch_government_trades, build_mirror_watchlist  # noqa: E402
from src.portfolio_tracker import Position, fetch_quote_and_news  # noqa: E402

app = FastAPI(
    title="OpenBB Market Hub",
    description="Backend personal de research: tesis temáticas, tracker de políticos y watchlist con noticias.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"status": "ok", "service": "openbb-market-hub"}


@app.get("/thesis")
def thesis(
    sector: str | None = None,
    min_revenue_growth: float | None = None,
    max_pe: float | None = None,
):
    criteria = ThesisCriteria(sector=sector, min_revenue_growth=min_revenue_growth, max_pe=max_pe)
    try:
        return {"candidates": screen_candidates(criteria)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/politician-trades")
def politician_trades(
    politician: str | None = None,
    days_back: int = 180,
    build_watchlist: bool = False,
    min_trades: int = 2,
):
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
def portfolio(symbols: list[str] = Query(..., description="Tickers, p. ej. ?symbols=AAPL&symbols=MSFT")):
    return {"positions": [fetch_quote_and_news(Position(symbol=s.upper()).symbol) for s in symbols]}
