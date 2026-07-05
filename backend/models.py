"""
backend/models.py
=================
Modelos de datos (SQLModel) de OpenBB Market Hub.

Diseño pensado para una cartera mixta tipo MyInvestor:
- `Asset` representa cualquier instrumento: acción, ETF o **fondo de inversión**
  (identificado por ISIN, no por ticker). Por eso `symbol` e `isin` son ambos
  opcionales: los fondos no siempre tienen ticker, las acciones no siempre
  exponen ISIN en las fuentes gratuitas.
- `Position` es la tenencia agregada de un asset (participaciones/acciones,
  precio medio, importe invertido y, opcionalmente, un valor de mercado
  importado del bróker cuando no podemos cotizarlo en vivo).
- `Transaction` guarda movimientos individuales (compra, venta, aportación,
  dividendo) para poder reconstruir histórico y P&L realizado.
- `Alert` / `AlertEvent` modelan el sistema de alertas.
- `PortfolioSnapshot` guarda el valor diario de la cartera para los gráficos.
"""

from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class AssetKind(str, Enum):
    equity = "equity"
    etf = "etf"
    fund = "fund"
    crypto = "crypto"
    other = "other"


class TxType(str, Enum):
    buy = "buy"
    sell = "sell"
    dividend = "dividend"
    fee = "fee"


class AlertKind(str, Enum):
    price_above = "price_above"
    price_below = "price_below"
    pct_change_day = "pct_change_day"   # variación intradía supera X %
    pct_from_cost = "pct_from_cost"     # P&L de la posición supera/baja X %
    news = "news"                       # nueva noticia relevante del activo
    politician = "politician"           # nuevo trade de político en ese ticker


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: AssetKind = AssetKind.equity
    symbol: Optional[str] = Field(default=None, index=True)
    isin: Optional[str] = Field(default=None, index=True)
    name: Optional[str] = None
    currency: str = "EUR"
    sector: Optional[str] = None
    region: Optional[str] = None
    # Última cotización conocida.
    last_price: Optional[float] = None
    last_price_at: Optional[datetime] = None
    price_source: Optional[str] = None        # "openbb", "import", "manual"
    in_watchlist: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Position(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id", index=True)
    quantity: float = 0.0
    avg_price: Optional[float] = None          # precio medio de coste por unidad
    invested_amount: Optional[float] = None    # importe invertido total
    # Valor de mercado importado del bróker (útil para fondos no cotizables en vivo).
    market_value_import: Optional[float] = None
    account: str = "MyInvestor"
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id", index=True)
    tx_type: TxType = TxType.buy
    tx_date: Optional[date] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    amount: Optional[float] = None
    fees: Optional[float] = None
    account: str = "MyInvestor"
    source: Optional[str] = None               # "import:archivo.xlsx", "manual"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id", index=True)
    symbol: Optional[str] = None               # para alertas sin asset en cartera
    kind: AlertKind = AlertKind.price_above
    threshold: Optional[float] = None
    note: Optional[str] = None
    active: bool = True
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alert_id: int = Field(foreign_key="alert.id", index=True)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    message: str = ""
    read: bool = False


class PortfolioSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_date: date = Field(index=True)
    total_value: float = 0.0
    total_invested: float = 0.0
    total_pnl: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NewsItem(SQLModel, table=True):
    """Noticia persistida por el refresco periódico, con sentimiento e
    importancia ya calculados. `dedupe_key` evita duplicados entre refrescos."""
    id: Optional[int] = Field(default=None, primary_key=True)
    dedupe_key: str = Field(index=True, unique=True)
    symbol: Optional[str] = Field(default=None, index=True)
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = Field(default=None, index=True)  # ISO "YYYY-MM-DD HH:MM:SS"
    summary: Optional[str] = None
    sentiment_label: str = "neutral"
    sentiment_score: float = 0.0
    importance: int = Field(default=0, index=True)     # 0-100
    category: Optional[str] = None                     # resultados, m&a, analistas...
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Suggestion(SQLModel, table=True):
    """Sugerencia generada (diaria/semanal): ranking de señales + briefing.
    El contenido va como JSON serializado para no rigidizar el esquema."""
    id: Optional[int] = Field(default=None, primary_key=True)
    period: str = Field(index=True)                    # "daily" | "weekly"
    generated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    payload: str = "{}"                                # JSON: señales, ranking, briefing
    engine: str = "rules"                              # "rules" | "claude"


class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: Optional[str] = None
