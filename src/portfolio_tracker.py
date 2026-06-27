"""
portfolio_tracker.py
=====================
Cartera/watchlist centralizada con noticias y sentimiento.

MyInvestor (u otro bróker sin API pública) no se conecta directamente:
la posición se importa a mano vía CSV exportado del bróker, o se mantiene
como una watchlist simple de tickers en este mismo script/archivo.

Uso:
    python src/portfolio_tracker.py --watchlist AAPL MSFT NVDA
    python src/portfolio_tracker.py --csv mi_cartera.csv

Formato CSV esperado (cabecera flexible, se buscan estas columnas):
    symbol,quantity,avg_price
    AAPL,10,150.20
    MSFT,5,310.00
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field

try:
    from openbb import obb
except ImportError:
    print("Falta instalar OpenBB. Ejecuta: pip install -r requirements.txt")
    sys.exit(1)


@dataclass
class Position:
    symbol: str
    quantity: float | None = None
    avg_price: float | None = None


def load_positions_from_csv(path: str) -> list[Position]:
    positions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get("symbol") or row.get("ticker") or row.get("Symbol")
            if not symbol:
                continue
            positions.append(Position(
                symbol=symbol.strip().upper(),
                quantity=_to_float(row.get("quantity") or row.get("Quantity")),
                avg_price=_to_float(row.get("avg_price") or row.get("Avg Price")),
            ))
    return positions


def _to_float(value) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def fetch_quote_and_news(symbol: str, news_limit: int = 5) -> dict:
    out = {"symbol": symbol, "price": None, "change_pct": None, "news": []}

    try:
        quote = obb.equity.price.quote(symbol=symbol)
        quote_df = quote.to_df() if hasattr(quote, "to_df") else quote
        if hasattr(quote_df, "iloc") and len(quote_df) > 0:
            row = quote_df.iloc[0]
            out["price"] = row.get("last_price") or row.get("close")
            out["change_pct"] = row.get("change_percent")
    except Exception as e:  # noqa: BLE001
        out["price_error"] = str(e)

    try:
        news = obb.news.company(symbol=symbol, limit=news_limit)
        news_df = news.to_df() if hasattr(news, "to_df") else news
        records = news_df.to_dict("records") if hasattr(news_df, "to_dict") else news_df
        for item in records[:news_limit]:
            out["news"].append({
                "title": item.get("title"),
                "date": item.get("date") or item.get("published_date"),
                "source": item.get("source") or item.get("provider"),
            })
    except Exception as e:  # noqa: BLE001
        out["news_error"] = str(e)

    return out


def print_dashboard(positions: list[Position]) -> None:
    print("\nCartera / Watchlist")
    print("=" * 70)
    for pos in positions:
        info = fetch_quote_and_news(pos.symbol)
        line = f"{pos.symbol:<6} precio={info['price']}"
        if pos.quantity is not None:
            line += f"  cantidad={pos.quantity}"
        if pos.avg_price is not None:
            line += f"  precio_medio={pos.avg_price}"
        print(line)
        if info.get("news"):
            for n in info["news"]:
                print(f"    · [{n.get('date')}] {n.get('title')} ({n.get('source')})")
        elif info.get("news_error"):
            print(f"    (sin noticias: {info['news_error']})")
        print()


def main():
    parser = argparse.ArgumentParser(description="Cartera/watchlist centralizada con noticias.")
    parser.add_argument("--csv", default=None, help="Ruta a un CSV exportado del bróker")
    parser.add_argument("--watchlist", nargs="*", default=None, help="Lista de tickers, p. ej. AAPL MSFT")
    parser.add_argument("--news-limit", type=int, default=5)
    args = parser.parse_args()

    if args.csv:
        positions = load_positions_from_csv(args.csv)
    elif args.watchlist:
        positions = [Position(symbol=s.upper()) for s in args.watchlist]
    else:
        print("Indica --csv ruta.csv o --watchlist TICKER1 TICKER2 ...")
        sys.exit(1)

    if not positions:
        print("No se encontraron posiciones/tickers válidos.")
        sys.exit(1)

    print_dashboard(positions)


if __name__ == "__main__":
    main()
