# OpenBB Market Hub

Plataforma personal de research e inversión, autoalojada, construida sobre
[OpenBB Platform](https://github.com/OpenBB-finance/OpenBB) con un **backend
FastAPI** y un **frontend React (Vite + Tailwind + shadcn-style)**.

No sustituye a tu bróker (MyInvestor) para precios en vivo ni ejecución: es una
capa de *research y seguimiento*. Como MyInvestor no tiene API pública, la
cartera se alimenta importando tus exportaciones (CSV/Excel).

## Qué puedes hacer

- **Dashboard**: valor total, invertido, P&L, distribución por tipo de activo y
  evolución del valor de la cartera.
- **Cartera**: posiciones consolidadas con P&L. Fondos valorados por su último
  valor liquidativo importado; acciones/ETF con precio en vivo de OpenBB. Alta y
  edición manual de posiciones.
- **Importar de MyInvestor**: sube tu export (CSV/Excel) y se detectan
  automáticamente fondos (por ISIN), acciones/ETF y movimientos, soportando el
  formato numérico europeo (`1.234,56`). Vista previa antes de confirmar.
- **Noticias + sentimiento**: feed **persistente** de tu cartera y del mercado
  global. El scheduler lo actualiza cada hora (`NEWS_REFRESH_MINUTES`); cada
  noticia se puntúa con sentimiento (ES/EN) e **importancia inversora** (0-100,
  por detección de eventos: resultados, M&A, regulación, analistas...), con
  filtro "solo importantes". Proveedor con fallback a yfinance (FMP restringió
  noticias e históricos de ETFs al plan de pago).
- **Sugerencias diarias/semanales**: ranking cuantitativo (tendencia SMA50/200,
  momentum 1m/3m, distancia a máximos de 52 semanas) sobre cartera + watchlist
  + ETFs de índices y sectores, más un briefing de mercado. Con
  `ANTHROPIC_API_KEY` en `.env`, el briefing lo redacta Claude usando las
  señales y las noticias importantes; sin clave, un motor de reglas. Se genera
  a diario (`SUGGESTION_HOUR`) y los lunes la semanal. **No es asesoramiento
  financiero** y la web lo indica siempre.
- **Análisis**: cotización, gráfico histórico (1M–5A) y noticias por símbolo.
- **Watchlist**: sigue activos sin tenerlos en cartera.
- **Alertas**: reglas por precio, variación diaria, P&L de la posición, noticias
  o trades de políticos. El backend las evalúa en segundo plano (scheduler).
- **Research**: tesis temática (de hipótesis macro a candidatas) y Government
  Trades de políticos de EE. UU. (con aviso de los 45 días de la STOCK Act).
  Las consultas lentas corren como **trabajos en segundo plano** en el servidor:
  puedes navegar por la app mientras se calculan y volver sin que se reinicien;
  los resultados se cachean unos minutos (configurable con `JOB_RESULT_TTL`).
- **Rendimiento**: retorno acumulado ajustado por aportaciones, volatilidad
  anualizada, ratio de Sharpe, máximo drawdown, comparación con un índice
  (S&P 500 / Nasdaq 100 / MSCI World), concentración de la cartera (peso top-5,
  posiciones efectivas), exposición por divisa y resumen de dividendos y
  comisiones por año.
- **Exportar**: cartera y transacciones a CSV (formato Excel es-ES) desde la web
  o vía `GET /api/portfolio/export/holdings.csv` y
  `GET /api/portfolio/export/transactions.csv`.

## Arranque rápido (Windows)

```powershell
# Opción A — todo en un servidor (compila la web y la sirve el backend en :8000)
powershell -ExecutionPolicy Bypass -File .\start.ps1

# Opción B — desarrollo (backend :8000 + frontend con recarga en :5173)
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

Antes copia `.env.example` a `.env` y rellena tus claves (FMP y FRED, gratuitas).

## Devcontainer (VS Code / Codespaces)

El repo incluye `.devcontainer/`: ábrelo en VS Code con la extensión *Dev
Containers* ("Reopen in Container") o en GitHub Codespaces. El contenedor trae
Python 3.12 + Node 20, instala dependencias automáticamente (`post-create.sh`)
y reenvía los puertos 8000 y 5173.

```bash
# Dentro del contenedor:
BUILD_FRONTEND=1 bash backend/run_backend.sh   # primera vez (compila la web)
bash backend/run_backend.sh                    # siguientes arranques
```

Notas: `.venv` y `frontend/node_modules` viven en volúmenes propios del
contenedor (los del host Windows no son compatibles con Linux). La base de
datos `data/market_hub.db` sí es la del workspace, compartida con el host.

## Arranque manual (cualquier sistema)

```bash
# 1) Backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                  # rellena tus claves

# 2) Frontend
cd frontend && npm install && npm run build && cd ..

# 3) Servir todo (web + API) en http://localhost:8000
uvicorn backend.app:app --reload
```

Para desarrollo del frontend con recarga en caliente: `cd frontend && npm run dev`
(usa el proxy a `:8000`, así que arranca también el backend).

## Arquitectura

```
openbb-market-hub/
├── backend/
│   ├── app.py              # FastAPI: routers + scheduler + sirve la web
│   ├── config.py           # rutas, .env, divisa base, intervalos
│   ├── db.py / models.py   # SQLite vía SQLModel (cartera, alertas, snapshots)
│   ├── scheduler.py        # APScheduler: refresco de precios y alertas
│   ├── routers/            # portfolio, market, news, alerts, research
│   └── services/           # openbb_client, myinvestor_import, portfolio,
│                           #   alerts_engine, sentiment
├── frontend/               # React + Vite + Tailwind (build -> frontend/dist)
│   └── src/{pages,components,lib,hooks}
├── src/                    # scripts originales (thesis, politicians, portfolio)
├── data/                   # SQLite y datos persistentes (gitignored)
└── .claude/skills/         # skills de Claude para este repo
```

Los datos viven en `data/market_hub.db` (SQLite). Las claves API, solo en `.env`.

## Tareas programadas / alertas

El backend incluye un scheduler que, mientras esté arrancado, refresca precios y
evalúa alertas periódicamente (configurable en `.env`). También puedes
dispararlo desde fuera por HTTP (p. ej. Programador de tareas de Windows):

```
POST http://localhost:8000/api/alerts/refresh-prices
POST http://localhost:8000/api/alerts/check
```

## Compatibilidad con OpenBB Workspace

Se mantienen los endpoints legacy (`/thesis`, `/politician-trades`, `/portfolio`)
para conectar el backend desde [pro.openbb.co](https://pro.openbb.co).

## Solución de problemas

- **La web muestra `{"message": "Frontend no compilado..."}`** — falta el build
  de React: `cd frontend && npm install && npm run build`. No hace falta
  reiniciar el backend: recarga la página.
- **`ModuleNotFoundError: No module named 'fastapi'` al arrancar** — estás
  usando un Python que no es el del proyecto (p. ej. otro venv activo en el
  PATH). Arranca siempre con el intérprete del proyecto:
  `.\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000`
  (los scripts `start.ps1` / `start-dev.ps1` ya lo hacen así).
- **`start.ps1` avisa de que el puerto 8000 está en uso** — ya hay una instancia
  corriendo; ábrela en http://localhost:8000 o mátala con
  `Stop-Process -Id <PID>` (el script te muestra el PID).
- **Las métricas de Rendimiento salen vacías** — se calculan sobre snapshots
  diarios de la cartera; deja el backend arrancado (el scheduler guarda un punto
  al día) o pulsa "Actualizar" a diario durante unos días.

## Notas

- **STOCK Act**: las operaciones de políticos llevan hasta 45 días de retraso de
  divulgación; son datos históricos/contextuales, nunca señales en tiempo real.
- Los nombres de endpoint de OpenBB cambian entre versiones; el código prueba
  varias rutas antes de rendirse (no asumas que un endpoint es estable).

MIT License.
