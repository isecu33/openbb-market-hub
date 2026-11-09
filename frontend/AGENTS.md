# AGENTS.md — openbb-market-hub / frontend

> **Mapa estructural para agentes.** Regenerable con `/project-map`.
> Comportamiento y reglas → `../CLAUDE.md` · Humanos/onboarding → `../README.md`
> · Diseño y decisiones → `../docs/SETUP.md` · Mapa raíz → `../AGENTS.md`

- **Tipo:** SPA frontend
- **Stack:** React (JavaScript, sin TypeScript) · Vite · Tailwind CSS · react-router-dom · componentes estilo shadcn
- **Estado:** MVP (sin tests automatizados)

---

## 1. Mapa de directorios

```
frontend/
├── index.html            [src]  entry HTML de Vite
├── vite.config.js         [cfg]  config de Vite
├── tailwind.config.js     [cfg]  config de Tailwind
├── postcss.config.js      [cfg]  config de PostCSS
├── package.json            [cfg]  dependencias y scripts npm (dev/build/preview)
├── public/                 [src]  favicon.svg y estáticos servidos tal cual
├── static/                 [ext]  vestigio del frontend-legacy (css/js sueltos) — no forma parte del build Vite, no editar
└── src/
    ├── main.jsx           [src]  entry point de React (monta <App/>)
    ├── App.jsx             [src]  layout raíz + definición de rutas (react-router-dom)
    ├── index.css           [src]  estilos globales / Tailwind
    ├── components/         [src]  componentes reutilizables
    │   ├── Layout.jsx        sidebar de navegación — añadir aquí la entrada al crear una página
    │   ├── shared.jsx
    │   └── ui/               primitivos estilo shadcn: badge, button, card, input, table, misc
    ├── hooks/              [src]  hooks personalizados
    │   └── useApi.js
    ├── lib/                [src]  utilidades y cliente API
    │   ├── api.js            cliente HTTP hacia el backend FastAPI
    │   ├── jobs.js            polling de trabajos en segundo plano (research)
    │   └── utils.js
    └── pages/              [src]  una página por ruta
        ├── Dashboard.jsx, Portfolio.jsx, Watchlist.jsx, News.jsx, Analysis.jsx,
        ├── Performance.jsx, Suggestions.jsx, Alerts.jsx, Research.jsx, Import.jsx
```

## 2. Arranque y comandos

- **Entrada / `main`:** `src/main.jsx` (monta `App.jsx` en `index.html`).
- **Instalar:** `npm install`
- **Arrancar (dev):** `npm run dev` (Vite, puerto 5173 con HMR; el backend debe correr aparte en :8000, ver `../start-dev.ps1`)
- **Build:** `npm run build` (el backend sirve el resultado desde `../start.ps1` en modo todo-en-uno)
- **Preview:** `npm run preview`
- **Tests:** no hay suite automatizada.
- **Config / secretos:** ninguno propio del frontend — el backend expone la API; claves API viven en `../.env`, nunca en el frontend.

## 3. Dónde va qué (tarea → ubicación)

| Para… | Toca… |
|---|---|
| nueva página/ruta | `src/pages/<X>.jsx` + registrar `<Route>` en `src/App.jsx` + entrada de navegación en `src/components/Layout.jsx` |
| componente reutilizable | `src/components/` |
| primitivo de UI (botón, tabla, card…) | `src/components/ui/` — reutilízalos antes de crear uno nuevo |
| llamada a la API del backend | `src/lib/api.js` (cliente) + hook en `src/hooks/useApi.js` |
| polling de trabajos en segundo plano (research lenta) | `src/lib/jobs.js` |
| utilidad genérica | `src/lib/utils.js` |
| estilos globales | `src/index.css` + `tailwind.config.js` |
| añadir dependencia | `package.json` |

## 4. Capas y reglas de import

- `pages/` compone `components/` y consume `lib/api.js` / `hooks/useApi.js` — nunca hace `fetch` directo, pasa siempre por `lib/`.
- `components/ui/` son primitivos sin lógica de negocio ni llamadas a red.
- El frontend solo habla con el backend vía la API REST montada en `backend/app.py` (ver `../backend/AGENTS.md`) — nunca importa código Python ni asume rutas de filesystem del servidor.
- `static/` (vestigio de `frontend-legacy/`) no se importa desde `src/` — no forma parte del grafo de módulos de Vite.

## 5. Convenciones locales de estructura

- **Naming:** componentes y páginas en `PascalCase.jsx`; hooks en `useCamelCase.js`; utilidades en `camelCase.js`.
- **Tests:** no existen todavía en este subsistema.
- **Rutas:** en español (`/cartera`, `/watchlist`, `/noticias`, `/analisis`, `/rendimiento`, `/sugerencias`, `/alertas`, `/research`, `/importar`), definidas en `src/App.jsx`.
- **NO tocar:** `static/` (vestigio de `frontend-legacy/`, no procesado por Vite).

## 6. Mapas anidados

Ninguno (subsistema de un solo nivel).

## 7. Mantenimiento

Regenerable con `/project-map`. **No** metas aquí comportamiento (→ `../CLAUDE.md`),
onboarding (→ `../README.md`) ni rationale de diseño (→ `../docs/SETUP.md`).
Si una ruta de este mapa deja de existir, el mapa está desactualizado: re-ejecuta `/project-map`.
