# AGENTS.md — openbb-market-hub / backend

> **Mapa estructural para agentes.** Regenerable con `/project-map`.
> Comportamiento y reglas → `../CLAUDE.md` · Humanos/onboarding → `../README.md`
> · Diseño y decisiones → `../docs/SETUP.md` · Mapa raíz → `../AGENTS.md`

- **Tipo:** API backend
- **Stack:** Python 3.11 · FastAPI · SQLModel (SQLite) · APScheduler · httpx
- **Estado:** MVP (sin tests automatizados)

---

## 1. Mapa de directorios

```
backend/
├── app.py           [src]  FastAPI app: crea la instancia, registra routers, monta el scheduler y sirve el build de React (catch-all SPA)
├── config.py         [src]  lee .env, rutas, divisa base, intervalos del scheduler
├── db.py             [src]  conexión/engine SQLite vía SQLModel
├── models.py         [src]  entidades SQLModel (tablas)
├── scheduler.py       [src]  APScheduler — refresco de precios + comprobación de alertas
├── routers/           [src]  endpoints FastAPI, uno por dominio → APIRouter expuesto como `router`
│   ├── portfolio.py
│   ├── market.py
│   ├── news.py
│   ├── alerts.py
│   └── research.py
├── services/           [src]  lógica de negocio, sin routing
│   ├── openbb_client.py    llamadas a OpenBB Platform (patrón _try_endpoints)
│   ├── myinvestor_import.py  parseo/fuzzy-matching del export de MyInvestor
│   ├── portfolio.py         cálculo de posiciones/cartera
│   ├── alerts_engine.py     evaluación de alertas
│   ├── sentiment.py         sentimiento de noticias
│   ├── metrics.py           rendimiento/riesgo de cartera
│   ├── news_store.py        persistencia del feed de noticias
│   ├── suggest.py           ranking + briefing de sugerencias (motor Gemini o reglas)
│   ├── news_digest.py       resumen diario de noticias (motor Gemini o reglas)
│   └── jobs.py              patrón "attach" para research lenta (get_or_submit)
└── run_backend.sh    [cfg]  arranque en devcontainer (BUILD_FRONTEND=1 para compilar la web la primera vez)
```

No hay `requirements.txt` dentro de `backend/` — vive en la raíz del repo (`../requirements.txt`).

## 2. Arranque y comandos

- **Entrada / `main`:** `backend/app.py` (variable `app`, ASGI).
- **Instalar:** `pip install -r ../requirements.txt`
- **Arrancar (dev):** `uvicorn backend.app:app --reload` (desde la raíz del repo, puerto 8000)
- **Devcontainer:** `bash backend/run_backend.sh`
- **Tests:** no hay suite automatizada; no asumir un comando de test.
- **Config / secretos:** `config.py` lee `../.env` (plantilla `../.env.example`).

## 3. Dónde va qué (tarea → ubicación)

| Para… | Toca… |
|---|---|
| nuevo endpoint | `backend/routers/<x>.py` + registrar el router en `backend/app.py` |
| lógica de negocio | `backend/services/<x>.py` |
| modelo/tabla | `backend/models.py` (+ acceso en `backend/db.py`) |
| config | `backend/config.py` (lee de `.env`) |
| tarea programada | `backend/scheduler.py` |
| consulta a OpenBB | `backend/services/openbb_client.py` — usa el patrón `_try_endpoints`, los nombres de endpoint cambian entre versiones |
| research lenta con caché/attach | `backend/services/jobs.py` (`get_or_submit`), consumido desde `backend/routers/research.py` |
| endpoint legacy (thesis/políticos/cartera CLI) | ya expuestos en `backend/app.py` llamando directo a `../src/*.py` — no los muevas a `routers/` sin revisar `../CLAUDE.md` |

## 4. Capas y reglas de import

- `routers/` depende de `services/`, nunca al revés.
- `services/` no importa de `routers/` ni conoce detalles HTTP (request/response de FastAPI).
- `app.py` es el único lugar que hace `include_router(...)` y que importa `../src/*.py` para los endpoints legacy.
- El frontend solo llega a este código vía la API REST — nunca hay imports cruzados con `frontend/`.

## 5. Convenciones locales de estructura

- **Naming:** módulos y funciones en `snake_case`; cada router expone un objeto `router` (APIRouter).
- **Tests:** no existen todavía en este subsistema.
- **Patrón dual Gemini/reglas:** `suggest.py` y `news_digest.py` usan Gemini si hay `GEMINI_API_KEY` en `.env`, si no caen a un motor de reglas — no asumas que Gemini está disponible.
- **Endpoints OpenBB inestables:** usa siempre `_try_endpoints` / try-except con rutas alternativas (ver `services/openbb_client.py`).
- **NO tocar:** el aviso de la STOCK Act (retraso de hasta 45 días) en `routers/research.py` y en `../src/politician_tracker.py`.

## 6. Mapas anidados

Ninguno (subsistema de un solo nivel).

## 7. Mantenimiento

Regenerable con `/project-map`. **No** metas aquí comportamiento (→ `../CLAUDE.md`),
onboarding (→ `../README.md`) ni rationale de diseño (→ `../docs/SETUP.md`).
Si una ruta de este mapa deja de existir, el mapa está desactualizado: re-ejecuta `/project-map`.
