"""
backend/routers/alerts.py
=========================
CRUD de alertas, listado de eventos disparados y endpoints de jobs (para
disparar el chequeo a mano o desde una tarea programada externa).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.db import get_session
from backend.models import Alert, AlertEvent, Asset, AlertKind
from backend.services import alerts_engine
from backend.services import portfolio as portfolio_svc

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertIn(BaseModel):
    symbol: str | None = None
    asset_id: int | None = None
    kind: str = "price_above"
    threshold: float | None = None
    note: str | None = None
    active: bool = True


@router.get("")
def list_alerts(session: Session = Depends(get_session)):
    alerts = session.exec(select(Alert).order_by(Alert.created_at.desc())).all()
    out = []
    for a in alerts:
        name = a.symbol
        if a.asset_id:
            asset = session.get(Asset, a.asset_id)
            if asset:
                name = asset.name or asset.symbol or asset.isin
        out.append({
            "id": a.id,
            "kind": a.kind.value if hasattr(a.kind, "value") else a.kind,
            "symbol": a.symbol,
            "asset_id": a.asset_id,
            "label": name,
            "threshold": a.threshold,
            "note": a.note,
            "active": a.active,
            "trigger_count": a.trigger_count,
            "last_triggered_at": a.last_triggered_at.isoformat() if a.last_triggered_at else None,
        })
    return out


@router.post("")
def create_alert(body: AlertIn, session: Session = Depends(get_session)):
    if body.kind not in AlertKind._value2member_map_:
        raise HTTPException(status_code=400, detail=f"Tipo de alerta inválido: {body.kind}")
    alert = Alert(
        symbol=body.symbol.upper() if body.symbol else None,
        asset_id=body.asset_id,
        kind=AlertKind(body.kind),
        threshold=body.threshold,
        note=body.note,
        active=body.active,
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return {"ok": True, "id": alert.id}


@router.patch("/{alert_id}")
def update_alert(alert_id: int, body: AlertIn, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    alert.threshold = body.threshold
    alert.note = body.note
    alert.active = body.active
    if body.kind in AlertKind._value2member_map_:
        alert.kind = AlertKind(body.kind)
    session.add(alert)
    session.commit()
    return {"ok": True}


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    session.delete(alert)
    session.commit()
    return {"ok": True}


@router.get("/events")
def list_events(unread_only: bool = False, limit: int = 50, session: Session = Depends(get_session)):
    stmt = select(AlertEvent).order_by(AlertEvent.triggered_at.desc())
    if unread_only:
        stmt = stmt.where(AlertEvent.read == False)  # noqa: E712
    events = session.exec(stmt).all()[:limit]
    return [
        {"id": e.id, "alert_id": e.alert_id, "message": e.message,
         "triggered_at": e.triggered_at.isoformat(), "read": e.read}
        for e in events
    ]


@router.post("/events/{event_id}/read")
def mark_read(event_id: int, session: Session = Depends(get_session)):
    e = session.get(AlertEvent, event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    e.read = True
    session.add(e)
    session.commit()
    return {"ok": True}


@router.post("/events/read-all")
def mark_all_read(session: Session = Depends(get_session)):
    events = session.exec(select(AlertEvent).where(AlertEvent.read == False)).all()  # noqa: E712
    for e in events:
        e.read = True
        session.add(e)
    session.commit()
    return {"ok": True, "count": len(events)}


@router.post("/check")
def run_check(session: Session = Depends(get_session)):
    """Evalúa todas las alertas ahora. Útil para tareas programadas externas."""
    return alerts_engine.evaluate_all(session)


@router.post("/refresh-prices")
def run_refresh(session: Session = Depends(get_session)):
    res = portfolio_svc.refresh_prices(session)
    portfolio_svc.write_snapshot(session)
    return res
