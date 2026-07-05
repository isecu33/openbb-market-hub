"""
backend/routers/news.py
=======================
Noticias con sentimiento: por activo, agregadas de toda la cartera/watchlist,
y feed general de mercado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.db import get_session
from backend.models import Asset, Position
from backend.services import openbb_client
from backend.services import news_store
from backend.services.sentiment import annotate

router = APIRouter(prefix="/api/news", tags=["news"])


# ---- Feed persistido (lo alimenta el scheduler) ----------------------------

@router.get("/feed")
def news_feed(limit: int = 80, min_importance: int = 0, symbol: str | None = None,
              session: Session = Depends(get_session)):
    """Noticias almacenadas (instantáneo). `min_importance` filtra por relevancia
    inversora (0-100); 40+ suele indicar un evento accionable."""
    items = news_store.feed(session, limit=limit, min_importance=min_importance, symbol=symbol)
    pos = sum(1 for n in items if n["sentiment"]["label"] == "positive")
    neg = sum(1 for n in items if n["sentiment"]["label"] == "negative")
    return {
        "news": items,
        "sentiment_summary": {"positive": pos, "negative": neg, "neutral": len(items) - pos - neg},
    }


@router.post("/refresh")
def news_refresh(session: Session = Depends(get_session)):
    """Fuerza una descarga de noticias ahora (el scheduler ya lo hace periódicamente)."""
    return news_store.refresh_news(session)


@router.get("/symbol/{symbol}")
def news_for_symbol(symbol: str, limit: int = 12):
    items = openbb_client.company_news(symbol.upper(), limit=limit)
    return {"symbol": symbol.upper(), "news": annotate(items)}


@router.get("/world")
def news_world(limit: int = 20):
    return {"news": annotate(openbb_client.world_news(limit=limit))}


@router.get("/portfolio")
def news_for_portfolio(limit_per_symbol: int = 4, session: Session = Depends(get_session)):
    """Agrega noticias de todos los activos de cartera + watchlist con ticker."""
    rows = session.exec(select(Asset)).all()
    # Sólo activos con ticker cotizable (los fondos por ISIN rara vez traen news).
    symbols = []
    for a in rows:
        if a.symbol:
            has_pos = session.exec(select(Position).where(Position.asset_id == a.id)).first()
            if has_pos or a.in_watchlist:
                symbols.append(a.symbol)
    symbols = sorted(set(symbols))[:25]

    all_news = []
    for sym in symbols:
        all_news.extend(openbb_client.company_news(sym, limit=limit_per_symbol))
    annotate(all_news)
    all_news.sort(key=lambda n: n.get("date") or "", reverse=True)

    pos = sum(1 for n in all_news if n.get("sentiment", {}).get("label") == "positive")
    neg = sum(1 for n in all_news if n.get("sentiment", {}).get("label") == "negative")
    return {
        "symbols": symbols,
        "news": all_news[:60],
        "sentiment_summary": {"positive": pos, "negative": neg, "neutral": len(all_news) - pos - neg},
    }
