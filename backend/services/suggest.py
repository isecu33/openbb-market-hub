"""
backend/services/suggest.py
===========================
Generador de sugerencias de inversión (diarias/semanales). Dos capas:

1. **Señales cuantitativas** (siempre): para cada símbolo del universo
   (cartera + watchlist + ETFs de índices/sectores) se calculan tendencia
   (precio vs SMA50/SMA200), momentum (retorno 1m/3m), distancia al máximo de
   52 semanas y volatilidad. De ahí sale un score 0-100 y un ranking.
2. **Briefing redactado por Claude** (opcional): si hay ANTHROPIC_API_KEY en
   .env, se le pasan las señales + noticias importantes recientes y redacta un
   briefing corto en español. Sin clave, se genera un resumen basado en reglas.

IMPORTANTE: esto es research personal, NO asesoramiento financiero. El
disclaimer viaja siempre en el payload y la web lo muestra.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta

from sqlmodel import Session, select

from backend.config import ANTHROPIC_API_KEY
from backend.models import Asset, NewsItem, Position, Suggestion
from backend.services import openbb_client

DISCLAIMER = (
    "Generado automáticamente a partir de señales cuantitativas y noticias. "
    "NO es asesoramiento financiero: úsalo como punto de partida de tu propio análisis."
)

# Universo base: índices y sectores (ETFs líquidos de EE. UU.). Se suma la
# cartera y la watchlist del usuario.
BASE_UNIVERSE = {
    "SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones", "IWM": "Russell 2000",
    "EFA": "Desarrollados ex-US", "EEM": "Emergentes", "GLD": "Oro", "TLT": "Bonos largos US",
    "XLE": "Energía", "XLK": "Tecnología", "XLV": "Salud", "XLF": "Financiero",
    "XLI": "Industrial", "XLU": "Utilities",
}


# ---------------------------------------------------------------------------
# Señales cuantitativas
# ---------------------------------------------------------------------------

def compute_signal(symbol: str, label: str | None = None) -> dict | None:
    hist = openbb_client.historical(symbol, days=420)
    closes = [h["close"] for h in hist if h.get("close")]
    if len(closes) < 60:
        return None
    last = closes[-1]
    sma50 = sum(closes[-50:]) / 50
    sma200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
    ret_1m = (last / closes[-21] - 1) * 100 if len(closes) > 21 else None
    ret_3m = (last / closes[-63] - 1) * 100 if len(closes) > 63 else None
    high_52w = max(closes[-252:]) if len(closes) >= 252 else max(closes)
    from_high = (last / high_52w - 1) * 100

    daily = [(a / b - 1) for a, b in zip(closes[-64:][1:], closes[-64:])]
    vol = None
    if len(daily) > 10:
        mean = sum(daily) / len(daily)
        vol = math.sqrt(sum((r - mean) ** 2 for r in daily) / (len(daily) - 1)) * math.sqrt(252) * 100

    # Score 0-100: tendencia (hasta 45) + momentum 3m (hasta 30) + cercanía a máximos (hasta 25).
    score = 0.0
    score += 15 if last > sma50 else 0
    if sma200:
        score += 15 if last > sma200 else 0
        score += 15 if sma50 > sma200 else 0
    else:
        score += 15 if last > sum(closes[-min(len(closes), 120):]) / min(len(closes), 120) else 0
    if ret_3m is not None:
        score += max(-0.0, min(30.0, 15 + ret_3m))          # -15% -> 0, 0% -> 15, +15% -> 30
    score += max(0.0, 25 + from_high * 25 / 20)              # en máximos -> 25, -20% -> 0

    return {
        "symbol": symbol,
        "label": label or symbol,
        "last_price": round(last, 2),
        "sma50": round(sma50, 2),
        "sma200": round(sma200, 2) if sma200 else None,
        "trend": "alcista" if (last > sma50 and (not sma200 or sma50 > sma200)) else
                 ("bajista" if (last < sma50 and (not sma200 or sma50 < sma200)) else "mixta"),
        "ret_1m_pct": round(ret_1m, 2) if ret_1m is not None else None,
        "ret_3m_pct": round(ret_3m, 2) if ret_3m is not None else None,
        "from_52w_high_pct": round(from_high, 2),
        "annualized_vol_pct": round(vol, 2) if vol is not None else None,
        "score": round(max(0.0, min(100.0, score)), 1),
    }


def _universe(session: Session) -> dict[str, str]:
    uni = dict(BASE_UNIVERSE)
    for a in session.exec(select(Asset).where(Asset.symbol.is_not(None))).all():
        has_pos = session.exec(select(Position).where(Position.asset_id == a.id)).first()
        if has_pos or a.in_watchlist:
            uni.setdefault(a.symbol, a.name or a.symbol)
    return uni


def _recent_important_news(session: Session, days: int = 7, min_importance: int = 40) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = session.exec(
        select(NewsItem)
        .where(NewsItem.importance >= min_importance, NewsItem.created_at >= datetime.utcnow() - timedelta(days=days))
        .order_by(NewsItem.importance.desc())
        .limit(15)
    ).all()
    return [
        {"symbol": n.symbol, "title": n.title, "category": n.category,
         "sentiment": n.sentiment_label, "importance": n.importance, "date": n.published_at or cutoff}
        for n in rows
    ]


# ---------------------------------------------------------------------------
# Briefing (Claude opcional, reglas si no)
# ---------------------------------------------------------------------------

def _claude_briefing(period: str, signals: list[dict], news: list[dict]) -> str | None:
    """Redacta el briefing con la API de Anthropic. Devuelve None si no se puede."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        horizon = "diario" if period == "daily" else "semanal"
        payload = json.dumps({"señales": signals, "noticias_importantes": news},
                             ensure_ascii=False, sort_keys=True)
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4000,
            thinking={"type": "adaptive"},
            system=(
                "Eres un analista de mercados escribiendo un briefing " + horizon + " en español "
                "para un inversor particular de perfil largo plazo. Recibes señales cuantitativas "
                "(tendencia, momentum, score 0-100) y noticias relevantes. Escribe un briefing corto "
                "(200-300 palabras): 1) pulso general del mercado según los índices; 2) 2-4 ideas "
                "concretas a vigilar con su razón (señal + noticia si la hay); 3) riesgos visibles. "
                "Sé específico con los símbolos y cifras que recibes; no inventes datos. Nunca des "
                "órdenes de compra/venta: presenta hechos y señales. Sin preámbulos ni despedidas."
            ),
            messages=[{"role": "user", "content": payload}],
        )
        if response.stop_reason == "refusal":
            return None
        return next((b.text for b in response.content if b.type == "text"), None)
    except Exception:  # noqa: BLE001 - la sugerencia debe generarse aunque Claude falle
        return None


def _rules_briefing(period: str, index_signals: list[dict], top: list[dict]) -> str:
    horizon = "diario" if period == "daily" else "semanal"
    up = [s for s in index_signals if s["trend"] == "alcista"]
    down = [s for s in index_signals if s["trend"] == "bajista"]
    lines = [f"Briefing {horizon} (motor de reglas, sin IA):"]
    lines.append(
        f"Pulso de mercado: {len(up)} de {len(index_signals)} índices/sectores en tendencia alcista"
        + (f"; débiles: {', '.join(s['symbol'] for s in down[:4])}." if down else ".")
    )
    if top:
        ideas = "; ".join(
            f"{s['symbol']} (score {s['score']}, {s['ret_3m_pct']:+.1f}% en 3m)"
            for s in top[:4] if s.get("ret_3m_pct") is not None
        )
        lines.append(f"Mejores señales del universo seguido: {ideas}.")
    lines.append("Añade ANTHROPIC_API_KEY en .env para recibir un briefing redactado con análisis de contexto.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generación y consulta
# ---------------------------------------------------------------------------

def generate(session: Session, period: str = "daily") -> dict:
    uni = _universe(session)
    signals = []
    for sym, label in uni.items():
        try:
            s = compute_signal(sym, label)
        except Exception:  # noqa: BLE001
            s = None
        if s:
            s["in_base_universe"] = sym in BASE_UNIVERSE
            signals.append(s)

    signals.sort(key=lambda s: s["score"], reverse=True)
    index_signals = [s for s in signals if s["in_base_universe"]]
    news = _recent_important_news(session)

    briefing = _claude_briefing(period, signals[:20], news)
    engine = "claude" if briefing else "rules"
    if not briefing:
        briefing = _rules_briefing(period, index_signals, signals)

    payload = {
        "period": period,
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": DISCLAIMER,
        "briefing": briefing,
        "top_signals": signals[:8],
        "bottom_signals": sorted(signals, key=lambda s: s["score"])[:4],
        "index_signals": index_signals,
        "important_news": news,
    }
    row = Suggestion(period=period, payload=json.dumps(payload, ensure_ascii=False), engine=engine)
    session.add(row)
    session.commit()
    payload["engine"] = engine
    return payload


def latest(session: Session, period: str = "daily") -> dict | None:
    row = session.exec(
        select(Suggestion).where(Suggestion.period == period)
        .order_by(Suggestion.generated_at.desc())
    ).first()
    if not row:
        return None
    out = json.loads(row.payload)
    out["engine"] = row.engine
    return out
