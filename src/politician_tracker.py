"""
politician_tracker.py
======================
Tracker de operaciones de políticos del Congreso de EE. UU. (Senado + Cámara
de Representantes), usando el módulo Government Trades de OpenBB
(proveedor FMP).

AVISO IMPORTANTE: la STOCK Act permite hasta 45 días de retraso entre la
operación real y su divulgación pública. Estos datos NUNCA son señales en
tiempo real — trátalos como información histórica/contextual, no como
indicador de timing de mercado.

Uso:
    python src/politician_tracker.py
    python src/politician_tracker.py --politician "Nancy Pelosi"
    python src/politician_tracker.py --build-watchlist --min-trades 3
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timedelta

try:
    from openbb import obb
except ImportError:
    print("Falta instalar OpenBB. Ejecuta: pip install -r requirements.txt")
    sys.exit(1)


STOCK_ACT_DISCLOSURE_DELAY_DAYS = 45


def _fetch_government_trades(politician: str | None, days_back: int):
    """Intenta varias rutas conocidas del módulo Government Trades.

    El nombre exacto del endpoint puede cambiar entre versiones de OpenBB
    (p. ej. obb.regulators.sec.* vs un proveedor específico de FMP), así que
    probamos alternativas en orden antes de rendirnos.
    """
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    attempts = []

    if hasattr(obb, "regulators") and hasattr(obb.regulators, "sec"):
        attempts.append(("regulators.sec.htm", lambda: obb.regulators.sec.htm_file()))

    # Ruta más probable en versiones recientes: comando dedicado de government trades.
    if hasattr(obb, "equity") and hasattr(obb.equity, "ownership"):
        attempts.append((
            "equity.ownership.government_trades",
            lambda: obb.equity.ownership.government_trades(
                symbol=None, provider="fmp", start_date=start_date
            ) if politician is None else obb.equity.ownership.government_trades(
                symbol=None, provider="fmp", politician=politician, start_date=start_date
            ),
        ))

    if not attempts:
        raise RuntimeError(
            "No se encontró un endpoint de Government Trades en esta instalación de OpenBB. "
            "Ejecuta la skill 'openbb-query' (list_endpoints.py) para localizar el nombre real, "
            "o revisa `obb.equity.ownership?` / `obb.regulators?` interactivamente."
        )

    last_error = None
    for description, fn in attempts:
        try:
            result = fn()
            return result, description
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue
    raise RuntimeError(f"Ninguna ruta funcionó. Último error: {last_error}")


def build_mirror_watchlist(trades, min_trades: int = 2) -> list[tuple[str, int]]:
    """Cuenta operaciones por ticker y devuelve los más frecuentes."""
    df = trades.to_df() if hasattr(trades, "to_df") else trades
    counter = Counter()

    rows = df.to_dict("records") if hasattr(df, "to_dict") else (df if isinstance(df, list) else [])
    for row in rows:
        symbol = row.get("symbol") or row.get("ticker")
        if symbol:
            counter[symbol] += 1

    return [(sym, n) for sym, n in counter.most_common() if n >= min_trades]


def print_disclosure_warning():
    print(
        f"\n⚠️  Recuerda: la STOCK Act permite hasta {STOCK_ACT_DISCLOSURE_DELAY_DAYS} días "
        "de retraso en la divulgación. La fecha de 'transacción' que ves puede ser muy "
        "anterior a la fecha en que se hizo pública. No uses esto para timing de entrada/salida.\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Tracker de Government Trades del Congreso de EE. UU.")
    parser.add_argument("--politician", default=None, help="Filtrar por nombre, p. ej. 'Nancy Pelosi'")
    parser.add_argument("--days-back", type=int, default=180)
    parser.add_argument("--build-watchlist", action="store_true", help="Construir watchlist espejo por frecuencia")
    parser.add_argument("--min-trades", type=int, default=2)
    args = parser.parse_args()

    print_disclosure_warning()

    try:
        trades, source = _fetch_government_trades(args.politician, args.days_back)
        print(f"Fuente de datos usada: {source}\n")
    except Exception as e:  # noqa: BLE001
        print(f"Error obteniendo los datos: {e}")
        sys.exit(1)

    if args.build_watchlist:
        watchlist = build_mirror_watchlist(trades, args.min_trades)
        print(f"Watchlist espejo (tickers con >= {args.min_trades} operaciones divulgadas):")
        for symbol, count in watchlist:
            print(f"  - {symbol}: {count} operaciones")
        if not watchlist:
            print("  (ninguno supera el umbral; prueba con --min-trades más bajo)")
    else:
        df = trades.to_df() if hasattr(trades, "to_df") else trades
        print(df)


if __name__ == "__main__":
    main()
