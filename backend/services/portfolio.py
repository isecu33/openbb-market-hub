"""
backend/services/portfolio.py
=============================
Lógica de cartera: upsert de activos, aplicación de imports, refresco de
precios y cálculo de la vista consolidada con P&L.

Reglas de valoración (en orden de preferencia):
  1. Si el activo tiene cotización en vivo (`asset.last_price`, normalmente
     acciones/ETF vía OpenBB) -> valor = last_price * quantity.
  2. Si no, se usa el valor de mercado importado del bróker
     (`position.market_value_import`), típico de fondos por ISIN.
  3. Si tampoco, se cae al importe invertido (P&L = 0).
"""

from __future__ import annotations

from datetime import datetime, date

from sqlmodel import Session, select

from backend.models import Asset, Position, Transaction, PortfolioSnapshot, AssetKind, TxType
from backend.services import openbb_client


# ---------------------------------------------------------------------------
# Upsert de activos
# ---------------------------------------------------------------------------

def find_or_create_asset(
    session: Session,
    *,
    isin: str | None = None,
    symbol: str | None = None,
    name: str | None = None,
    kind: str = "equity",
    currency: str = "EUR",
) -> Asset:
    asset = None
    if isin:
        asset = session.exec(select(Asset).where(Asset.isin == isin)).first()
    if asset is None and symbol:
        asset = session.exec(select(Asset).where(Asset.symbol == symbol)).first()
    if asset is None and name and not isin and not symbol:
        asset = session.exec(select(Asset).where(Asset.name == name)).first()

    if asset is None:
        asset = Asset(
            isin=isin, symbol=symbol, name=name,
            kind=AssetKind(kind) if kind in AssetKind._value2member_map_ else AssetKind.other,
            currency=currency or "EUR",
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
    else:
        # Completar campos que falten.
        changed = False
        if name and not asset.name:
            asset.name = name; changed = True
        if symbol and not asset.symbol:
            asset.symbol = symbol; changed = True
        if isin and not asset.isin:
            asset.isin = isin; changed = True
        if changed:
            session.add(asset); session.commit(); session.refresh(asset)
    return asset


# ---------------------------------------------------------------------------
# Aplicar imports
# ---------------------------------------------------------------------------

def apply_positions(session: Session, parsed_positions: list[dict], account: str = "MyInvestor") -> dict:
    created, updated = 0, 0
    for p in parsed_positions:
        asset = find_or_create_asset(
            session,
            isin=p.get("isin"), symbol=p.get("symbol"), name=p.get("name"),
            kind=p.get("kind", "fund"), currency=p.get("currency", "EUR"),
        )
        # Precio de fondo importado: lo usamos como last_price si no hay otro.
        if p.get("nav") and not asset.last_price:
            asset.last_price = p["nav"]
            asset.last_price_at = datetime.utcnow()
            asset.price_source = "import"
            session.add(asset)

        pos = session.exec(select(Position).where(Position.asset_id == asset.id)).first()
        if pos is None:
            pos = Position(asset_id=asset.id, account=account)
            created += 1
        else:
            updated += 1
        pos.quantity = p.get("quantity") or pos.quantity or 0.0
        pos.avg_price = p.get("avg_price") if p.get("avg_price") is not None else pos.avg_price
        pos.invested_amount = p.get("invested") if p.get("invested") is not None else pos.invested_amount
        pos.market_value_import = p.get("market_value") if p.get("market_value") is not None else pos.market_value_import
        pos.updated_at = datetime.utcnow()
        session.add(pos)
    session.commit()
    return {"created": created, "updated": updated}


def apply_transactions(session: Session, parsed_tx: list[dict], source: str = "import") -> dict:
    inserted = 0
    for t in parsed_tx:
        asset = find_or_create_asset(
            session,
            isin=t.get("isin"), symbol=t.get("symbol"), name=t.get("name"),
            kind=t.get("kind", "fund"),
        )
        tx = Transaction(
            asset_id=asset.id,
            tx_type=TxType(t["tx_type"]) if t.get("tx_type") in TxType._value2member_map_ else TxType.buy,
            tx_date=t.get("date"),
            quantity=t.get("quantity"),
            price=t.get("price"),
            amount=t.get("amount"),
            source=source,
        )
        session.add(tx)
        inserted += 1
    session.commit()
    return {"inserted": inserted}


# ---------------------------------------------------------------------------
# Refresco de precios
# ---------------------------------------------------------------------------

def refresh_prices(session: Session) -> dict:
    """Actualiza last_price de los activos que tengan ticker cotizable."""
    assets = session.exec(select(Asset).where(Asset.symbol.is_not(None))).all()
    ok, fail = 0, 0
    for asset in assets:
        q = openbb_client.quote(asset.symbol)
        if q.get("price"):
            asset.last_price = float(q["price"])
            asset.last_price_at = datetime.utcnow()
            asset.price_source = "openbb"
            if q.get("currency") and not asset.currency:
                asset.currency = q["currency"]
            session.add(asset)
            ok += 1
        else:
            fail += 1
    session.commit()
    return {"updated": ok, "failed": fail}


# ---------------------------------------------------------------------------
# Vista consolidada
# ---------------------------------------------------------------------------

def _position_value(asset: Asset, pos: Position) -> tuple[float, float, str]:
    """Devuelve (valor_mercado, invertido, fuente_precio)."""
    invested = pos.invested_amount
    if invested is None and pos.avg_price and pos.quantity:
        invested = pos.avg_price * pos.quantity

    if asset.last_price and pos.quantity:
        return asset.last_price * pos.quantity, (invested or 0.0), asset.price_source or "live"
    if pos.market_value_import is not None:
        return pos.market_value_import, (invested or 0.0), "import"
    if invested is not None:
        return invested, invested, "cost"
    return 0.0, 0.0, "none"


def portfolio_view(session: Session) -> dict:
    rows = session.exec(select(Position, Asset).join(Asset, Position.asset_id == Asset.id)).all()
    holdings = []
    total_value = total_invested = 0.0
    by_kind: dict[str, float] = {}
    by_sector: dict[str, float] = {}

    for pos, asset in rows:
        value, invested, src = _position_value(asset, pos)
        pnl = value - invested if invested else 0.0
        pnl_pct = (pnl / invested * 100) if invested else 0.0
        total_value += value
        total_invested += invested
        kind = asset.kind.value if hasattr(asset.kind, "value") else str(asset.kind)
        by_kind[kind] = by_kind.get(kind, 0.0) + value
        sector = asset.sector or "Sin clasificar"
        by_sector[sector] = by_sector.get(sector, 0.0) + value
        holdings.append({
            "asset_id": asset.id,
            "name": asset.name,
            "symbol": asset.symbol,
            "isin": asset.isin,
            "kind": kind,
            "currency": asset.currency,
            "quantity": pos.quantity,
            "avg_price": pos.avg_price,
            "last_price": asset.last_price,
            "invested": round(invested, 2),
            "market_value": round(value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "price_source": src,
            "last_price_at": asset.last_price_at.isoformat() if asset.last_price_at else None,
            "account": pos.account,
        })

    total_pnl = total_value - total_invested
    for h in holdings:
        h["weight"] = round(h["market_value"] / total_value * 100, 2) if total_value else 0.0

    holdings.sort(key=lambda h: h["market_value"], reverse=True)
    return {
        "holdings": holdings,
        "summary": {
            "total_value": round(total_value, 2),
            "total_invested": round(total_invested, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl / total_invested * 100, 2) if total_invested else 0.0,
            "positions": len(holdings),
            "base_currency": "EUR",
        },
        "allocation": {
            "by_kind": [{"label": k, "value": round(v, 2)} for k, v in sorted(by_kind.items(), key=lambda x: -x[1])],
            "by_sector": [{"label": k, "value": round(v, 2)} for k, v in sorted(by_sector.items(), key=lambda x: -x[1])],
        },
    }


def write_snapshot(session: Session) -> PortfolioSnapshot:
    view = portfolio_view(session)
    s = view["summary"]
    today = date.today()
    existing = session.exec(
        select(PortfolioSnapshot).where(PortfolioSnapshot.snapshot_date == today)
    ).first()
    if existing:
        existing.total_value = s["total_value"]
        existing.total_invested = s["total_invested"]
        existing.total_pnl = s["total_pnl"]
        snap = existing
    else:
        snap = PortfolioSnapshot(
            snapshot_date=today,
            total_value=s["total_value"],
            total_invested=s["total_invested"],
            total_pnl=s["total_pnl"],
        )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap
