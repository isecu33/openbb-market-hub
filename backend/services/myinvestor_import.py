"""
backend/services/myinvestor_import.py
=====================================
Importador flexible de exportaciones de MyInvestor (y, en general, de cualquier
bróker que exporte CSV/Excel).

MyInvestor no tiene API pública, pero permite exportar tu cartera y tus
movimientos. El problema: las cabeceras varían (español, con tildes, formato
de número europeo "1.234,56") y puede tratarse de:

  - una **cartera de fondos** (ISIN, participaciones, valor liquidativo,
    importe invertido, valor actual), o
  - una **cartera de acciones/ETF** (ticker, cantidad, precio medio), o
  - un export de **movimientos** (fecha, tipo, producto, importe).

Este módulo detecta el tipo de fichero por sus columnas y normaliza todo a una
estructura común. No asume un layout fijo: hace *fuzzy matching* de cabeceras,
de modo que si MyInvestor cambia ligeramente el formato, sigue funcionando.
"""

from __future__ import annotations

import io
import unicodedata
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Normalización de cabeceras y números
# ---------------------------------------------------------------------------

def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _norm(s) -> str:
    return _strip_accents(str(s)).strip().lower().replace("\n", " ")


# Candidatos de cabecera por campo lógico (orden = prioridad).
COLUMN_MAP = {
    "name": ["nombre", "fondo", "producto", "denominacion", "descripcion", "activo", "valor", "name", "security"],
    "isin": ["isin", "codigo isin", "code isin", "identificador"],
    "symbol": ["ticker", "simbolo", "symbol", "codigo", "epic"],
    "quantity": ["participaciones", "n participaciones", "num participaciones", "titulos", "n titulos",
                 "cantidad", "acciones", "units", "shares", "quantity", "qty", "nominal"],
    "nav": ["valor liquidativo", "vl", "v.l.", "nav", "precio", "cotizacion", "precio actual"],
    "avg_price": ["precio medio", "precio de compra", "precio compra", "coste medio", "pmp", "avg price", "cost"],
    "invested": ["importe invertido", "inversion", "aportado", "aportacion", "importe", "coste", "invertido",
                 "capital invertido", "total invertido", "invested", "cost basis"],
    "market_value": ["valor actual", "valor de mercado", "valoracion", "valor mercado", "valor posicion",
                     "market value", "valuation", "valor"],
    "currency": ["divisa", "moneda", "currency", "ccy"],
    "date": ["fecha", "fecha operacion", "fecha valor", "date", "trade date"],
    "tx_type": ["tipo", "tipo operacion", "operacion", "movimiento", "concepto", "type", "side"],
}

# Para distinguir un export de movimientos de uno de posiciones.
TX_TYPE_BUY = {"compra", "suscripcion", "suscripción", "aportacion", "aportación", "buy", "subscription", "traspaso entrada"}
TX_TYPE_SELL = {"venta", "reembolso", "buy", "sell", "redemption", "traspaso salida"}
TX_TYPE_DIV = {"dividendo", "dividend", "cupon", "cupón", "reparto"}


def _parse_number(value) -> float | None:
    """Convierte '1.234,56', '1,234.56', '€ 1.200', etc. a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:  # noqa: BLE001
            return None
    s = str(value).strip()
    if not s or s.lower() in {"nan", "-", "n/a"}:
        return None
    # Quitar símbolos de divisa y espacios.
    s = s.replace("€", "").replace("$", "").replace("%", "").replace("\xa0", "").replace(" ", "")
    has_comma = "," in s
    has_dot = "." in s
    if has_comma and has_dot:
        # El último separador que aparece es el decimal.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")     # europeo: 1.234,56
        else:
            s = s.replace(",", "")                        # anglosajón: 1,234.56
    elif has_comma:
        s = s.replace(",", ".")                           # 1234,56 -> 1234.56
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(value):
    if value is None or str(value).strip() in {"", "nan"}:
        return None
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.date()
    s = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Lectura del fichero
# ---------------------------------------------------------------------------

def _read_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        return pd.read_excel(io.BytesIO(content), dtype=str)
    # CSV: detectar separador (MyInvestor suele usar ';').
    text = content.decode("utf-8-sig", errors="replace")
    sep = ";" if text.count(";") >= text.count(",") else ","
    return pd.read_csv(io.StringIO(text), sep=sep, dtype=str)


def _build_header_index(columns) -> dict[str, str]:
    """Mapea campo lógico -> nombre de columna real del fichero."""
    normalized = {col: _norm(col) for col in columns}
    resolved: dict[str, str] = {}
    for field, candidates in COLUMN_MAP.items():
        for cand in candidates:
            for real, norm in normalized.items():
                if norm == cand:
                    resolved[field] = real
                    break
            if field in resolved:
                break
        if field in resolved:
            continue
        # Segunda pasada: coincidencia parcial.
        for cand in candidates:
            for real, norm in normalized.items():
                if cand in norm and real not in resolved.values():
                    resolved[field] = real
                    break
            if field in resolved:
                break
    return resolved


def _classify_tx(raw_type: str) -> str:
    t = _norm(raw_type)
    if any(k in t for k in TX_TYPE_DIV):
        return "dividend"
    if any(k in t for k in TX_TYPE_SELL):
        return "sell"
    if any(k in t for k in TX_TYPE_BUY):
        return "buy"
    return "buy"


def _guess_kind(isin: str | None, symbol: str | None, name: str | None) -> str:
    n = _norm(name or "")
    if "etf" in n:
        return "etf"
    if isin and not symbol:
        return "fund"
    if isin and len(isin) == 12 and not symbol:
        return "fund"
    if symbol:
        return "equity"
    return "fund" if isin else "other"


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------

def parse_file(filename: str, content: bytes) -> dict:
    """
    Devuelve:
      {
        "kind": "positions" | "transactions",
        "positions": [ {name, isin, symbol, kind, quantity, avg_price,
                        invested, market_value, currency} ],
        "transactions": [ {date, tx_type, name, isin, symbol, quantity,
                           price, amount} ],
        "warnings": [...]
      }
    """
    df = _read_dataframe(filename, content)
    df = df.dropna(how="all")
    cols = _build_header_index(df.columns)
    warnings: list[str] = []

    is_tx = "date" in cols and "tx_type" in cols

    def cell(row, field):
        col = cols.get(field)
        if not col:
            return None
        val = row.get(col)
        if pd.isna(val):
            return None
        return val

    positions: list[dict] = []
    transactions: list[dict] = []

    for _, row in df.iterrows():
        name = cell(row, "name")
        isin = cell(row, "isin")
        symbol = cell(row, "symbol")
        isin = str(isin).strip().upper() if isin else None
        symbol = str(symbol).strip().upper() if symbol else None
        name = str(name).strip() if name else None
        if not any([name, isin, symbol]):
            continue

        if is_tx:
            transactions.append({
                "date": _parse_date(cell(row, "date")),
                "tx_type": _classify_tx(cell(row, "tx_type") or ""),
                "name": name,
                "isin": isin,
                "symbol": symbol,
                "quantity": _parse_number(cell(row, "quantity")),
                "price": _parse_number(cell(row, "nav") or cell(row, "avg_price")),
                "amount": _parse_number(cell(row, "invested") or cell(row, "market_value")),
                "kind": _guess_kind(isin, symbol, name),
            })
        else:
            qty = _parse_number(cell(row, "quantity"))
            nav = _parse_number(cell(row, "nav"))
            invested = _parse_number(cell(row, "invested"))
            market_value = _parse_number(cell(row, "market_value"))
            avg_price = _parse_number(cell(row, "avg_price"))
            # Si falta el precio medio pero tenemos importe y participaciones, lo derivamos.
            if avg_price is None and invested and qty:
                avg_price = round(invested / qty, 6)
            # Si falta valor de mercado pero hay VL y participaciones, lo derivamos.
            if market_value is None and nav and qty:
                market_value = round(nav * qty, 2)
            positions.append({
                "name": name,
                "isin": isin,
                "symbol": symbol,
                "kind": _guess_kind(isin, symbol, name),
                "quantity": qty,
                "avg_price": avg_price,
                "nav": nav,
                "invested": invested,
                "market_value": market_value,
                "currency": (str(cell(row, "currency")).strip().upper() if cell(row, "currency") else "EUR"),
            })

    if not is_tx and not positions:
        warnings.append("No se detectaron posiciones. Revisa que el archivo tenga columnas de nombre/ISIN y participaciones.")
    if not cols:
        warnings.append("No se reconoció ninguna cabecera; ¿es realmente un export de MyInvestor?")

    return {
        "kind": "transactions" if is_tx else "positions",
        "detected_columns": cols,
        "positions": positions,
        "transactions": transactions,
        "warnings": warnings,
    }
