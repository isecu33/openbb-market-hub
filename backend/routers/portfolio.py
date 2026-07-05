"""
backend/routers/portfolio.py
============================
Endpoints de cartera: vista consolidada, import de MyInvestor, alta/edición
manual de posiciones, watchlist y serie histórica de valor.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.db import get_session
from backend.models import Asset, Position, PortfolioSnapshot, Transaction
from backend.services import portfolio as svc
from backend.services import metrics as metrics_svc
from backend.services import myinvestor_import

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("")
def get_portfolio(session: Session = Depends(get_session)):
    return svc.portfolio_view(session)


@router.get("/history")
def get_history(days: int = 365, session: Session = Depends(get_session)):
    rows = session.exec(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_date)
    ).all()
    return [
        {
            "date": r.snapshot_date.isoformat(),
            "value": r.total_value,
            "invested": r.total_invested,
            "pnl": r.total_pnl,
        }
        for r in rows[-days:]
    ]


# ---- Métricas y exportación -------------------------------------------------

@router.get("/metrics")
def get_metrics(days: int = 365, benchmark: str | None = "SPY",
                session: Session = Depends(get_session)):
    """Métricas de rendimiento/riesgo: retornos, vol, Sharpe, drawdown,
    concentración, divisa, ingresos y comparación con benchmark."""
    return metrics_svc.performance_metrics(session, days=days, benchmark=benchmark)


@router.get("/export/holdings.csv")
def export_holdings(session: Session = Depends(get_session)):
    csv = metrics_svc.holdings_csv(session)
    return PlainTextResponse(csv, media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": "attachment; filename=cartera.csv",
    })


@router.get("/export/transactions.csv")
def export_transactions(session: Session = Depends(get_session)):
    csv = metrics_svc.transactions_csv(session)
    return PlainTextResponse(csv, media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": "attachment; filename=transacciones.csv",
    })


# ---- Import de MyInvestor -------------------------------------------------

@router.post("/import/preview")
async def import_preview(file: UploadFile = File(...)):
    """Analiza el archivo y devuelve lo detectado SIN guardar nada."""
    content = await file.read()
    try:
        parsed = myinvestor_import.parse_file(file.filename, content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {e}") from e
    return parsed


@router.post("/import")
async def import_commit(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Analiza y persiste el archivo en la cartera."""
    content = await file.read()
    try:
        parsed = myinvestor_import.parse_file(file.filename, content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {e}") from e

    if parsed["kind"] == "transactions":
        res = svc.apply_transactions(session, parsed["transactions"], source=f"import:{file.filename}")
    else:
        res = svc.apply_positions(session, parsed["positions"])
    svc.write_snapshot(session)
    return {"kind": parsed["kind"], "result": res, "warnings": parsed.get("warnings", [])}


# ---- Alta/edición manual --------------------------------------------------

class PositionIn(BaseModel):
    name: str | None = None
    symbol: str | None = None
    isin: str | None = None
    kind: str = "equity"
    currency: str = "EUR"
    quantity: float = 0.0
    avg_price: float | None = None
    invested_amount: float | None = None
    account: str = "MyInvestor"
    notes: str | None = None


@router.post("/positions")
def upsert_position(body: PositionIn, session: Session = Depends(get_session)):
    asset = svc.find_or_create_asset(
        session, isin=body.isin, symbol=body.symbol, name=body.name,
        kind=body.kind, currency=body.currency,
    )
    pos = session.exec(select(Position).where(Position.asset_id == asset.id)).first()
    if pos is None:
        pos = Position(asset_id=asset.id)
    pos.quantity = body.quantity
    pos.avg_price = body.avg_price
    pos.invested_amount = body.invested_amount if body.invested_amount is not None else (
        (body.avg_price * body.quantity) if body.avg_price else None
    )
    pos.account = body.account
    pos.notes = body.notes
    session.add(pos)
    session.commit()
    session.refresh(pos)
    return {"ok": True, "position_id": pos.id, "asset_id": asset.id}


@router.delete("/positions/{asset_id}")
def delete_position(asset_id: int, session: Session = Depends(get_session)):
    pos = session.exec(select(Position).where(Position.asset_id == asset_id)).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Posición no encontrada")
    session.delete(pos)
    session.commit()
    return {"ok": True}


@router.get("/transactions")
def list_transactions(session: Session = Depends(get_session)):
    rows = session.exec(select(Transaction, Asset).join(Asset, Transaction.asset_id == Asset.id)
                        .order_by(Transaction.tx_date.desc())).all()
    return [
        {
            "id": tx.id,
            "date": tx.tx_date.isoformat() if tx.tx_date else None,
            "type": tx.tx_type.value if hasattr(tx.tx_type, "value") else tx.tx_type,
            "asset": asset.name or asset.symbol or asset.isin,
            "symbol": asset.symbol,
            "isin": asset.isin,
            "quantity": tx.quantity,
            "price": tx.price,
            "amount": tx.amount,
        }
        for tx, asset in rows
    ]


# ---- Watchlist ------------------------------------------------------------

class WatchIn(BaseModel):
    symbol: str | None = None
    isin: str | None = None
    name: str | None = None
    kind: str = "equity"


@router.get("/watchlist")
def get_watchlist(session: Session = Depends(get_session)):
    assets = session.exec(select(Asset).where(Asset.in_watchlist == True)).all()  # noqa: E712
    out = []
    for a in assets:
        out.append({
            "asset_id": a.id, "symbol": a.symbol, "isin": a.isin, "name": a.name,
            "kind": a.kind.value if hasattr(a.kind, "value") else a.kind,
            "last_price": a.last_price,
        })
    return out


@router.post("/watchlist")
def add_watchlist(body: WatchIn, session: Session = Depends(get_session)):
    asset = svc.find_or_create_asset(session, isin=body.isin, symbol=body.symbol,
                                     name=body.name, kind=body.kind)
    asset.in_watchlist = True
    session.add(asset)
    session.commit()
    return {"ok": True, "asset_id": asset.id}


@router.delete("/watchlist/{asset_id}")
def remove_watchlist(asset_id: int, session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    asset.in_watchlist = False
    session.add(asset)
    session.commit()
    return {"ok": True}
