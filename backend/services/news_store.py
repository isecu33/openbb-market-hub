"""
backend/services/news_store.py
==============================
Persistencia de noticias: el scheduler llama a `refresh_news` periódicamente
para descargar titulares de los activos de cartera/watchlist (+ mercado
global), puntuarlos (sentimiento + importancia) y guardarlos deduplicados en
SQLite. La web lee el feed almacenado (`feed`), que es instantáneo y no
depende de que el proveedor responda en ese momento.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from sqlmodel import Session, select

from backend.models import Asset, NewsItem, Position
from backend.services import openbb_client
from backend.services.sentiment import score_text, importance

RETENTION_DAYS = 30


def _dedupe_key(item: dict) -> str:
    base = item.get("url") or f"{item.get('symbol')}|{item.get('title')}"
    return hashlib.sha1((base or "").encode()).hexdigest()


def _tracked_symbols(session: Session, cap: int = 25) -> list[str]:
    symbols = []
    for a in session.exec(select(Asset).where(Asset.symbol.is_not(None))).all():
        has_pos = session.exec(select(Position).where(Position.asset_id == a.id)).first()
        if has_pos or a.in_watchlist:
            symbols.append(a.symbol)
    return sorted(set(symbols))[:cap]


def refresh_news(session: Session, limit_per_symbol: int = 8) -> dict:
    """Descarga, puntúa y persiste noticias nuevas. Devuelve contadores."""
    symbols = _tracked_symbols(session)
    raw: list[dict] = []
    for sym in symbols:
        raw.extend(openbb_client.company_news(sym, limit=limit_per_symbol))
    raw.extend(openbb_client.world_news(limit=15))

    inserted, skipped = 0, 0
    for item in raw:
        if not item.get("title"):
            continue
        key = _dedupe_key(item)
        exists = session.exec(select(NewsItem).where(NewsItem.dedupe_key == key)).first()
        if exists:
            skipped += 1
            continue
        text = f"{item.get('title')}. {item.get('summary') or ''}"
        senti = score_text(text)
        imp, category = importance(text, senti["score"])
        session.add(NewsItem(
            dedupe_key=key,
            symbol=item.get("symbol"),
            title=item["title"],
            url=item.get("url"),
            source=item.get("source"),
            published_at=item.get("date") or None,
            summary=item.get("summary"),
            sentiment_label=senti["label"],
            sentiment_score=senti["score"],
            importance=imp,
            category=category,
        ))
        inserted += 1

    # Poda de noticias antiguas para que la BD no crezca sin límite.
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    old = session.exec(select(NewsItem).where(NewsItem.created_at < cutoff)).all()
    for n in old:
        session.delete(n)

    session.commit()
    return {"symbols": symbols, "inserted": inserted, "skipped_duplicates": skipped,
            "pruned": len(old)}


def feed(session: Session, limit: int = 80, min_importance: int = 0,
         symbol: str | None = None, only_tracked: bool = False) -> list[dict]:
    stmt = select(NewsItem)
    if min_importance:
        stmt = stmt.where(NewsItem.importance >= min_importance)
    if symbol:
        stmt = stmt.where(NewsItem.symbol == symbol.upper())
    elif only_tracked:
        stmt = stmt.where(NewsItem.symbol.is_not(None))
    rows = session.exec(
        stmt.order_by(NewsItem.published_at.desc(), NewsItem.created_at.desc()).limit(limit)
    ).all()
    return [
        {
            "id": n.id,
            "symbol": n.symbol,
            "title": n.title,
            "url": n.url,
            "source": n.source,
            "date": n.published_at,
            "summary": n.summary,
            "sentiment": {"label": n.sentiment_label, "score": n.sentiment_score},
            "importance": n.importance,
            "category": n.category,
        }
        for n in rows
    ]
