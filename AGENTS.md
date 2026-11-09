# AGENTS.md — openbb-market-hub

> **Mapa estructural para agentes.** Regenerable con `/project-map`.
> Comportamiento y reglas → `CLAUDE.md` · Humanos/onboarding → `README.md`
> · Diseño y decisiones → `docs/SETUP.md`

- **Tipo:** backend FastAPI + frontend React (SPA, monorepo de un repo)
- **Stack:** Python 3.11 / FastAPI / SQLModel / SQLite / APScheduler · React (JS, no TS) / Vite / Tailwind
- **Estado:** MVP (sin suite de tests automatizada todavía)

---

## 1. Mapa de directorios

```
openbb-market-hub/
├── backend/             [src]  API FastAPI, scheduler, persistencia → ver backend/AGENTS.md
├── frontend/             [src]  SPA React (Vite + Tailwind)          → ver frontend/AGENTS.md
├── frontend-legacy/      [ext]  HTML/CSS/JS estático plano, previo al frontend React — legado, no tocar salvo que se pida explícitamente
├── src/                  [src]  3 scripts CLI independientes (thesis_energy, politician_tracker, portfolio_tracker), también usados por backend/app.py como endpoints "legacy"
├── data/                  [gen]  market_hub.db (SQLite) — generado en runtime, gitignored, no editar a mano
├── docs/                  [doc]  SETUP.md
├── scripts/               [cfg]  bootstrap_run.ps1, setup_keys.py — utilidades de arranque/configuración
├── .devcontainer/         [cfg]  devcontainer.json + post-create.sh
├── .venv/                 [gen]  virtualenv Python — no versionar, no editar
├── requirements.txt       [cfg]  dependencias Python (raíz, no dentro de backend/)
├── start.ps1              [cfg]  arranque todo-en-uno: compila frontend y sirve todo desde backend en :8000
├── start-dev.ps1          [cfg]  arranque desarrollo: backend :8000 (reload) + frontend Vite :5173 (HMR)
├── .env / .env.example    [cfg]  claves API y config (FMP, FRED, GEMINI opcional, puertos, intervalos)
├── README.md              [doc]  pitch, instalación, uso
└── CLAUDE.md              [doc]  comportamiento y convenciones para agentes
```

## 2. Arranque y comandos

- **Entrada / `main`:** `backend/app.py` (FastAPI app; sirve también el build de React vía catch-all).
- **Instalar:** `pip install -r requirements.txt` (backend) · `cd frontend && npm install` (frontend)
- **Arrancar (dev):** `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1` (backend :8000 con reload + frontend Vite :5173 con HMR) — o manualmente `uvicorn backend.app:app --reload` + `cd frontend && npm run dev`
- **Arrancar (todo-en-uno):** `powershell -ExecutionPolicy Bypass -File .\start.ps1` (compila frontend con `npm run build` y lo sirve desde el backend en :8000)
- **Build:** `cd frontend && npm run build`
- **Tests:** no hay suite automatizada en este repo (sin `pytest` ni `test_*`); no asumir que existe un comando de test.
- **Config / secretos:** `backend/config.py` lee `.env` (plantilla en `.env.example`) — claves nunca en código ni commits.

## 3. Dónde va qué (tarea → ubicación)

| Para… | Toca… |
|---|---|
| nuevo endpoint backend | `backend/routers/<x>.py` + registrar `include_router` en `backend/app.py` |
| lógica de negocio backend | `backend/services/<x>.py` |
| modelo/tabla SQLModel | `backend/models.py` (+ `backend/db.py` si hace falta lógica de acceso) |
| config / variables de entorno | `backend/config.py` (lee de `.env`, plantilla `.env.example`) |
| tarea programada | `backend/scheduler.py` (APScheduler) |
| nueva vista/página web | `frontend/src/pages/<X>.jsx` + ruta en `frontend/src/App.jsx` + entrada de navegación en `frontend/src/components/Layout.jsx` |
| componente reutilizable | `frontend/src/components/` (primitivos de UI en `frontend/src/components/ui/`) |
| llamada a la API desde el frontend | `frontend/src/lib/api.js` (cliente) + `frontend/src/hooks/useApi.js` |
| script de research independiente (CLI) | `src/<script>.py` — recuerda que `backend/app.py` también los expone como endpoints legacy |
| añadir dependencia | `requirements.txt` (Python) o `frontend/package.json` (web) |

Detalle por subsistema → `backend/AGENTS.md` y `frontend/AGENTS.md`.

## 4. Capas y reglas de import

- `backend/` y `frontend/` solo se comunican vía la API REST que expone `backend/app.py` (routers + endpoints legacy) — el frontend nunca importa código Python, ni el backend código JS.
- `src/` son scripts CLI independientes; `backend/app.py` los importa directamente para exponerlos como endpoints legacy (`/thesis`, `/politician-trades`, `/portfolio`) — no dupliques esa lógica dentro de `backend/services/`.
- `frontend-legacy/` no forma parte del build activo (no tiene `package.json`, no lo procesa Vite) — es histórico; no lo referencies desde `frontend/` ni `backend/app.py`.
- Las consultas lentas de research (tesis, políticos, sugerencias) pasan por el patrón "attach" de `backend/services/jobs.py`; los routers que exponen research (`backend/routers/research.py`) dependen de `jobs.py`, no al revés.

## 5. Convenciones locales de estructura

- **Naming:** routers y servicios en `snake_case.py`; páginas y componentes React en `PascalCase.jsx`.
- **Tests:** no existen en este repo todavía.
- **Contenido data-driven / assets:** `data/market_hub.db` (SQLite runtime, gitignored) — no versionar ni editar a mano.
- **NO tocar:** `frontend-legacy/` (legado sin build), `.venv/` (generado), `data/*.db` (generado en runtime).

## 6. Mapas anidados

- `backend/AGENTS.md` — al trabajar en la API FastAPI, routers, servicios, modelos o scheduler.
- `frontend/AGENTS.md` — al trabajar en la SPA React (páginas, componentes, hooks, cliente API).

## 7. Mantenimiento

Regenerable con `/project-map`. **No** metas aquí comportamiento (→ `CLAUDE.md`),
onboarding (→ `README.md`) ni rationale de diseño (→ `docs/SETUP.md`).
Si una ruta de este mapa deja de existir, el mapa está desactualizado: re-ejecuta `/project-map`.
