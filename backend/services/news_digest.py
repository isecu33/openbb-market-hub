"""
backend/services/news_digest.py
================================
Resumen diario agregado de las noticias importantes recientes del feed
persistido. Dos motores, igual que en `suggest.py`:

1. **Gemini** (opcional): si hay GEMINI_API_KEY en .env, redacta un resumen
   corto en español de lo más relevante.
2. **Reglas**: sin clave (o si Gemini falla), un resumen basado en recuentos
   por categoría/sentimiento.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlmodel import Session, select

from backend.config import GEMINI_API_KEY
from backend.models import NewsDigest, NewsItem

GEMINI_MODEL = "gemini-2.5-flash"


def _recent_important(session: Session, hours: int = 36, min_importance: int = 40) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    rows = session.exec(
        select(NewsItem)
        .where(NewsItem.importance >= min_importance, NewsItem.created_at >= cutoff)
        .order_by(NewsItem.importance.desc())
        .limit(20)
    ).all()
    return [
        {"symbol": n.symbol, "title": n.title, "category": n.category,
         "sentiment": n.sentiment_label, "importance": n.importance, "date": n.published_at}
        for n in rows
    ]


def _gemini_summary(news: list[dict]) -> str | None:
    """Redacta el resumen con la API de Gemini. Devuelve None si no se puede."""
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        payload = json.dumps({"noticias_importantes": news}, ensure_ascii=False, sort_keys=True)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=payload,
            config=types.GenerateContentConfig(
                max_output_tokens=1500,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                system_instruction=(
                    "Eres un analista redactando en español un resumen corto (120-180 palabras) "
                    "de las noticias financieras más relevantes de las últimas horas para un "
                    "inversor particular. Agrupa por tema cuando tenga sentido, sé específico con "
                    "símbolos y cifras, no inventes datos y no des recomendaciones de compra/venta: "
                    "solo describe qué ha pasado y por qué es relevante. Sin preámbulos ni despedidas."
                ),
            ),
        )
        return response.text or None
    except Exception:  # noqa: BLE001 - el resumen debe generarse aunque Gemini falle
        return None


def _rules_summary(news: list[dict]) -> str:
    if not news:
        return "Sin noticias relevantes recientes (motor de reglas, sin IA)."
    by_category: dict[str, int] = {}
    pos = neg = 0
    for n in news:
        if n["category"]:
            by_category[n["category"]] = by_category.get(n["category"], 0) + 1
        if n["sentiment"] == "positive":
            pos += 1
        elif n["sentiment"] == "negative":
            neg += 1
    cats = ", ".join(f"{k} ({v})" for k, v in sorted(by_category.items(), key=lambda kv: -kv[1]))
    lines = [f"Resumen de noticias (motor de reglas, sin IA): {len(news)} noticias relevantes."]
    if cats:
        lines.append(f"Por categoría: {cats}.")
    lines.append(f"Tono: {pos} positivas, {neg} negativas, {len(news) - pos - neg} neutras.")
    top3 = ", ".join(n["title"] for n in news[:3])
    if top3:
        lines.append(f"Destacan: {top3}.")
    lines.append("Añade GEMINI_API_KEY en .env para recibir un resumen redactado con contexto.")
    return "\n".join(lines)


def generate(session: Session) -> dict:
    news = _recent_important(session)
    summary = _gemini_summary(news)
    engine = "gemini" if summary else "rules"
    if not summary:
        summary = _rules_summary(news)

    row = NewsDigest(summary=summary, engine=engine, based_on=len(news))
    session.add(row)
    session.commit()
    session.refresh(row)
    return {
        "generated_at": row.generated_at.isoformat(),
        "summary": row.summary,
        "engine": row.engine,
        "based_on": row.based_on,
    }


def latest(session: Session) -> dict | None:
    row = session.exec(select(NewsDigest).order_by(NewsDigest.generated_at.desc())).first()
    if not row:
        return None
    return {
        "generated_at": row.generated_at.isoformat(),
        "summary": row.summary,
        "engine": row.engine,
        "based_on": row.based_on,
    }
