"""
backend/services/metrics.py
===========================
Métricas de rendimiento y riesgo de la cartera, calculadas a partir de:

  - `PortfolioSnapshot` (serie diaria de valor/invertido) -> retornos, volatilidad,
    Sharpe, máximo drawdown, mejor/peor día. Los retornos diarios se ajustan por
    flujos (aportaciones/retiradas) usando la variación de `total_invested`, una
    aproximación al TWR suficiente para una cartera personal.
  - La vista consolidada de cartera -> concentración (peso máximo, top-5, HHI)
    y exposición por divisa.
  - `Transaction` -> totales de compras/ventas/dividendos/comisiones e ingresos
    por año.
  - OpenBB (opcional) -> comparación con un índice de referencia (benchmark).

Todo devuelve dicts serializables y nunca lanza: si falta histórico se indica
en `caveats` en lugar de romper la página.
"""

from __future__ import annotations

import math
from collections import defaultdict

from sqlmodel import Session, select

from backend.models import PortfolioSnapshot, Transaction, TxType
from backend.services import openbb_client
from backend.services import portfolio as portfolio_svc

TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# Retornos y riesgo a partir de snapshots
# ---------------------------------------------------------------------------

def _flow_adjusted_returns(snaps: list[PortfolioSnapshot]) -> list[dict]:
    """Retorno diario descontando flujos: r = (ΔV - Δinvertido) / V_prev."""
    out = []
    for prev, cur in zip(snaps, snaps[1:]):
        if not prev.total_value:
            continue
        flow = (cur.total_invested or 0.0) - (prev.total_invested or 0.0)
        r = (cur.total_value - prev.total_value - flow) / prev.total_value
        out.append({"date": cur.snapshot_date.isoformat(), "r": r})
    return out


def _risk_stats(returns: list[dict]) -> dict:
    if len(returns) < 2:
        return {}
    rs = [x["r"] for x in returns]
    n = len(rs)
    mean = sum(rs) / n
    var = sum((r - mean) ** 2 for r in rs) / (n - 1)
    std = math.sqrt(var)
    cumulative = 1.0
    for r in rs:
        cumulative *= (1 + r)

    # Curva acumulada y drawdown.
    curve, acc = [], 1.0
    for x in returns:
        acc *= (1 + x["r"])
        curve.append({"date": x["date"], "level": acc})
    peak, max_dd, dd_series = 0.0, 0.0, []
    for pt in curve:
        peak = max(peak, pt["level"])
        dd = pt["level"] / peak - 1 if peak else 0.0
        max_dd = min(max_dd, dd)
        dd_series.append({"date": pt["date"], "dd_pct": round(dd * 100, 2)})

    best = max(returns, key=lambda x: x["r"])
    worst = min(returns, key=lambda x: x["r"])
    return {
        "days_observed": n,
        "cumulative_pct": round((cumulative - 1) * 100, 2),
        "annualized_vol_pct": round(std * math.sqrt(TRADING_DAYS) * 100, 2),
        "sharpe": round(mean / std * math.sqrt(TRADING_DAYS), 2) if std else None,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "best_day": {"date": best["date"], "pct": round(best["r"] * 100, 2)},
        "worst_day": {"date": worst["date"], "pct": round(worst["r"] * 100, 2)},
        "drawdown_series": dd_series,
    }


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def _benchmark_comparison(snaps: list[PortfolioSnapshot], symbol: str, returns: list[dict]) -> dict:
    """Serie normalizada (base 100) de cartera vs índice sobre las mismas fechas."""
    if len(snaps) < 2:
        return {"symbol": symbol, "series": []}
    days_span = (snaps[-1].snapshot_date - snaps[0].snapshot_date).days + 7
    hist = openbb_client.historical(symbol, days=days_span)
    closes = {h["date"]: h["close"] for h in hist if h.get("date") and h.get("close")}
    if not closes:
        return {"symbol": symbol, "series": [], "error": "sin datos del benchmark"}

    # Cartera en base 100 (retornos ajustados por flujos).
    port_level, series = 100.0, []
    port_by_date = {snaps[0].snapshot_date.isoformat(): 100.0}
    for x in returns:
        port_level *= (1 + x["r"])
        port_by_date[x["date"]] = port_level

    bench_base = None
    last_close = None
    for d, level in port_by_date.items():
        close = closes.get(d, last_close)  # festivos: arrastra el último cierre
        if close is None:
            continue
        last_close = close
        if bench_base is None:
            bench_base = close
        series.append({
            "date": d,
            "portfolio": round(level, 2),
            "benchmark": round(close / bench_base * 100, 2),
        })
    out = {"symbol": symbol, "series": series}
    if series:
        out["portfolio_cumulative_pct"] = round(series[-1]["portfolio"] - 100, 2)
        out["benchmark_cumulative_pct"] = round(series[-1]["benchmark"] - 100, 2)
    return out


# ---------------------------------------------------------------------------
# Concentración y divisa
# ---------------------------------------------------------------------------

def _concentration(view: dict) -> dict:
    holdings = view.get("holdings", [])
    total = view["summary"]["total_value"] or 0.0
    if not holdings or not total:
        return {"positions": len(holdings)}
    weights = sorted((h["market_value"] / total for h in holdings), reverse=True)
    hhi = sum(w * w for w in weights)
    top = holdings[0]
    return {
        "positions": len(holdings),
        "top_holding": top.get("symbol") or top.get("name"),
        "top_weight_pct": round(weights[0] * 100, 2),
        "top5_weight_pct": round(sum(weights[:5]) * 100, 2),
        "hhi": round(hhi, 4),
        "effective_positions": round(1 / hhi, 1) if hhi else None,
    }


def _by_currency(view: dict) -> list[dict]:
    total = view["summary"]["total_value"] or 0.0
    acc: dict[str, float] = defaultdict(float)
    for h in view.get("holdings", []):
        acc[h.get("currency") or "?"] += h["market_value"]
    return [
        {"label": cur, "value": round(v, 2), "weight_pct": round(v / total * 100, 2) if total else 0.0}
        for cur, v in sorted(acc.items(), key=lambda x: -x[1])
    ]


# ---------------------------------------------------------------------------
# Ingresos / flujos desde transacciones
# ---------------------------------------------------------------------------

def _income_summary(session: Session) -> dict:
    txs = session.exec(select(Transaction)).all()
    totals = {t.value: 0.0 for t in TxType}
    by_year: dict[int, dict[str, float]] = defaultdict(lambda: {"dividends": 0.0, "buys": 0.0, "sells": 0.0, "fees": 0.0})
    for tx in txs:
        amount = abs(tx.amount) if tx.amount is not None else (
            abs((tx.price or 0.0) * (tx.quantity or 0.0)) or 0.0
        )
        kind = tx.tx_type.value if hasattr(tx.tx_type, "value") else str(tx.tx_type)
        totals[kind] = totals.get(kind, 0.0) + amount
        fees = tx.fees or 0.0
        if fees:
            totals["fee"] = totals.get("fee", 0.0) + fees
        if tx.tx_date:
            y = by_year[tx.tx_date.year]
            if kind == "dividend":
                y["dividends"] += amount
            elif kind == "buy":
                y["buys"] += amount
            elif kind == "sell":
                y["sells"] += amount
            if fees or kind == "fee":
                y["fees"] += fees or amount
    return {
        "transactions": len(txs),
        "buys_total": round(totals.get("buy", 0.0), 2),
        "sells_total": round(totals.get("sell", 0.0), 2),
        "dividends_total": round(totals.get("dividend", 0.0), 2),
        "fees_total": round(totals.get("fee", 0.0), 2),
        "by_year": [
            {"year": y, **{k: round(v, 2) for k, v in d.items()}}
            for y, d in sorted(by_year.items())
        ],
    }


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def performance_metrics(session: Session, days: int = 365, benchmark: str | None = "SPY") -> dict:
    snaps = session.exec(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_date)
    ).all()[-max(days, 2):]

    view = portfolio_svc.portfolio_view(session)
    returns = _flow_adjusted_returns(snaps)
    risk = _risk_stats(returns)

    caveats = []
    if len(snaps) < 2:
        caveats.append("Aún no hay suficientes snapshots diarios para calcular retornos: "
                       "deja el backend arrancado unos días o pulsa 'Actualizar' a diario.")
    elif len(snaps) < 30:
        caveats.append(f"Métricas calculadas con solo {len(snaps)} días de histórico; "
                       "volatilidad y Sharpe serán poco fiables hasta ~30 días.")
    if any(h["price_source"] in ("import", "cost") for h in view.get("holdings", [])):
        caveats.append("Parte de la cartera se valora con datos importados del bróker "
                       "(fondos sin cotización en vivo): las métricas diarias los recogen "
                       "solo cuando reimportas.")

    out = {
        "period_days": days,
        "summary": view["summary"],
        "returns": risk,
        "concentration": _concentration(view),
        "by_currency": _by_currency(view),
        "income": _income_summary(session),
        "caveats": caveats,
    }
    if benchmark:
        out["benchmark"] = _benchmark_comparison(snaps, benchmark.upper(), returns)
    return out


# ---------------------------------------------------------------------------
# Exportación CSV
# ---------------------------------------------------------------------------

def holdings_csv(session: Session) -> str:
    view = portfolio_svc.portfolio_view(session)
    cols = ["name", "symbol", "isin", "kind", "currency", "quantity", "avg_price",
            "last_price", "invested", "market_value", "pnl", "pnl_pct", "weight",
            "price_source", "account"]
    lines = [";".join(cols)]
    for h in view["holdings"]:
        lines.append(";".join(_csv_cell(h.get(c)) for c in cols))
    return "\n".join(lines) + "\n"


def transactions_csv(session: Session) -> str:
    from backend.models import Asset
    rows = session.exec(
        select(Transaction, Asset).join(Asset, Transaction.asset_id == Asset.id)
        .order_by(Transaction.tx_date)
    ).all()
    cols = ["date", "type", "asset", "symbol", "isin", "quantity", "price", "amount", "fees", "account"]
    lines = [";".join(cols)]
    for tx, asset in rows:
        lines.append(";".join(_csv_cell(v) for v in [
            tx.tx_date.isoformat() if tx.tx_date else None,
            tx.tx_type.value if hasattr(tx.tx_type, "value") else tx.tx_type,
            asset.name, asset.symbol, asset.isin,
            tx.quantity, tx.price, tx.amount, tx.fees, tx.account,
        ]))
    return "\n".join(lines) + "\n"


def _csv_cell(v) -> str:
    """CSV con ';' (Excel es-ES) y coma decimal para abrir directo en Excel."""
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".").replace(".", ",")
    s = str(v)
    if ";" in s or '"' in s or "\n" in s:
        s = '"' + s.replace('"', '""') + '"'
    return s
