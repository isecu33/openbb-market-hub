"""
backend/services/alerts_engine.py
=================================
Motor de evaluación de alertas. Recorre las alertas activas y las comprueba
contra el estado actual del mercado/cartera. Cuando una se cumple, registra un
`AlertEvent` y actualiza la alerta.

Tipos soportados:
  - price_above / price_below : precio cruza un umbral.
  - pct_change_day            : variación intradía supera X % (abs).
  - pct_from_cost             : el P&L de la posición cruza X % (positivo o
                                negativo según el signo del umbral).
  - news                      : aparece una noticia con sentimiento marcado.
  - politician                : nuevo trade de político sobre el ticker.

No envía emails (el usuario eligió "app + tareas programadas"): los eventos se
consultan desde la web. El scheduler interno y/o una tarea programada externa
llaman a `evaluate_all` periódicamente.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from backend.models import Alert, AlertEvent, Asset, Position, AlertKind
from backend.services import openbb_client
from backend.services.sentiment import score_text


def _record(session: Session, alert: Alert, message: str) -> AlertEvent:
    ev = AlertEvent(alert_id=alert.id, message=message)
    alert.last_triggered_at = datetime.utcnow()
    alert.trigger_count += 1
    session.add(ev)
    session.add(alert)
    return ev


def _resolve_symbol(session: Session, alert: Alert) -> tuple[str | None, Asset | None]:
    if alert.asset_id:
        asset = session.get(Asset, alert.asset_id)
        if asset:
            return asset.symbol or alert.symbol, asset
    return alert.symbol, None


def _cooldown_ok(alert: Alert, hours: int = 12) -> bool:
    if not alert.last_triggered_at:
        return True
    return datetime.utcnow() - alert.last_triggered_at > timedelta(hours=hours)


def evaluate_all(session: Session) -> dict:
    alerts = session.exec(select(Alert).where(Alert.active == True)).all()  # noqa: E712
    triggered = []

    for alert in alerts:
        symbol, asset = _resolve_symbol(session, alert)
        try:
            ev = _evaluate_one(session, alert, symbol, asset)
        except Exception:  # noqa: BLE001
            ev = None
        if ev:
            triggered.append({"alert_id": alert.id, "message": ev.message})

    session.commit()
    return {"checked": len(alerts), "triggered": triggered}


def _evaluate_one(session: Session, alert: Alert, symbol: str | None, asset: Asset | None):
    kind = alert.kind

    if kind in (AlertKind.price_above, AlertKind.price_below):
        if not symbol or alert.threshold is None:
            return None
        q = openbb_client.quote(symbol)
        price = q.get("price")
        if price is None:
            return None
        price = float(price)
        if kind == AlertKind.price_above and price >= alert.threshold and _cooldown_ok(alert):
            return _record(session, alert, f"{symbol} ha superado {alert.threshold} (precio {price:.2f}).")
        if kind == AlertKind.price_below and price <= alert.threshold and _cooldown_ok(alert):
            return _record(session, alert, f"{symbol} ha caído por debajo de {alert.threshold} (precio {price:.2f}).")

    elif kind == AlertKind.pct_change_day:
        if not symbol or alert.threshold is None:
            return None
        q = openbb_client.quote(symbol)
        chg = q.get("change_pct")
        if chg is None:
            return None
        if abs(float(chg)) >= abs(alert.threshold) and _cooldown_ok(alert, hours=8):
            return _record(session, alert, f"{symbol} se mueve {float(chg):+.2f}% hoy (umbral {alert.threshold}%).")

    elif kind == AlertKind.pct_from_cost:
        if not asset or alert.threshold is None:
            return None
        pos = session.exec(select(Position).where(Position.asset_id == asset.id)).first()
        if not pos or not pos.invested_amount:
            return None
        value = (asset.last_price * pos.quantity) if (asset.last_price and pos.quantity) else (pos.market_value_import or 0)
        pnl_pct = (value - pos.invested_amount) / pos.invested_amount * 100
        thr = alert.threshold
        hit = pnl_pct >= thr if thr >= 0 else pnl_pct <= thr
        if hit and _cooldown_ok(alert, hours=24):
            return _record(session, alert, f"{asset.name or symbol}: P&L {pnl_pct:+.1f}% (umbral {thr:+.1f}%).")

    elif kind == AlertKind.news:
        if not symbol:
            return None
        news = openbb_client.company_news(symbol, limit=5)
        for n in news:
            s = score_text(n.get("title"))
            if s["label"] != "neutral":
                # Evitar repetir la misma noticia: cooldown corto + título en mensaje.
                if _cooldown_ok(alert, hours=6):
                    return _record(
                        session, alert,
                        f"Noticia {s['label']} sobre {symbol}: {n.get('title')}",
                    )
        return None

    elif kind == AlertKind.politician:
        # Comprobación ligera: ¿hay trades recientes del ticker?
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).resolve().parents[2]))
            from src.politician_tracker import _fetch_government_trades  # type: ignore
            trades, _ = _fetch_government_trades(None, 50)
            df = trades.to_df() if hasattr(trades, "to_df") else trades
            records = df.to_dict("records") if hasattr(df, "to_dict") else []
            for r in records:
                tkr = (r.get("symbol") or r.get("ticker") or "").upper()
                if symbol and tkr == symbol.upper() and _cooldown_ok(alert, hours=24):
                    who = r.get("representative") or r.get("name") or "un político"
                    return _record(session, alert, f"Nuevo trade declarado en {symbol} por {who} (recuerda el retraso de 45 días de la STOCK Act).")
        except Exception:  # noqa: BLE001
            return None

    return None
