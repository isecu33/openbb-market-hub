"""
thesis_energy.py
=================
Flujo de "tesis temática": de una hipótesis macro a una lista corta de
candidatas para analizar en profundidad.

Hipótesis de ejemplo incluida: "la demanda de energía sube por la IA y los
datacenters" -> empresas de generación, transmisión y equipos eléctricos que
podrían beneficiarse.

Uso:
    python src/thesis_energy.py
    python src/thesis_energy.py --sector "Utilities" --min-rev-growth 0.05

Los nombres exactos de algunos endpoints del screener pueden variar según la
versión de OpenBB instalada. Este script intenta varias rutas conocidas y
avisa si ninguna funciona, en vez de fallar en silencio.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

try:
    from openbb import obb
except ImportError:
    print("Falta instalar OpenBB. Ejecuta: pip install -r requirements.txt")
    sys.exit(1)


# Universo de partida para la tesis de energía/datacenters.
# Pensado como ejemplo editable, no como recomendación de inversión.
DEFAULT_UNIVERSE = [
    "NEE", "DUK", "SO", "AEP", "EXC", "CEG", "VST", "NRG",
    "ETN", "EMR", "PWR", "GEV", "ETR",
]


@dataclass
class ThesisCriteria:
    sector: str | None = None
    min_revenue_growth: float | None = None
    max_pe: float | None = None
    universe: list[str] | None = None


def _try_endpoints(endpoint_attempts: list[tuple[str, dict]]):
    """Prueba varias rutas de endpoint hasta que una funcione.

    Cada tupla es (descripcion, kwargs) y el callable se resuelve dentro de
    cada bloque try, porque el nombre exacto del atributo puede no existir
    en todas las versiones.
    """
    last_error = None
    for description, fn, kwargs in endpoint_attempts:
        try:
            return fn(**kwargs), description
        except Exception as e:  # noqa: BLE001 - queremos capturar cualquier fallo de API
            last_error = e
            continue
    raise RuntimeError(
        f"Ninguna ruta de endpoint funcionó. Último error: {last_error}\n"
        "Sugerencia: ejecuta la skill/script 'list_endpoints.py' para explorar "
        "los nombres reales disponibles en tu instalación de OpenBB."
    )


def screen_candidates(criteria: ThesisCriteria) -> list[dict]:
    """Filtra el universo de partida según los criterios de la tesis."""
    universe = criteria.universe or DEFAULT_UNIVERSE
    results = []

    for ticker in universe:
        try:
            profile_attempts = [
                ("equity.profile", lambda **kw: obb.equity.profile(**kw), {"symbol": ticker}),
            ]
            profile, _ = _try_endpoints(profile_attempts)
            profile_df = profile.to_df() if hasattr(profile, "to_df") else profile

            metrics_attempts = [
                ("equity.fundamental.metrics", lambda **kw: obb.equity.fundamental.metrics(**kw),
                 {"symbol": ticker, "period": "annual", "limit": 1}),
            ]
            metrics, _ = _try_endpoints(metrics_attempts)
            metrics_df = metrics.to_df() if hasattr(metrics, "to_df") else metrics

            row = {
                "symbol": ticker,
                "name": _safe_get(profile_df, "name", ticker),
                "sector": _safe_get(profile_df, "sector", None),
                "pe_ratio": _safe_get(metrics_df, "pe_ratio", None),
                "revenue_growth": _safe_get(metrics_df, "revenue_growth", None),
            }

            if criteria.sector and row["sector"] and criteria.sector.lower() not in str(row["sector"]).lower():
                continue
            if criteria.max_pe and row["pe_ratio"] and row["pe_ratio"] > criteria.max_pe:
                continue
            if criteria.min_revenue_growth and row["revenue_growth"] is not None and row["revenue_growth"] < criteria.min_revenue_growth:
                continue

            results.append(row)
        except Exception as e:  # noqa: BLE001
            print(f"  [aviso] No se pudo procesar {ticker}: {e}")
            continue

    return results


def _safe_get(df_or_obj, key: str, default):
    try:
        if hasattr(df_or_obj, "iloc"):
            return df_or_obj.iloc[0].get(key, default)
        if isinstance(df_or_obj, list) and df_or_obj:
            return df_or_obj[0].get(key, default)
        if isinstance(df_or_obj, dict):
            return df_or_obj.get(key, default)
    except Exception:  # noqa: BLE001
        pass
    return default


def print_report(rows: list[dict], hypothesis: str) -> None:
    print(f"\nTesis: {hypothesis}")
    print("=" * 70)
    if not rows:
        print("Ninguna candidata superó los filtros. Prueba a relajar los criterios.")
        return
    for r in rows:
        print(f"- {r['symbol']:<6} {r.get('name', ''):<35} sector={r.get('sector')}"
              f" pe={r.get('pe_ratio')} rev_growth={r.get('revenue_growth')}")
    print("\nRecuerda: esto es un filtro de partida, no una recomendación. "
          "El siguiente paso manual es revisar cada candidata en detalle "
          "(noticias, comparables, riesgos) antes de cualquier decisión.")


def main():
    parser = argparse.ArgumentParser(description="Filtra candidatas a partir de una tesis temática.")
    parser.add_argument("--hypothesis", default="La demanda de energía sube por la IA y los datacenters")
    parser.add_argument("--sector", default=None)
    parser.add_argument("--min-rev-growth", type=float, default=None)
    parser.add_argument("--max-pe", type=float, default=None)
    args = parser.parse_args()

    criteria = ThesisCriteria(
        sector=args.sector,
        min_revenue_growth=args.min_rev_growth,
        max_pe=args.max_pe,
    )

    rows = screen_candidates(criteria)
    print_report(rows, args.hypothesis)


if __name__ == "__main__":
    main()
