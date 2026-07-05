"""
backend/services/openbb_client.py
=================================
Capa fina sobre OpenBB Platform. Centraliza la carga de credenciales y
expone funciones simples (quote, histórico, noticias, búsqueda) con manejo
defensivo: los nombres de endpoint cambian entre versiones de OpenBB, así que
probamos varias rutas antes de rendirnos (patrón `_try` del repo).

Todas las funciones devuelven estructuras Python normales (dict/list) y nunca
lanzan: si algo falla, devuelven un campo `error` para que la API siga viva.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from functools import lru_cache
from threading import Lock
from typing import Any

from backend.config import FMP_API_KEY, FRED_API_KEY

try:
    from openbb import obb
    _OBB_OK = True
except Exception:  # noqa: BLE001
    obb = None  # type: ignore
    _OBB_OK = False

# Cargar credenciales una vez.
if _OBB_OK:
    try:
        if FMP_API_KEY:
            obb.user.credentials.fmp_api_key = FMP_API_KEY
        if FRED_API_KEY:
            obb.user.credentials.fred_api_key = FRED_API_KEY
    except Exception:  # noqa: BLE001
        pass


def available() -> bool:
    return _OBB_OK


def _to_records(result: Any) -> list[dict]:
    """Normaliza la salida de OpenBB a una lista de dicts."""
    if result is None:
        return []
    try:
        df = result.to_df() if hasattr(result, "to_df") else result
    except Exception:  # noqa: BLE001
        df = result
    if hasattr(df, "reset_index"):
        try:
            df = df.reset_index()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(df, "to_dict"):
        return df.to_dict("records")
    if isinstance(df, list):
        return df
    return []


# Caché de cotizaciones con TTL: el motor de alertas y el refresco de cartera
# piden los mismos símbolos en ráfaga; sin esto se quema la cuota gratuita del
# proveedor. TTL corto para no servir precios rancios.
_QUOTE_TTL_SECONDS = int(os.getenv("QUOTE_CACHE_TTL", "120"))
_quote_cache: dict[str, tuple[float, dict]] = {}
_quote_lock = Lock()


def quote(symbol: str, *, use_cache: bool = True) -> dict:
    """Cotización rápida de una acción/ETF (cacheada _QUOTE_TTL_SECONDS)."""
    if not _OBB_OK:
        return {"symbol": symbol, "error": "OpenBB no disponible"}
    symbol = symbol.upper()
    if use_cache:
        with _quote_lock:
            hit = _quote_cache.get(symbol)
        if hit and time.monotonic() - hit[0] < _QUOTE_TTL_SECONDS:
            return dict(hit[1])
    out: dict = {"symbol": symbol, "price": None, "change_pct": None, "currency": None}
    try:
        res = obb.equity.price.quote(symbol=symbol)
        rows = _to_records(res)
        if rows:
            r = rows[0]
            out["price"] = (
                r.get("last_price") or r.get("close") or r.get("price") or r.get("prev_close")
            )
            out["change_pct"] = r.get("change_percent") or r.get("change_pct")
            out["currency"] = r.get("currency")
            out["name"] = r.get("name")
            out["prev_close"] = r.get("prev_close")
            out["day_high"] = r.get("high") or r.get("day_high")
            out["day_low"] = r.get("low") or r.get("day_low")
            out["volume"] = r.get("volume")
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    if out.get("price") is not None:
        with _quote_lock:
            _quote_cache[symbol] = (time.monotonic(), dict(out))
    return out


def historical(symbol: str, days: int = 365, interval: str = "1d") -> list[dict]:
    """Serie histórica de precios. FMP restringe muchos símbolos (ETFs) al plan
    de pago (402), así que se intenta el proveedor por defecto y como fallback
    yfinance (gratis, sin clave)."""
    if not _OBB_OK:
        return []
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    attempts = [
        lambda: obb.equity.price.historical(symbol=symbol, start_date=start, interval=interval),
        lambda: obb.equity.price.historical(symbol=symbol, start_date=start, interval=interval,
                                            provider="yfinance"),
    ]
    for fn in attempts:
        try:
            rows = _to_records(fn())
        except Exception:  # noqa: BLE001
            continue
        cleaned = []
        for r in rows:
            d = r.get("date") or r.get("index")
            cleaned.append({
                "date": str(d)[:10] if d is not None else None,
                "open": r.get("open"),
                "high": r.get("high"),
                "low": r.get("low"),
                "close": r.get("close"),
                "volume": r.get("volume"),
            })
        cleaned = [c for c in cleaned if c["close"] is not None]
        if cleaned:
            return cleaned
    return []


def _news_rows_to_items(rows: list[dict], limit: int, symbol: str | None = None) -> list[dict]:
    out = []
    for r in rows[:limit]:
        out.append({
            "title": r.get("title"),
            "date": str(r.get("date") or r.get("published_date") or "")[:19],
            "source": r.get("source") or r.get("provider"),
            "url": r.get("url") or r.get("link"),
            "summary": r.get("text") or r.get("summary"),
            "symbol": symbol,
        })
    return out


def company_news(symbol: str, limit: int = 12) -> list[dict]:
    """Noticias de un símbolo. FMP restringió news al plan de pago (402), así
    que se prueba el proveedor por defecto y como fallback yfinance (gratis,
    sin clave)."""
    if not _OBB_OK:
        return []
    attempts = [
        lambda: obb.news.company(symbol=symbol, limit=limit),
        lambda: obb.news.company(symbol=symbol, provider="yfinance", limit=limit),
    ]
    for fn in attempts:
        try:
            rows = _to_records(fn())
            if rows:
                return _news_rows_to_items(rows, limit, symbol)
        except Exception:  # noqa: BLE001
            continue
    return []


# Sin proveedor gratuito de "world news" (benzinga/fmp/intrinio/tiingo piden
# clave de pago): se aproxima con noticias de ETFs macro vía yfinance.
_WORLD_PROXIES = ["SPY", "QQQ", "EFA", "TLT", "GLD"]


def world_news(limit: int = 20) -> list[dict]:
    if not _OBB_OK:
        return []
    try:
        res = obb.news.world(limit=limit)
        rows = _to_records(res)
        if rows:
            return _news_rows_to_items(rows, limit)
    except Exception:  # noqa: BLE001
        pass
    # Fallback: agregar titulares de proxies macro (mercado global).
    seen, out = set(), []
    per = max(3, limit // len(_WORLD_PROXIES))
    for proxy in _WORLD_PROXIES:
        for item in company_news(proxy, limit=per):
            key = item.get("url") or item.get("title")
            if key and key not in seen:
                seen.add(key)
                item["symbol"] = None
                out.append(item)
    out.sort(key=lambda n: n.get("date") or "", reverse=True)
    return out[:limit]


@lru_cache(maxsize=256)
def search_symbol(query: str) -> tuple:
    """Busca un símbolo/empresa. Cacheado porque es relativamente caro."""
    if not _OBB_OK:
        return tuple()
    attempts = [
        lambda: obb.equity.search(query),
        lambda: obb.equity.search(query, provider="sec"),
    ]
    for fn in attempts:
        try:
            rows = _to_records(fn())
            results = []
            for r in rows[:10]:
                results.append({
                    "symbol": r.get("symbol") or r.get("ticker"),
                    "name": r.get("name") or r.get("long_name"),
                })
            if results:
                return tuple(tuple(sorted(d.items())) for d in results)
        except Exception:  # noqa: BLE001
            continue
    return tuple()


def search(query: str) -> list[dict]:
    return [dict(t) for t in search_symbol(query)]
