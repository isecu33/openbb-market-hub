# CLAUDE.md

Contexto de proyecto para Claude Code/Desktop. Se carga automáticamente al
trabajar dentro de este repositorio.

## Qué es este proyecto

Plataforma personal de research e inversión, autoalojada, sobre OpenBB Platform.
**No** sustituye al bróker (MyInvestor) para precios en vivo ni ejecución — es
research y seguimiento: dashboard de cartera, noticias, sentimiento, alertas,
tesis temáticas y tracking de operaciones de políticos.

Arquitectura: **backend FastAPI + SQLite (SQLModel)** y **frontend React (Vite +
Tailwind, componentes estilo shadcn)**.

## Estructura

- `backend/app.py` — FastAPI: monta routers, scheduler y sirve el build de React.
- `backend/config.py` — `.env`, rutas, divisa base, intervalos del scheduler.
- `backend/db.py` + `backend/models.py` — SQLite vía SQLModel.
- `backend/scheduler.py` — APScheduler (refresco de precios + alertas).
- `backend/routers/` — `portfolio`, `market`, `news`, `alerts`, `research`.
- `backend/services/` — `openbb_client`, `myinvestor_import`, `portfolio`,
  `alerts_engine`, `sentiment`.
- `frontend/src/` — `pages/`, `components/` (incl. `ui/`), `lib/`, `hooks/`.
- `src/` — scripts originales independientes (siguen funcionando vía CLI).

## Los casos de uso de research (no los mezcles conceptualmente)

1. `src/thesis_energy.py` — de hipótesis macro a lista corta de candidatas.
2. `src/politician_tracker.py` — Government Trades (Senado + Cámara), proveedor
   FMP. **Siempre** recuerda el retraso de hasta 45 días de la STOCK Act.
3. `src/portfolio_tracker.py` — script CLI original de watchlist/cartera.

La web añade encima: dashboard, import de MyInvestor, alertas y análisis.

## Convenciones del repo

- Cada script de `src/` es ejecutable de forma independiente vía `argparse`.
- Los endpoints de OpenBB cambian de nombre entre versiones. Usa el patrón
  `_try_endpoints` / try-except con rutas alternativas (ver `openbb_client.py` y
  los scripts de `src/`). No asumas que un nombre de endpoint es estable.
- Las claves API viven solo en `.env` (nunca en código ni commits).
  `.env.example` documenta qué claves hacen falta y dónde sacarlas gratis.
- Persistencia en `data/market_hub.db` (SQLite, gitignored).
- El importador de MyInvestor (`myinvestor_import.py`) hace *fuzzy matching* de
  cabeceras y soporta formato numérico europeo; si MyInvestor cambia el export,
  ajusta `COLUMN_MAP` en vez de asumir un layout fijo.
- MIT License. Cambios que añadan dependencias -> `requirements.txt` (Python) o
  `frontend/package.json` (web).

## Skills disponibles en este repo

- **openbb-query** — escribir/depurar consultas a OpenBB; `list_endpoints.py`
  descubre endpoints reales sin adivinar.
- **thesis-builder** — flujo tesis temática → candidatas; señala cuándo los datos
  contradicen la tesis.
- **politician-watchlist** — Government Trades con el aviso de los 45 días.

## Cómo ayudar en este proyecto

- Nueva consulta a OpenBB y dudas del endpoint exacto: usa `list_endpoints.py`
  antes de adivinar.
- Si tocas `politician_tracker.py` o `routers/research.py`, no elimines el aviso
  de la STOCK Act.
- Nuevo endpoint backend: añade el router en `backend/routers/`, regístralo en
  `app.py` y, si procede, su servicio en `backend/services/`.
- Nueva vista web: página en `frontend/src/pages/`, ruta en `App.jsx` y entrada
  en el sidebar (`components/Layout.jsx`); reutiliza los primitivos de
  `components/ui/`.
