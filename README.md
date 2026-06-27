# OpenBB Market Hub

Plataforma personal de investigación de inversiones, autoalojada y construida sobre [OpenBB Platform](https://github.com/OpenBB-finance/OpenBB). Centraliza noticias, sentimiento y seguimiento de operaciones del Congreso de EE. UU. **sin sustituir a tu bróker** (pensado originalmente para complementar MyInvestor, que no tiene API pública) para precios en vivo ni ejecución de órdenes — es una capa de research, no de trading.

## Casos de uso

1. **`src/thesis_energy.py`** — Flujo de tesis temática: parte de una hipótesis macro (p. ej. "la demanda de energía sube por la IA y los datacenters") y filtra un universo de acciones hasta una lista corta de candidatas para analizar en profundidad.
2. **`src/politician_tracker.py`** — Tracker de operaciones de políticos (Senado + Cámara de Representantes de EE. UU.), usando el módulo *Government Trades* de OpenBB (proveedor FMP). **Importante**: la STOCK Act permite hasta 45 días de retraso en la divulgación, así que estas operaciones nunca son señales en tiempo real.
3. **`src/portfolio_tracker.py`** — Watchlist/cartera centralizada con noticias y sentimiento. Como MyInvestor no expone API pública, la cartera se carga a mano vía CSV o se mantiene como watchlist de tickers.

## Instalación rápida

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env              # y rellena tus claves
python scripts/setup_keys.py      # verifica que las claves funcionan
```

Detalles completos en [`docs/SETUP.md`](docs/SETUP.md).

## Backend para OpenBB Workspace

```bash
bash backend/run_backend.sh
```

Esto levanta un backend FastAPI local que puedes conectar desde [pro.openbb.co](https://pro.openbb.co) (Workspace → Apps → Connect backend) para visualizar los datos en una interfaz tipo terminal financiero.

## Agent Skills de Claude

En `.claude/skills/` hay tres skills para Claude Code/Desktop dentro de este repo: `openbb-query`, `thesis-builder` y `politician-watchlist`. Se cargan solas al abrir el proyecto y se activan cuando pides algo relacionado. Ver `CLAUDE.md` para el contexto general que usan.

> **Nota de seguridad**: trata las skills como software — son legibles y solo usan OpenBB local + tu `.env`, pero revísalas antes de confiar en ellas si las modificas o añades nuevas.

## Estructura

```
openbb-market-hub/
├── src/
│   ├── thesis_energy.py
│   ├── politician_tracker.py
│   └── portfolio_tracker.py
├── backend/
│   └── run_backend.sh
├── scripts/
│   └── setup_keys.py
├── docs/
│   └── SETUP.md
├── .claude/
│   ├── skills/
│   │   ├── openbb-query/
│   │   ├── thesis-builder/
│   │   └── politician-watchlist/
│   └── CLAUDE.md (referenciado, ver raíz)
├── .env.example
├── requirements.txt
├── .gitignore
├── LICENSE
└── CLAUDE.md
```

## Licencia

MIT — ver [`LICENSE`](LICENSE).
