"""
backend/services/sentiment.py
=============================
Análisis de sentimiento ligero basado en léxico (sin dependencias extra ni
llamadas externas). No pretende ser un modelo NLP serio: da una señal rápida
(positivo / neutro / negativo) sobre titulares de noticias financieras, en
inglés y español, suficiente para colorear el feed y alimentar alertas.
"""

from __future__ import annotations

import re

POSITIVE = {
    # EN
    "beat", "beats", "surge", "surges", "soar", "soars", "rally", "rallies",
    "gain", "gains", "jump", "jumps", "rise", "rises", "record", "growth",
    "profit", "profits", "upgrade", "upgraded", "outperform", "strong", "bullish",
    "boost", "boosts", "wins", "win", "approval", "approved", "expansion", "raises",
    "tops", "high", "higher", "rebound", "optimistic", "buyback", "dividend",
    # ES
    "sube", "suben", "dispara", "récord", "beneficio", "beneficios", "crece",
    "crecimiento", "máximos", "alza", "fuerte", "mejora", "supera", "ganancias",
    "aprobado", "expansión", "rebote", "optimista", "repunte",
}

NEGATIVE = {
    # EN
    "miss", "misses", "plunge", "plunges", "drop", "drops", "fall", "falls",
    "slump", "slumps", "loss", "losses", "downgrade", "downgraded", "weak",
    "bearish", "warning", "warns", "cut", "cuts", "lawsuit", "probe", "fraud",
    "decline", "declines", "slide", "slides", "tumble", "tumbles", "fears",
    "recall", "bankruptcy", "default", "selloff", "low", "lower", "crash",
    # ES
    "cae", "caen", "desploma", "desplome", "pérdida", "pérdidas", "baja",
    "débil", "recorte", "recortes", "demanda judicial", "fraude", "alerta",
    "mínimos", "hundimiento", "quiebra", "temores", "advierte", "retroceso",
}

_WORD_RE = re.compile(r"[a-záéíóúñü]+", re.IGNORECASE)


def score_text(text: str | None) -> dict:
    """Devuelve {label, score} con score en [-1, 1]."""
    if not text:
        return {"label": "neutral", "score": 0.0}
    words = [w.lower() for w in _WORD_RE.findall(text)]
    pos = sum(1 for w in words if w in POSITIVE)
    neg = sum(1 for w in words if w in NEGATIVE)
    total = pos + neg
    if total == 0:
        return {"label": "neutral", "score": 0.0}
    score = round((pos - neg) / total, 3)
    if score > 0.15:
        label = "positive"
    elif score < -0.15:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "score": score}


def annotate(items: list[dict], field: str = "title") -> list[dict]:
    """Añade sentimiento a una lista de noticias in-place."""
    for it in items:
        base = it.get(field) or ""
        extra = it.get("summary") or ""
        it["sentiment"] = score_text(f"{base}. {extra}")
    return items


# ---------------------------------------------------------------------------
# Importancia: ¿merece esta noticia atención de inversión?
# Heurística por eventos (EN/ES): cada categoría tiene un peso base; el
# sentimiento fuerte añade un plus. Escala 0-100.
# ---------------------------------------------------------------------------

EVENT_CATEGORIES: dict[str, tuple[int, tuple[str, ...]]] = {
    "m&a": (45, ("merger", "acquisition", "acquire", "takeover", "buyout",
                 "fusión", "adquisición", "opa ", "compra de")),
    "resultados": (40, ("earnings", "quarterly results", "guidance", "outlook",
                        "forecast", "revenue beat", "profit warning",
                        "resultados trimestrales", "previsiones", "beneficio neto")),
    "regulación": (40, ("lawsuit", "antitrust", "investigation", "probe", "fine",
                        "fda", "approval", "recall", "sec ", "ban ",
                        "demanda", "multa", "investigación", "regulador", "aprobación")),
    "dirección": (30, ("ceo", "cfo", "resigns", "steps down", "appoints", "named chief",
                       "dimite", "nombra", "consejero delegado")),
    "analistas": (25, ("upgrade", "downgrade", "price target", "rating", "initiates coverage",
                       "overweight", "underweight", "precio objetivo", "recomendación")),
    "capital": (25, ("dividend", "buyback", "stock split", "share repurchase", "spin-off",
                     "dividendo", "recompra", "ampliación de capital")),
    "macro": (20, ("fed ", "ecb", "interest rate", "inflation", "cpi", "gdp", "recession",
                   "bce", "tipos de interés", "inflación", "pib", "recesión")),
}


def classify_event(text: str | None) -> tuple[str | None, int]:
    """Devuelve (categoría, peso_base) del evento más fuerte detectado."""
    if not text:
        return None, 0
    t = f" {text.lower()} "
    best: tuple[str | None, int] = (None, 0)
    for category, (weight, keywords) in EVENT_CATEGORIES.items():
        if weight > best[1] and any(kw in t for kw in keywords):
            best = (category, weight)
    return best


def importance(text: str | None, sentiment_score: float = 0.0) -> tuple[int, str | None]:
    """Puntuación 0-100 de relevancia inversora + categoría detectada."""
    category, base = classify_event(text)
    score = base + round(abs(sentiment_score) * 30)
    if category and abs(sentiment_score) > 0.5:
        score += 10  # evento identificado + sentimiento fuerte = señal clara
    return min(score, 100), category
