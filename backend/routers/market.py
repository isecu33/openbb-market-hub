"""
backend/routers/market.py
=========================
Datos de mercado: cotización puntual, histórico para gráficos y búsqueda de
símbolos.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.services import openbb_client

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/quote/{symbol}")
def quote(symbol: str):
    return openbb_client.quote(symbol.upper())


@router.get("/history/{symbol}")
def history(symbol: str, days: int = 365, interval: str = "1d"):
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "series": openbb_client.historical(symbol.upper(), days=days, interval=interval),
    }


@router.get("/search")
def search(q: str):
    return {"query": q, "results": openbb_client.search(q)}
