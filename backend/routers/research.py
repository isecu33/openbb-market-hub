"""
backend/routers/research.py
===========================
Reexpone los dos casos de uso de research del proyecto original:
  - Tesis temática (screener de candidatas).
  - Government Trades (operaciones de políticos de EE. UU.).

Mantiene el aviso de la STOCK Act (retraso de hasta 45 días) en la respuesta.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.thesis_energy import ThesisCriteria, screen_candidates  # noqa: E402
from src.politician_tracker import (  # noqa: E402
    _fetch_government_trades,
    build_mirror_watchlist,
    STOCK_ACT_DISCLOSURE_DELAY_DAYS,
)

from fastapi import Depends
from sqlmodel import Session

from backend.db import get_session  # noqa: E402
from backend.services import jobs  # noqa: E402
from backend.services import suggest  # noqa: E402

router = APIRouter(prefix="/api/research", tags=["research"])


# ---- Sugerencias diarias/semanales -----------------------------------------

@router.get("/suggestions")
def suggestions(period: str = "daily", session: Session = Depends(get_session)):
    """Última sugerencia generada (el scheduler crea una diaria y otra semanal)."""
    out = suggest.latest(session, period=period)
    return out or {"period": period, "empty": True,
                   "hint": "Aún no hay sugerencias: genera una o espera al scheduler."}


@router.get("/suggestions/generate")
def suggestions_generate(period: str = "daily", refresh: bool = False):
    """Genera una sugerencia ahora, como trabajo en segundo plano (sondéable)."""
    def work():
        from backend.db import session_scope
        with session_scope() as s:
            return suggest.generate(s, period=period)

    snap = jobs.get_or_submit(jobs.make_key("suggestions", {"period": period}), work, refresh=refresh)
    out = {k: v for k, v in snap.items() if k != "result"}
    if snap["status"] == "done":
        out["suggestion"] = snap["result"]
    return out

# Estas consultas tardan (varias llamadas API por ticker), así que corren como
# trabajos en segundo plano: la respuesta es un snapshot {status: running|done|
# error} que el frontend sondea. Peticiones con los mismos parámetros se
# enganchan al trabajo en curso o al resultado cacheado, nunca lo relanzan.


@router.get("/thesis")
def thesis(sector: str | None = None, min_revenue_growth: float | None = None,
           max_pe: float | None = None, refresh: bool = False):
    params = {"sector": sector, "min_revenue_growth": min_revenue_growth, "max_pe": max_pe}

    def work():
        criteria = ThesisCriteria(**params)
        return {"candidates": screen_candidates(criteria)}

    snap = jobs.get_or_submit(jobs.make_key("thesis", params), work, refresh=refresh)
    out = {k: v for k, v in snap.items() if k != "result"}
    if snap["status"] == "done":
        out.update(snap["result"])
    return out


@router.get("/politicians")
def politicians(politician: str | None = None, days_back: int = 180,
                build_watchlist: bool = False, min_trades: int = 2,
                refresh: bool = False):
    params = {"politician": politician, "days_back": days_back,
              "build_watchlist": build_watchlist, "min_trades": min_trades}

    disclaimer = (
        f"La STOCK Act permite hasta {STOCK_ACT_DISCLOSURE_DELAY_DAYS} días de retraso "
        "entre la operación y su divulgación. Estos datos son históricos/contextuales, "
        "nunca señales en tiempo real."
    )

    def work():
        trades, source = _fetch_government_trades(politician, days_back)
        if build_watchlist:
            return {"source": source, "watchlist": build_mirror_watchlist(trades, min_trades)}
        df = trades.to_df() if hasattr(trades, "to_df") else trades
        records = df.to_dict("records") if hasattr(df, "to_dict") else df
        return {"source": source, "trades": records}

    snap = jobs.get_or_submit(jobs.make_key("politicians", params), work, refresh=refresh)
    out = {k: v for k, v in snap.items() if k != "result"}
    out["disclaimer"] = disclaimer
    if snap["status"] == "done":
        out.update(snap["result"])
    return out
